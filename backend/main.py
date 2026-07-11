"""FastAPI application."""

from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles

from backend import geo
from backend.exceptions import AppException
from backend.routes import auth, edits, items, map_routes, pages, search
from matcher import database
from matcher.config import config

config.from_dict({
    "SECRET_KEY": os.getenv("SECRET_KEY", "dev-secret-key"),
    "DB_URL": os.getenv("DATABASE_URL", "postgresql:///osm"),
    "GEOLITE2": os.getenv("GEOLITE2"),
})

app = FastAPI(title="OWL Map")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=config.get("SECRET_KEY", "dev-secret-key"))

app.include_router(auth.router)
app.include_router(items.router)
app.include_router(map_routes.router)
app.include_router(search.router)
app.include_router(edits.router)
app.include_router(pages.router)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse({"status": "ok"})


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom app exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.message},
    )


@app.on_event("startup")
async def startup() -> None:
    """Initialize app on startup."""
    database.init_db(config.get("DB_URL", "postgresql:///osm"))

    geolite2_path = config.get("GEOLITE2")
    if geolite2_path:
        geo.init_reader(geolite2_path)


@app.on_event("shutdown")
async def shutdown() -> None:
    """Clean up on shutdown."""
    geo.close_reader()
