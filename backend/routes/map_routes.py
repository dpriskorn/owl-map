"""Map-related routes."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from matcher import api, model

router = APIRouter()


@router.get("/api/1/osm")
async def get_osm_objects(request: Request) -> JSONResponse:
    """Get OSM objects with wikidata tag in bounds."""
    bounds_param = request.query_params.get("bounds", "")
    isa_param = request.query_params.get("isa", "")
    if not bounds_param:
        return JSONResponse({"objects": []})
    bounds = [float(x) for x in bounds_param.split(",")]
    isa_filter = {qid.strip() for qid in isa_param.upper().split(",")} if isa_param else None
    objects = api.get_osm_with_wikidata_tag(bounds, isa_filter=isa_filter)
    return JSONResponse({"success": True, "objects": objects})


@router.get("/api/1/place/{osm_type}/{osm_id}")
async def get_place_items(osm_type: str, osm_id: int) -> JSONResponse:
    """Get Wikidata items for an OSM place."""
    result = api.get_place_items(osm_type, osm_id)
    return JSONResponse({"success": True, **result})


@router.get("/api/1/polygon/{osm_type}/{osm_id}")
async def get_polygon(osm_type: str, osm_id: int) -> JSONResponse:
    """Get GeoJSON polygon for an OSM object."""
    obj = model.Polygon.get_osm(osm_type, osm_id)
    return JSONResponse({
        "successful": True,
        "osm_type": osm_type,
        "osm_id": osm_id,
        "geojson": obj.geojson(),
    })
