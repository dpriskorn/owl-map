"""OSM OAuth authentication routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from requests_oauthlib import OAuth1Session

from backend.dependencies import get_client_key
from matcher import database, osm_oauth
from matcher.config import config
from matcher.model import User

router = APIRouter()

osm_api_base = "https://api.openstreetmap.org/api/0.6"


@router.get("/login")
async def login(request: Request) -> RedirectResponse:
    """Redirect to OSM login."""
    next_url = request.query_params.get("next") or "/"
    return RedirectResponse(url=f"/oauth/start?next={next_url}")


@router.get("/logout")
async def logout(request: Request) -> RedirectResponse:
    """Logout."""
    next_url = request.query_params.get("next") or "/"
    request.session.clear()
    return RedirectResponse(url=next_url)


@router.get("/oauth/start")
async def start_oauth(request: Request, client_key: str = Depends(get_client_key)) -> RedirectResponse:
    """Start OAuth flow."""
    next_page = request.query_params.get("next")
    if next_page:
        request.session["next"] = next_page

    client_secret = config["CLIENT_SECRET"]

    request_token_url = "https://www.openstreetmap.org/oauth/request_token"
    callback = str(request.url_for("oauth_callback"))

    oauth = OAuth1Session(
        client_key, client_secret=client_secret, callback_uri=callback
    )
    fetch_response = oauth.fetch_request_token(request_token_url)

    request.session["owner_key"] = fetch_response.get("oauth_token")
    request.session["owner_secret"] = fetch_response.get("oauth_token_secret")

    base_authorization_url = "https://www.openstreetmap.org/oauth/authorize"
    authorization_url = oauth.authorization_url(
        base_authorization_url, oauth_consumer_key=client_key
    )
    return RedirectResponse(url=authorization_url)


@router.get("/oauth/callback")
async def oauth_callback(request: Request, client_key: str = Depends(get_client_key)) -> RedirectResponse:
    """Handle OAuth callback."""
    client_secret = config["CLIENT_SECRET"]

    oauth = OAuth1Session(
        client_key,
        client_secret=client_secret,
        resource_owner_key=request.session.get("owner_key"),
        resource_owner_secret=request.session.get("owner_secret"),
    )

    oauth_response = oauth.parse_authorization_response(str(request.url))
    verifier = oauth_response.get("oauth_verifier")
    access_token_url = "https://www.openstreetmap.org/oauth/access_token"
    oauth = OAuth1Session(
        client_key,
        client_secret=client_secret,
        resource_owner_key=request.session.get("owner_key"),
        resource_owner_secret=request.session.get("owner_secret"),
        verifier=verifier,
    )

    oauth_tokens = oauth.fetch_access_token(access_token_url)
    request.session["owner_key"] = oauth_tokens.get("oauth_token")
    request.session["owner_secret"] = oauth_tokens.get("oauth_token_secret")

    r = oauth.get(osm_api_base + "/user/details")
    info = osm_oauth.parse_userinfo_call(r.content)

    user = User.query.filter_by(osm_id=info["id"]).one_or_none()

    if user:
        user.osm_oauth_token = oauth_tokens.get("oauth_token")
        user.osm_oauth_token_secret = oauth_tokens.get("oauth_token_secret")
    else:
        user = User(
            username=info["username"],
            description=info["description"],
            img=info["img"],
            osm_id=info["id"],
            osm_account_created=info["account_created"],
            mock_upload=False,
        )
        database.session.add(user)
    database.session.commit()

    request.session["user_id"] = user.id

    next_page = request.session.get("next") or "/"
    return RedirectResponse(url=next_page)
