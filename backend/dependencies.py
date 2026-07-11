"""FastAPI dependencies."""

from __future__ import annotations

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from matcher import database as db
from matcher.config import config
from matcher.model import User


def get_db() -> Session:
    """Get database session."""
    return db.session


def get_current_user(request: Request) -> User | None:
    """Get current user from session, or None."""
    user_id = request.session.get("user_id")
    if user_id is None:
        return None
    user = User.query.get(user_id)
    return user


async def require_user(request: Request) -> User:
    """Require an authenticated user."""
    user = get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def get_client_key() -> str:
    """Get OSM client key from config."""
    return config["CLIENT_KEY"]
