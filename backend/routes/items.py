"""Simplified items API routes using Qlever for Wikidata."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from matcher import api

router = APIRouter()


@router.get("/api/1/count")
async def count_items(request: Request) -> JSONResponse:
    """Count Wikidata items in the given bounds via Qlever."""
    bbox_str = request.query_params.get("bbox", "")
    try:
        bbox = [float(x) for x in bbox_str.split(",")] if bbox_str else None
        if not bbox or len(bbox) != 4:
            return JSONResponse({"count": 0})
        count = api.wikidata_items_count(bbox)
        return JSONResponse({"count": count})
    except ValueError:
        return JSONResponse({"count": 0})


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
