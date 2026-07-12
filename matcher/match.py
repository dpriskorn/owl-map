"""Matching logic for Wikidata items and OSM objects."""

from __future__ import annotations

import re
from typing import Any


POINT_PATTERN = re.compile(r"POINT\(([0-9.-]+) ([0-9.-]+)\)")


def parse_wkt_point(wkt_str: str) -> tuple[float, float] | None:
    """Parse WKT POINT string to (lat, lon) tuple."""
    m = POINT_PATTERN.match(wkt_str)
    if m:
        lon, lat = float(m.group(1)), float(m.group(2))
        return (lat, lon)
    return None


def match_wikidata_to_osm(
    wikidata_items: dict[str, Any],
    osm_objects: dict[str, Any],
    isa_type: str | None = None
) -> dict[str, Any]:
    """Match Wikidata items to OSM objects based on wikidata references.

    Args:
        wikidata_items: Dict of Wikidata items keyed by QID
        osm_objects: Dict of OSM objects keyed by OSM ID
        isa_type: Optional ISA type QID (not used in matching, for context)

    Returns:
        {
            "matched": [...],       # OSM objects that match a WD item
            "wikidata_only": [...], # WD items with no matching OSM object
            "osm_only": [...],      # OSM objects with wikidata but not in our WD items
        }
    """
    matched = []
    wikidata_only = []
    osm_only = []

    wikidata_qids = set(wikidata_items.keys())

    for osm_id, osm_obj in osm_objects.items():
        wikidata_qid = osm_obj.get("wikidata_qid")
        if wikidata_qid and wikidata_qid in wikidata_qids:
            matched.append({
                "osm_id": osm_id,
                "osm": osm_obj,
                "wikidata_qid": wikidata_qid,
                "wikidata": wikidata_items[wikidata_qid],
            })
        else:
            osm_only.append({
                "osm_id": osm_id,
                "osm": osm_obj,
                "wikidata_qid": wikidata_qid,
            })

    matched_wikidata_qids = {m["wikidata_qid"] for m in matched}
    for qid, item in wikidata_items.items():
        if qid not in matched_wikidata_qids:
            wikidata_only.append({
                "wikidata_qid": qid,
                "wikidata": item,
            })

    return {
        "matched": matched,
        "wikidata_only": wikidata_only,
        "osm_only": osm_only,
    }


def get_osm_tag_from_p1282(p1282_value: str | None) -> tuple[str, str] | None:
    """Parse P1282 string to (key, value) tuple.

    P1282 is formatted as "key=value" e.g., "leisure=bathing_place"

    Args:
        p1282_value: The P1282 statement value

    Returns:
        Tuple of (tag_key, tag_value) or None if invalid format
    """
    if not p1282_value:
        return None
    if "=" in p1282_value:
        key, value = p1282_value.split("=", 1)
        return (key.strip(), value.strip())
    return None
