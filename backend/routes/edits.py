"""Edit session routes."""

from __future__ import annotations

import json
from time import sleep

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from backend.dependencies import require_user
from matcher import database, edit, mail
from matcher.config import config
from matcher.model import EditSession, User

router = APIRouter()


@router.post("/api/1/edit")
async def create_edit(request: Request, user: User = Depends(require_user)) -> JSONResponse:
    """Create a new edit session."""
    data = await request.json()
    comment = data.get("comment", config.get("DEFAULT_COMMENT", "+wikidata"))
    edit_list = data.get("edit_list", [])

    session = EditSession(
        user_id=user.id,
        edit_list=edit_list,
        comment=comment,
    )
    database.session.add(session)
    database.session.commit()

    return JSONResponse({"session_id": session.id})


@router.post("/api/1/edit/{session_id}")
async def update_edit(session_id: int, request: Request, user: User = Depends(require_user)) -> JSONResponse:
    """Update an edit session."""
    data = await request.json()
    edit_list = data.get("edit_list", [])

    session = EditSession.query.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.edit_list = edit_list
    database.session.commit()

    return JSONResponse({"session_id": session.id})


@router.get("/api/1/save/{session_id}")
async def save_edit(session_id: int, user: User = Depends(require_user)):
    """Save changeset (SSE stream)."""
    return StreamingResponse(
        save_generator(session_id, user),
        media_type="text/event-stream",
    )


def save_generator(session_id: int, user: User):
    """Generator for SSE streaming of edit saves."""
    client_key = config["CLIENT_KEY"]

    token = {
        "oauth_token": user.osm_oauth_token,
        "oauth_token_secret": user.osm_oauth_token_secret,
    }

    def send(event: str, **kwargs):
        data = json.dumps(kwargs) if kwargs else ""
        yield f"event: {event}\ndata: {data}\n\n"

    session = EditSession.query.get(session_id)
    if not session:
        yield from send("error", error="Session not found")
        return

    yield from send("progress", num=0, total=len(session.edit_list))

    changeset = edit.new_changeset(session.comment)
    try:
        r = edit.create_changeset(client_key, token, changeset)
    except Exception as e:
        mail.send_mail("error creating changeset", str(e))
        yield from send("error", error=str(e))
        return

    changeset_id = int(r.text.strip())

    for num, e in enumerate(session.edit_list):
        yield from send("progress", edit=e, num=num)
        sleep(1)
        result = edit.save_element(client_key, token, e["osm_type"], e["osm_id"], e["data"], username=user.username)
        if result is None:
            yield from send("error", edit=e, error="Failed to save")
            continue
        yield from send("saved", edit=e, num=num)
        sleep(1)

    edit.close_changeset(client_key, token, changeset_id)
    edit.record_changeset(id=changeset_id, comment=session.comment)

    yield from send("closing")
    sleep(1)
    yield from send("done")
