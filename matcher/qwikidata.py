"""Wikidata queries via Qlever SPARQL endpoint."""

from __future__ import annotations

from matcher.qlever import qlever


def wikidata_items_count(bounds: list[float]) -> int:
    """Count Wikidata items in bounding box via Qlever."""
    lat_min, lon_min, lat_max, lon_max = bounds
    query = f"""
    SELECT COUNT(DISTINCT ?item) WHERE {{
      ?item wdt:P625 ?coord .
      ?coord wikibase:geoLatitude ?lat .
      ?coord wikibase:geoLongitude ?lon .
      FILTER(?lat >= {lat_min} && ?lat <= {lat_max} &&
             ?lon >= {lon_min} && ?lon <= {lon_max})
    }}
    """
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
    query = f"""
    SELECT ?item ?lat ?lon WHERE {{
      ?item wdt:P625 ?coord .
      ?coord wikibase:geoLatitude ?lat .
      ?coord wikibase:geoLongitude ?lon .
      FILTER(?lat >= {lat_min} && ?lat <= {lat_max} &&
             ?lon >= {lon_min} && ?lon <= {lon_max})
    }}
    """
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
    query = f"""
    SELECT ?type (COUNT(DISTINCT ?item) AS ?count) WHERE {{
      ?item wdt:P31 ?type ;
            wdt:P625 ?coord .
      ?coord wikibase:geoLatitude ?lat .
      ?coord wikibase:geoLongitude ?lon .
      FILTER(?lat >= {lat_min} && ?lat <= {lat_max} &&
             ?lon >= {lon_min} && ?lon <= {lon_max})
    }}
    GROUP BY ?type
    ORDER BY DESC(?count)
    LIMIT 100
    """
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
    query = f"""
    SELECT ?lat ?lon WHERE {{
      wd:{qid} wdt:P625 ?coord .
      ?coord wikibase:geoLatitude ?lat .
      ?coord wikibase:geoLongitude ?lon .
    }}
    """
    result = qlever.execute_query(query)
    try:
        lat = float(result["results"]["bindings"][0]["lat"]["value"])
        lon = float(result["results"]["bindings"][0]["lon"]["value"])
        return (lat, lon)
    except (KeyError, IndexError, ValueError):
        return None
