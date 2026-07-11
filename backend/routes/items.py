"""Simplified items API routes using Qlever for Wikidata."""

from __future__ import annotations

import requests

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from wikibaseintegrator.wbi_helpers import search_entities, config

from matcher import api

router = APIRouter()

USER_AGENT = "owl-map/1.0 (https://github.com/dpriskorn/owl-map)"
config["USER_AGENT"] = USER_AGENT

WIKIDATA_REST_URL = "https://www.wikidata.org/w/rest.php/wikibase/v1"


def _fetch_wikidata_labels(qids: list[str], language: str) -> dict[str, dict]:
    """Fetch labels and descriptions from Wikidata REST API in specified language."""
    results = {}
    for qid in qids:
        try:
            url = f"{WIKIDATA_REST_URL}/entities/items/{qid}"
            response = requests.get(
                url,
                headers={"User-Agent": USER_AGENT},
                params={"languages": language},
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                results[qid] = {
                    "label": data.get("label", qid),
                    "description": data.get("description"),
                }
            else:
                results[qid] = {"label": qid, "description": None}
        except Exception:
            results[qid] = {"label": qid, "description": None}
    return results


@router.get("/api/1/wikidata_search")
async def wikidata_search(request: Request) -> JSONResponse:
    """Search Wikidata by label/alias using wikibaseintegrator."""
    q = request.query_params.get("q", "")
    language = request.query_params.get("language", "en")
    if not q or len(q) < 3:
        return JSONResponse({"results": []})
    try:
        results = search_entities(
            search_string=q,
            language=language,
            max_results=50,
            dict_result=True,
        )
        qids = [r["id"] for r in results[:10]]
        wikidata_data = _fetch_wikidata_labels(qids, language)

        normalized = []
        for r in results[:10]:
            qid = r["id"]
            data = wikidata_data.get(qid, {"label": qid, "description": None})
            normalized.append({
                "id": qid,
                "label": data["label"],
                "description": data["description"],
            })
        return JSONResponse({"results": normalized, "language": language})
    except Exception as e:
        return JSONResponse({"results": [], "error": str(e)})


@router.get("/api/1/items")
async def get_items(request: Request) -> JSONResponse:
    """Get Wikidata items in bounds via Qlever."""
    bbox_str = request.query_params.get("bbox", "")
    try:
        bbox = [float(x) for x in bbox_str.split(",")] if bbox_str else None
        if not bbox or len(bbox) != 4:
            return JSONResponse({"items": {}})
        result = api.wikidata_items(bbox)
        return JSONResponse(result)
    except ValueError:
        return JSONResponse({"items": {}})


@router.get("/api/1/isa")
async def get_isa(request: Request) -> JSONResponse:
    """Get Wikidata IsA counts in bounds via Qlever."""
    bbox_str = request.query_params.get("bbox", "")
    try:
        bbox = [float(x) for x in bbox_str.split(",")] if bbox_str else None
        if not bbox or len(bbox) != 4:
            return JSONResponse({"isa_count": []})
        result = api.wikidata_isa_counts(bbox)
        return JSONResponse({"isa_count": result})
    except ValueError:
        return JSONResponse({"isa_count": []})


@router.get("/api/1/osm")
async def get_osm_objects(request: Request) -> JSONResponse:
    """Get OSM objects in bounds."""
    bbox_str = request.query_params.get("bounds", "")
    try:
        bbox = [float(x) for x in bbox_str.split(",")] if bbox_str else None
        if not bbox or len(bbox) != 4:
            return JSONResponse({"osm": []})
        osm_objects = api.get_osm_in_bbox(bbox)
        return JSONResponse({"osm": osm_objects})
    except ValueError:
        return JSONResponse({"osm": []})


@router.get("/api/1/search")
async def search_osm(request: Request) -> JSONResponse:
    """Search OSM objects by name."""
    q = request.query_params.get("q", "")
    bbox_str = request.query_params.get("bbox", "")
    if not q:
        return JSONResponse({"results": []})
    try:
        bbox = [float(x) for x in bbox_str.split(",")] if bbox_str else None
        results = api.search_osm(q, bbox)
        return JSONResponse({"results": results})
    except ValueError:
        return JSONResponse({"results": []})


@router.get("/api/1/location")
async def get_location(request: Request) -> JSONResponse:
    """Get user's geolocation."""
    remote_ip = request.query_params.get("ip", request.client.host if request.client else "")
    from backend.geo import get_location
    loc = get_location(remote_ip)
    if loc:
        return JSONResponse(loc)
    return JSONResponse({})
