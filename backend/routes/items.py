"""Items and item-related API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from matcher import api, database, model, wikidata, wikidata_api
from matcher import context

router = APIRouter()


@router.get("/api/1/count")
async def count_items(request: Request) -> JSONResponse:
    """Count Wikidata items in the given bounds."""
    bbox_str = request.query_params.get("bbox", "")
    types_param = request.query_params.get("types", "")
    item_type = request.query_params.get("type", "")
    try:
        bbox = [float(x) for x in bbox_str.split(",")] if bbox_str else None
        item_types = types_param.split(",") if types_param else []
        count = api.wikidata_items_count(bbox, item_types, item_type)
        return JSONResponse({"count": count})
    except ValueError:
        return JSONResponse({"count": 0})


@router.get("/api/1/items")
async def get_items(request: Request) -> JSONResponse:
    """Get Wikidata items in bounds."""
    bbox_str = request.query_params.get("bbox", "")
    types_param = request.query_params.get("types", "")
    item_type = request.query_params.get("type", "")
    try:
        bbox = [float(x) for x in bbox_str.split(",")] if bbox_str else None
        item_types = types_param.split(",") if types_param else []
        items = api.wikidata_items(bbox, item_types, item_type)
        return JSONResponse({"items": items})
    except ValueError:
        return JSONResponse({"items": []})


@router.get("/api/1/item/Q{item_id}")
async def get_item_detail(item_id: int, request: Request) -> JSONResponse:
    """Get detail for a Wikidata item."""
    item = model.Item.query.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    detail = api.item_detail(item)
    return JSONResponse(detail)


@router.get("/api/1/item/Q{item_id}/tags")
async def get_item_tags(item_id: int) -> JSONResponse:
    """Get OSM tags/keys for a Wikidata item."""
    item = model.Item.query.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    tags = api.get_item_tags(item)
    return JSONResponse(tags)


@router.get("/api/1/item/Q{item_id}/candidates")
async def get_item_candidates(item_id: int, request: Request) -> JSONResponse:
    """Find nearby OSM candidates for a Wikidata item."""
    radius = request.query_params.get("radius", "1000")
    context.set("street_number_first", True)
    candidates = api.find_osm_candidates(item_id, int(radius))
    return JSONResponse(candidates)


@router.get("/api/1/missing")
async def get_missing_items(request: Request) -> JSONResponse:
    """Fetch missing Wikidata item details."""
    qids_str = request.query_params.get("qids", "")
    lat = request.query_params.get("lat")
    lon = request.query_params.get("lon")
    qids = [q.strip() for q in qids_str.split(",") if q.strip()] if qids_str else []
    if not qids or not lat or not lon:
        return JSONResponse({"items": [], "isa_count": []})
    result = api.missing_wikidata_items(qids, float(lat), float(lon))
    return JSONResponse(result)


@router.get("/api/1/location")
async def get_location(request: Request) -> JSONResponse:
    """Get user's geolocation."""
    remote_ip = request.query_params.get("ip", request.client.host if request.client else "")
    from backend.geo import get_location
    loc = get_location(remote_ip)
    if loc:
        return JSONResponse(loc)
    return JSONResponse({})


@router.get("/api/1/isa")
async def get_isa(request: Request) -> JSONResponse:
    """Get Wikidata IsA counts in bounds."""
    bbox_str = request.query_params.get("bbox", "")
    try:
        bbox = [float(x) for x in bbox_str.split(",")] if bbox_str else None
        result = api.wikidata_isa_counts(bbox)
        return JSONResponse(result)
    except ValueError:
        return JSONResponse({"isa_count": []})


@router.get("/api/1/isa_search")
async def isa_search(request: Request) -> JSONResponse:
    """Search for IsA item types."""
    q = request.query_params.get("q", "")
    isa_list = api.isa_incremental_search(q)
    return JSONResponse({"isa_list": isa_list})


@router.get("/item/Q{item_id}")
async def item_redirect(item_id: int) -> JSONResponse:
    """Lookup item and return its location."""
    item = model.Item.query.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    coords = api.item_location(item)
    return JSONResponse(coords)


@router.get("/refresh/Q{item_id}")
async def refresh_item(item_id: int) -> JSONResponse:
    """Refresh local Wikidata item mirror."""
    entity = wikidata_api.get_entity(f"Q{item_id}")
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    claims = entity.get("claims", {})
    coords = wikidata.get_entity_coords(claims)
    item = model.Item.query.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not in database")

    if coords:
        item.locations = model.location_objects(coords)
    database.session.commit()
    return JSONResponse({"status": "done"})
