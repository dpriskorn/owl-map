"""OSM Qlever integration for spatial OSM data queries."""

from __future__ import annotations

import re
from typing import Any

import requests


POINT_PATTERN = re.compile(r"POINT\(([0-9.-]+) ([0-9.-]+)\)")


class OSMQlever:
    """OSM Qlever SPARQL endpoint for Wikidata."""

    def __init__(
        self,
        endpoint: str = "https://qlever.dev/osm-planet",
        user_agent: str = "owl-map/1.0 (https://github.com/dpriskorn/owl-map)",
    ) -> None:
        self.endpoint = endpoint
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    def execute_query(self, query: str) -> dict:
        """Execute a SPARQL query and return JSON results."""
        print(f"osm_qlever executing query:\n{query[:500]}...")
        params = {"query": query, "action": "json_export"}
        response = self.session.get(self.endpoint, params=params, timeout=60)
        print(f"osm_qlever response status: {response.status_code}")
        response.raise_for_status()
        result = response.json()
        print(f"osm_qlever got {len(result.get('results', {}).get('bindings', []))} bindings")
        return result

    def get_objects_by_tag(
        self,
        tag_key: str,
        tag_value: str,
        bbox: list[float],
    ) -> dict[str, Any]:
        """Get OSM objects by tag within bbox.

        Args:
            tag_key: OSM tag key (e.g., "leisure")
            tag_value: OSM tag value (e.g., "bathing_place")
            bbox: [lat_min, lon_min, lat_max, lon_max]

        Returns:
            Dict of OSM objects keyed by OSM ID, each with markers and optional wikidata reference
        """
        lat_min, lon_min, lat_max, lon_max = bbox
        polygon = f"POLYGON(({lon_min} {lat_min}, {lon_max} {lat_min}, {lon_max} {lat_max}, {lon_min} {lat_max}, {lon_min} {lat_min}))"

        query = f"""PREFIX osmkey: <https://www.openstreetmap.org/wiki/Key:>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX osm2rdfkey: <https://osm2rdf.cs.uni-freiburg.de/rdf/key#>
SELECT ?osm_id ?geometry ?wikidata WHERE {{
  ?osm_id osmkey:{tag_key} "{tag_value}" .
  ?osm_id geo:hasGeometry/geo:asWKT ?geometry .
  OPTIONAL {{ ?osm_id osm2rdfkey:wikidata ?wikidata }}
  FILTER(geof:sfIntersects(?geometry, "{polygon}"^^geo:wktLiteral))
}}
LIMIT 500"""

        print(f"osm_qlever get_objects_by_tag query:\n{query}")
        result = self.execute_query(query)

        objects: dict[str, Any] = {}
        try:
            for binding in result["results"]["bindings"]:
                osm_id = binding["osm_id"]["value"]
                wkt_str = binding["geometry"]["value"]
                wikidata_ref = None
                if "wikidata" in binding:
                    wikidata_ref = binding["wikidata"]["value"].split("/")[-1]

                coords = self._parse_wkt_point(wkt_str)
                if coords:
                    lat, lon = coords
                    if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                        if osm_id not in objects:
                            objects[osm_id] = {
                                "osm_id": osm_id,
                                "markers": [],
                                "wikidata_qid": wikidata_ref,
                            }
                        objects[osm_id]["markers"].append({"lat": lat, "lon": lon})
        except (KeyError, ValueError):
            pass

        return objects

    def get_nearby_objects_by_tag(
        self,
        tag_key: str,
        tag_value: str,
        lat: float,
        lon: float,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get OSM objects with tag near a point, sorted by distance.

        Args:
            tag_key: OSM tag key
            tag_value: OSM tag value
            lat: Latitude of center point
            lon: Longitude of center point
            limit: Maximum number of results

        Returns:
            List of OSM objects sorted by distance to center point
        """
        center_wkt = f"Point({lon} {lat})"

        query = f"""PREFIX osmkey: <https://www.openstreetmap.org/wiki/Key:>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX geof: <http://www.opengis.net/def/function/geosparql#>
PREFIX osm2rdfkey: <https://osm2rdf.cs.uni-freiburg.de/rdf/key#>
SELECT ?osm_id ?geometry ?wikidata (geof:distance(?geometry, "{center_wkt}"^^geo:wktLiteral) AS ?distance) WHERE {{
  ?osm_id osmkey:{tag_key} "{tag_value}" .
  ?osm_id geo:hasGeometry/geo:asWKT ?geometry .
  OPTIONAL {{ ?osm_id osm2rdfkey:wikidata ?wikidata }}
}}
ORDER BY ?distance
LIMIT {limit}"""

        print(f"osm_qlever get_nearby_objects_by_tag query:\n{query}")
        result = self.execute_query(query)

        objects = []
        try:
            for binding in result["results"]["bindings"]:
                osm_id = binding["osm_id"]["value"]
                wkt_str = binding["geometry"]["value"]
                wikidata_ref = None
                if "wikidata" in binding:
                    wikidata_ref = binding["wikidata"]["value"].split("/")[-1]
                distance = float(binding["distance"]["value"])

                coords = self._parse_wkt_point(wkt_str)
                if coords:
                    obj_lat, obj_lon = coords
                    objects.append({
                        "osm_id": osm_id,
                        "lat": obj_lat,
                        "lon": obj_lon,
                        "wikidata_qid": wikidata_ref,
                        "distance": distance,
                    })
        except (KeyError, ValueError):
            pass

        return objects

    def _parse_wkt_point(self, wkt_str: str) -> tuple[float, float] | None:
        """Parse WKT POINT string to (lat, lon) tuple."""
        m = POINT_PATTERN.match(wkt_str)
        if m:
            lon, lat = float(m.group(1)), float(m.group(2))
            return (lat, lon)
        return None


osm_qlever = OSMQlever()

