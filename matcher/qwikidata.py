"""Wikidata queries via Qlever SPARQL endpoint."""

from __future__ import annotations

import os

import yaml

from matcher.qlever import qlever

_queries_path = os.path.join(os.path.dirname(__file__), "queries.yaml")
with open(_queries_path) as f:
    QUERIES = yaml.safe_load(f)


def wikidata_items_count(bounds: list[float]) -> int:
    """Count Wikidata items in bounding box via Qlever."""
    lat_min, lon_min, lat_max, lon_max = bounds
    query = QUERIES["wikidata_items_count"].format(
        lat_min=lat_min, lon_min=lon_min,
        lat_max=lat_max, lon_max=lon_max
    )
    result = qlever.execute_query(query)
    try:
        return int(result["results"]["bindings"][0]["callret-0"]["value"])
    except (KeyError, IndexError, ValueError):
        return 0


def wikidata_items(bounds: list[float]) -> dict:
    """Get Wikidata items in bounding box via Qlever.

    Returns items dict keyed by QID, each with markers array.
    Labels are fetched by frontend from Wikidata REST API.
    """
    lat_min, lon_min, lat_max, lon_max = bounds
    query = QUERIES["wikidata_items"].format(
        lat_min=lat_min, lon_min=lon_min,
        lat_max=lat_max, lon_max=lon_max
    )
    result = qlever.execute_query(query)
    items: dict[str, dict] = {}
    try:
        for binding in result["results"]["bindings"]:
            qid = binding["item"]["value"].split("/")[-1]
            lat = float(binding["lat"]["value"])
            lon = float(binding["lon"]["value"])
            if qid not in items:
                items[qid] = {"qid": qid, "markers": []}
            items[qid]["markers"].append({"lat": lat, "lon": lon})
    except (KeyError, ValueError):
        pass
    return {"items": items, "isa_count": []}


def wikidata_isa_counts(bounds: list[float]) -> list[dict]:
    """Get IsA type counts in bounding box via Qlever."""
    lat_min, lon_min, lat_max, lon_max = bounds
    query = QUERIES["wikidata_isa_counts"].format(
        lat_min=lat_min, lon_min=lon_min,
        lat_max=lat_max, lon_max=lon_max
    )
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
        lat = float(result["results"]["bindings"][0]["lat"]["value"])
        lon = float(result["results"]["bindings"][0]["lon"]["value"])
        return (lat, lon)
    except (KeyError, IndexError, ValueError):
        return None
