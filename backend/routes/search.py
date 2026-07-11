"""Search routes."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from matcher import nominatim

router = APIRouter()


@router.get("/api/1/search")
async def search(request: Request) -> JSONResponse:
    """Search via Nominatim."""
    q = request.query_params.get("q")
    if not q:
        return JSONResponse({"success": False, "error": "Missing query"})
    try:
        hits = nominatim.lookup(q)
    except nominatim.SearchError as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=503)
    for hit in hits:
        hit["name"] = nominatim.get_hit_name(hit)
        hit["label"] = nominatim.get_hit_label(hit)
        hit["address"] = list(hit["address"].items())
    return JSONResponse(hits)
