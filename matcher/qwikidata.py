"""Wikidata queries via Qlever SPARQL endpoint."""

from __future__ import annotations

import os
import re

import yaml

from matcher.qlever import qlever

_queries_path = os.path.join(os.path.dirname(__file__), "queries.yaml")
with open(_queries_path) as f:
    _raw = yaml.safe_load(f)

QUERIES = {k: v.strip() for k, v in _raw.items()}

POINT_PATTERN = re.compile(r"POINT\(([0-9.-]+) ([0-9.-]+)\)")


def _parse_point(coord_str: str) -> tuple[float, float] | None:
    """Parse POINT(lon lat) string to (lat, lon) tuple."""
    m = POINT_PATTERN.match(coord_str)
    if m:
        lon, lat = float(m.group(1)), float(m.group(2))
        return (lat, lon)
    return None


def wikidata_items_count(bounds: list[float]) -> int:
    """Count Wikidata items with coordinates via Qlever."""
    query = QUERIES["wikidata_items_count"]
    result = qlever.execute_query(query)
    try:
        return int(result["results"]["bindings"][0]["count"]["value"])
    except (KeyError, IndexError, ValueError):
        return 0


def wikidata_items(bounds: list[float]) -> dict:
    """Get Wikidata items in bounding box via Qlever.

    Returns items dict keyed by QID, each with markers array.
    Labels are fetched by frontend from Wikidata REST API.
    """
    lat_min, lon_min, lat_max, lon_max = bounds
    query = QUERIES["wikidata_items"]
    result = qlever.execute_query(query)
    items: dict[str, dict] = {}
    try:
        for binding in result["results"]["bindings"]:
            qid = binding["item"]["value"].split("/")[-1]
            coord_str = binding["coord_str"]["value"]
            coords = _parse_point(coord_str)
            if coords:
                lat, lon = coords
                if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                    if qid not in items:
                        items[qid] = {"qid": qid, "markers": []}
                    items[qid]["markers"].append({"lat": lat, "lon": lon})
    except (KeyError, ValueError):
        pass
    return {"items": items, "isa_count": []}


def wikidata_isa_counts(bounds: list[float]) -> list[dict]:
    """Get IsA type counts via Qlever (ignores bbox filter due to Qlever limitations)."""
    query = QUERIES["wikidata_isa_counts"]
    result = qlever.execute_query(query)
    isa_count = []
    try:
        for binding in result["results"]["bindings"]:
            type_qid = binding["type"]["value"].split("/")[-1]
            count = int(binding["count"]["value"])
            isa_count.append({"qid": type_qid, "count": count, "label": type_qid})
    except (KeyError, ValueError):
        pass
    return isa_count


def get_item_coordinates(qid: str) -> tuple[float, float] | None:
    """Get coordinates for a single Wikidata item via Qlever."""
    query = QUERIES["get_item_coordinates"].format(qid=qid)
    result = qlever.execute_query(query)
    try:
        coord_str = result["results"]["bindings"][0]["coord"]["value"]
        return _parse_point(coord_str)
    except (KeyError, IndexError, ValueError):
        return None
