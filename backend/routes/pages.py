"""Page routes - SPA catch-all and server-rendered pages."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/")
async def index() -> HTMLResponse:
    """Serve SPA index page."""
    index_path = Path("static/index.html")
    if index_path.exists():
        return HTMLResponse(index_path.read_text())
    return HTMLResponse("<h1>OWL Map</h1><p>Frontend not built yet. Run 'cd frontend && npx vite build'</p>")


@router.get("/map")
async def map_redirect(request: Request) -> HTMLResponse:
    """Map page - serve SPA."""
    index_path = Path("static/index.html")
    if index_path.exists():
        return HTMLResponse(index_path.read_text())
    return HTMLResponse("<h1>OWL Map</h1><p>Frontend not built yet.</p>")
