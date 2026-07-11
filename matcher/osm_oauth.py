"""OSM Authentication."""

import typing
from datetime import datetime
from urllib.parse import urlencode

import lxml.etree
import requests
from requests_oauthlib import OAuth1Session


osm_api_base = "https://api.openstreetmap.org/api/0.6"


def get_oauth_session(client_key: str, token: dict) -> OAuth1Session:
    """Create an OAuth1Session from stored token dict."""
    return OAuth1Session(
        client_key,
        resource_owner_key=token.get("oauth_token"),
        resource_owner_secret=token.get("oauth_token_secret"),
    )


def api_put_request(
    client_key: str, token: dict, path: str, **kwargs: typing.Any
) -> requests.Response:
    """Send OSM API PUT request."""
    oauth = get_oauth_session(client_key, token)
    from matcher import user_agent_headers

    return oauth.request(
        "PUT", osm_api_base + path, headers=user_agent_headers(), **kwargs
    )


def api_request(
    client_key: str, token: dict, path: str, **params: typing.Any
) -> requests.Response:
    """Send OSM API request."""
    url = osm_api_base + path
    if params:
        url += "?" + urlencode(params)

    oauth = get_oauth_session(client_key, token)
    return oauth.get(url, timeout=4)


def parse_iso_date(value: str) -> datetime:
    """Parse ISO date."""
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")


def parse_userinfo_call(xml: bytes) -> dict[str, typing.Any]:
    """Parse userinfo call."""
    root = lxml.etree.fromstring(xml)
    user = root[0]
    img = user.find(".//img")

    account_created_date = user.get("account_created")
    assert account_created_date
    account_created = parse_iso_date(account_created_date)

    assert user.tag == "user"

    id_str = user.get("id")
    assert id_str and isinstance(id_str, str)

    return {
        "account_created": account_created,
        "id": int(id_str),
        "username": user.get("display_name"),
        "description": user.findtext(".//description"),
        "img": (img.get("href") if img is not None else None),
    }
