"""Simplified items API routes using Qlever for Wikidata."""

from __future__ import annotations

import math

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from wikibaseintegrator.wbi_helpers import search_entities, config

from matcher import api
from matcher.match import get_osm_tag_from_p1282, match_wikidata_to_osm
from matcher.osm_qlever import osm_qlever
from matcher.wikidata_api import get_items_near_coordinates

router = APIRouter()

USER_AGENT = "owl-map/1.0 (https://github.com/dpriskorn/owl-map)"
config["USER_AGENT"] = USER_AGENT


def bbox_to_center_radius(bbox: list[float]) -> tuple[float, float, float]:
    """Convert bbox [lat_min, lon_min, lat_max, lon_max] to center point and radius in km.

    Returns:
        Tuple of (center_lat, center_lon, radius_km)
    """
    lat_min, lon_min, lat_max, lon_max = bbox
    center_lat = (lat_min + lat_max) / 2
    center_lon = (lon_min + lon_max) / 2

    lat_range_km = (lat_max - lat_min) * 111.0
    lon_range_km = (lon_max - lon_min) * 111.0 * math.cos(math.radians(center_lat))
    radius_km = math.sqrt(lat_range_km ** 2 + lon_range_km ** 2) / 2 + 1

    return center_lat, center_lon, max(radius_km, 5.0)


def filter_items_in_bbox(items: dict, bbox: list[float]) -> dict:
    """Filter items to only those within the bbox.

    Args:
        items: Dict of items with markers
        bbox: [lat_min, lon_min, lat_max, lon_max]

    Returns:
        Filtered items dict
    """
    lat_min, lon_min, lat_max, lon_max = bbox
    filtered = {}
    for qid, item in items.items():
        valid_markers = [
            m for m in item.get("markers", [])
            if lat_min <= m["lat"] <= lat_max and lon_min <= m["lon"] <= lon_max
        ]
        if valid_markers:
            filtered[qid] = {**item, "markers": valid_markers}
    return filtered


@router.get("/api/1/wikidata_search")
async def wikidata_search(request: Request) -> JSONResponse:
    """Search Wikidata by label/alias using wikibaseintegrator. Returns QIDs only."""
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
        qids = [{"id": r["id"]} for r in results[:10]]
        return JSONResponse({"results": qids, "language": language})
    except Exception as e:
        return JSONResponse({"results": [], "error": str(e)})


@router.get("/api/1/items")
async def get_items(request: Request) -> JSONResponse:
    """Get Wikidata items + OSM objects in bounds via Wikimedia API + Qlever.

    Uses Wikimedia API's nearcoord to find nearby QIDs, then Qlever
    to fetch coordinates and optionally filter by ISA type.
    When ISA type is set, also queries OSM Qlever for matching objects.
    Returns three categories: matched pairs, wikidata-only, and osm-only.
    """
    bbox_str = request.query_params.get("bbox", "")
    isa_str = request.query_params.get("isa", "")
    print(f"get_items called: bbox={bbox_str}, isa={isa_str}")

    warnings = []

    try:
        bbox = [float(x) for x in bbox_str.split(",")] if bbox_str else None
        if not bbox or len(bbox) != 4:
            print("get_items: invalid bbox, returning empty")
            return JSONResponse({"items": {}, "osm_objects": {}, "warnings": []})

        lat_min, lon_min, lat_max, lon_max = bbox
        center_lat, center_lon, radius_km = bbox_to_center_radius(bbox)
        isa_type = isa_str if isa_str else None

        print(f"get_items: searching nearcoord {radius_km}km around ({center_lat}, {center_lon})")
        qids = get_items_near_coordinates(center_lat, center_lon, int(radius_km))
        print(f"get_items: got {len(qids)} QIDs from Wikimedia API")

        if not qids:
            return JSONResponse({"items": {}, "osm_objects": {}, "warnings": []})

        if isa_type:
            print(f"get_items: fetching with ISA filter: {isa_type}")
            wikidata_result = api.wikidata_items_by_qids(qids, isa_type)
        else:
            print("get_items: fetching without ISA filter")
            wikidata_result = api.wikidata_items_by_qids(qids)

        items = filter_items_in_bbox(wikidata_result.get("items", {}), bbox)
        print(f"get_items: {len(items)} Wikidata items after bbox filter")

        osm_objects = {}
        osm_tag_info = None

        if isa_type:
            p1282_value = api.get_item_p1282(isa_type)
            if p1282_value:
                osm_tag_info = get_osm_tag_from_p1282(p1282_value)
                if osm_tag_info:
                    tag_key, tag_value = osm_tag_info
                    print(f"get_items: querying OSM for {tag_key}={tag_value}")
                    osm_objects = osm_qlever.get_objects_by_tag(tag_key, tag_value, bbox)
                    print(f"get_items: got {len(osm_objects)} OSM objects")
                else:
                    print(f"get_items: could not parse P1282 value: {p1282_value}")
            else:
                warning = {
                    "type": "no_p1282",
                    "message": f"ISA type {isa_type} has no P1282 OSM tag",
                    "url": f"https://www.wikidata.org/wiki/{isa_type}",
                }
                warnings.append(warning)
                print(f"get_items: warning - {warning}")

        match_result = match_wikidata_to_osm(items, osm_objects, isa_type)
        print(f"get_items: matched={len(match_result['matched'])}, wikidata_only={len(match_result['wikidata_only'])}, osm_only={len(match_result['osm_only'])}")

        enriched_items = {}
        for qid, item in items.items():
            enriched_items[qid] = {
                **item,
                "match_status": "wikidata_only",
                "osm_id": None,
            }

        for match in match_result["matched"]:
            qid = match["wikidata_qid"]
            if qid in enriched_items:
                enriched_items[qid]["match_status"] = "matched"
                enriched_items[qid]["osm_id"] = match["osm_id"]

        return JSONResponse({
            "items": enriched_items,
            "osm_objects": osm_objects,
            "warnings": warnings,
        })
    except Exception as e:
        print(f"get_items: error {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse({"items": {}, "osm_objects": {}, "warnings": []})


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


@router.get("/api/1/osm-nearby")
async def get_osm_nearby(request: Request) -> JSONResponse:
    """Get OSM objects near a Wikidata item with the same P1282 tag.

    Query params:
        - qid: Wikidata QID of the item
        - lat: Latitude of the item
        - lon: Longitude of the item
        - limit: Maximum number of results (default 10)
    """
    qid = request.query_params.get("qid", "")
    lat_str = request.query_params.get("lat", "")
    lon_str = request.query_params.get("lon", "")
    limit_str = request.query_params.get("limit", "10")

    try:
        lat = float(lat_str)
        lon = float(lon_str)
        limit = int(limit_str)
    except (ValueError, TypeError):
        return JSONResponse({"osm_objects": []})

    print(f"get_osm_nearby: qid={qid}, lat={lat}, lon={lon}")

    p1282_value = api.get_item_p1282(qid)
    if not p1282_value:
        return JSONResponse({
            "osm_objects": [],
            "warning": f"QID {qid} has no P1282 OSM tag",
            "url": f"https://www.wikidata.org/wiki/{qid}",
        })

    osm_tag_info = get_osm_tag_from_p1282(p1282_value)
    if not osm_tag_info:
        return JSONResponse({
            "osm_objects": [],
            "warning": f"Could not parse P1282 value: {p1282_value}",
        })

    tag_key, tag_value = osm_tag_info
    print(f"get_osm_nearby: querying OSM for {tag_key}={tag_value} near ({lat}, {lon})")

    osm_objects = osm_qlever.get_nearby_objects_by_tag(tag_key, tag_value, lat, lon, limit)
    print(f"get_osm_nearby: got {len(osm_objects)} OSM objects")

    return JSONResponse({"osm_objects": osm_objects})
