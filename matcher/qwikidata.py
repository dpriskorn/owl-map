"""Wikidata queries via Qlever SPARQL endpoint."""

from __future__ import annotations

import math
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


def _build_contains_filter(min_val: float, max_val: float) -> list[str]:
    """Build CONTAINS filters for approximate coordinate filtering.

    Returns list of string prefixes to search for in the POINT string.
    This is an approximate filter due to Qlever's lack of spatial predicates.
    """
    prefixes = []
    cur = math.floor(min_val * 10) / 10
    while cur <= max_val:
        prefix = f"{cur:.10g}".rstrip('0').rstrip('.')
        if '.' not in prefix:
            prefix += '.'
        prefixes.append(prefix)
        cur = round(cur + 0.1, 10)
    return prefixes


def _build_sparql_filter(bounds: list[float]) -> str:
    """Build SPARQL FILTER clause for approximate bbox filtering."""
    lat_min, lon_min, lat_max, lon_max = bounds

    lon_prefixes = _build_contains_filter(lon_min, lon_max)
    lat_prefixes = _build_contains_filter(lat_min, lat_max)

    lon_filter = " || ".join(f'CONTAINS(STR(?coord), "{p}")' for p in lon_prefixes)
    lat_filter = " || ".join(f'CONTAINS(STR(?coord), "{p}")' for p in lat_prefixes)

    return f"FILTER(({lon_filter}) && ({lat_filter}))"


def _build_items_query(bounds: list[float], isa_types: list[str] | None = None) -> str:
    """Build SPARQL query for items with bbox filter and optional ISA type filter."""
    bbox_filter = _build_sparql_filter(bounds)

    isa_filter = ""
    if isa_types:
        type_list = ", ".join(f"wd:{isa}" for isa in isa_types)
        isa_filter = f"?item wdt:P31 ?type . FILTER(?type IN ({type_list}))"

    return f"""PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX bd: <http://www.bigdata.com/rdf#>
SELECT ?item (STR(?coord) AS ?coord_str) WHERE {{
  ?item wdt:P625 ?coord .
  {bbox_filter}
  {isa_filter}
}}
LIMIT 400"""


def wikidata_items_count(bounds: list[float]) -> int:
    """Count Wikidata items with coordinates via Qlever."""
    query = QUERIES["wikidata_items_count"]
    result = qlever.execute_query(query)
    try:
        return int(result["results"]["bindings"][0]["count"]["value"])
    except (KeyError, IndexError, ValueError):
        return 0


def wikidata_items(bounds: list[float], isa_types: list[str] | None = None) -> dict:
    """Get Wikidata items in bounding box via Qlever.

    Returns items dict keyed by QID, each with markers array.
    Uses approximate string matching for bbox filter due to Qlever limitations.
    Labels are fetched by frontend from Wikidata REST API.
    """
    lat_min, lon_min, lat_max, lon_max = bounds
    query = _build_items_query(bounds, isa_types)
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
