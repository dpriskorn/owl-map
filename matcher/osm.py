"""OSM queries against local PostgreSQL database."""

from __future__ import annotations

import json
import re

import geoalchemy2
import sqlalchemy
from sqlalchemy.sql import select

from matcher import context, database, model

srid = 4326
re_point = re.compile(r"^POINT\((.+) (.+)\)$")


def make_envelope(bounds: list[float]) -> geoalchemy2.functions.ST_MakeEnvelope:
    """Make an envelope for the given bounds."""
    return sqlalchemy.func.ST_MakeEnvelope(*bounds, srid)


def parse_point(point_str: str) -> tuple[str, str]:
    """Parse point from PostGIS POINT string."""
    m = re_point.match(point_str)
    assert m
    lon, lat = m.groups()
    assert lon and lat
    return (lon, lat)


def get_country_iso3166_1(lat: float, lon: float) -> set[str]:
    """Return ISO country codes for given lat/lon."""
    pt = sqlalchemy.func.ST_SetSRID(sqlalchemy.func.ST_MakePoint(lon, lat), srid)
    alpha2_codes: set[str] = set()
    q = model.Polygon.query.filter(
        sqlalchemy.func.ST_Covers(model.Polygon.way, pt),
        model.Polygon.admin_level == "2",
    )
    for country in q:
        alpha2: str = country.tags.get("ISO3166-1")
        if alpha2:
            alpha2_codes.add(alpha2)
    context.set("alpha2_codes", alpha2_codes)
    return alpha2_codes


def is_street_number_first(lat: float, lon: float) -> bool:
    """Is lat/lon within a country that puts street number first?"""
    if lat is None or lon is None:
        return True
    alpha2 = get_country_iso3166_1(lat, lon)
    alpha2_number_first = {"GB", "IE", "US", "MX", "CA", "FR", "AU", "NZ", "ZA"}
    return bool(alpha2_number_first & alpha2)


def make_envelope_around_point(
    lat: float, lon: float, distance: float
) -> geoalchemy2.functions.ST_MakeEnvelope:
    """Make an envelope around a point."""
    conn = database.session.connection()
    p = sqlalchemy.sql.expression.cast(
        sqlalchemy.func.ST_MakePoint(lon, lat), geoalchemy2.Geography
    )
    s = select(
        *[
            sqlalchemy.func.ST_AsText(
                sqlalchemy.func.ST_Project(p, distance, sqlalchemy.func.radians(deg))
            )
            for deg in (0, 90, 180, 270)
        ]
    )
    coords = [parse_point(i) for i in conn.execute(s).fetchone()]
    north = float(coords[0][1])
    east = float(coords[1][0])
    south = float(coords[2][1])
    west = float(coords[3][0])
    return sqlalchemy.func.ST_MakeEnvelope(west, south, east, north, srid)


def drop_way_area(tags: dict[str, str]) -> dict[str, str]:
    """Remove way_area field from tags dict."""
    if "way_area" in tags:
        del tags["way_area"]
    return tags


def get_osm_in_bbox(bounds: list[float]) -> list[dict]:
    """Get all OSM objects within bounding box."""
    bbox_str = ",".join(str(v) for v in bounds)
    conn = database.session.connection()

    sql = f"""
    SELECT 'point' as tbl, osm_id, tags,
           ST_AsText(ST_Centroid(way)) as centroid,
           ST_AsGeoJSON(way) as geojson
    FROM osm_point
    WHERE ST_Intersects(ST_MakeEnvelope({bbox_str}, {srid}), way)

    UNION ALL

    SELECT 'line' as tbl, osm_id, tags,
           ST_AsText(ST_Centroid(ST_Collect(way))) AS centroid,
           ST_AsGeoJSON(ST_Collect(way)) AS geojson
    FROM osm_line
    WHERE ST_Intersects(ST_MakeEnvelope({bbox_str}, {srid}), way)
    GROUP BY osm_id, tags

    UNION ALL

    SELECT 'polygon' as tbl, osm_id, tags,
           ST_AsText(ST_Centroid(ST_Collect(way))) AS centroid,
           ST_AsGeoJSON(ST_Collect(way)) AS geojson
    FROM osm_polygon
    WHERE ST_Intersects(ST_MakeEnvelope({bbox_str}, {srid}), way)
    GROUP BY osm_id, tags
    HAVING ST_Area(ST_Collect(way)) < 20 * ST_Area(ST_MakeEnvelope({bbox_str}, {srid}))
    """
    result = conn.execute(sqlalchemy.text(sql))
    osm_objects = []
    for tbl, osm_id, tags, centroid, geojson in result:
        osm_type = "node" if tbl == "point" else ("way" if osm_id > 0 else "relation")
        osm_id = abs(osm_id)
        osm_objects.append({
            "identifier": f"{osm_type}/{osm_id}",
            "id": osm_id,
            "type": osm_type,
            "geojson": json.loads(geojson),
            "centroid": centroid,
            "name": tags.get("name") or tags.get("addr:housename") or "[no label]",
            "tags": drop_way_area(dict(tags)),
        })
    return osm_objects


def search_osm(query: str, bounds: list[float] | None = None, limit: int = 20) -> list[dict]:
    """Search OSM objects by name."""
    conn = database.session.connection()
    bbox_filter = ""
    if bounds:
        bbox_str = ",".join(str(v) for v in bounds)
        bbox_filter = f"AND ST_Intersects(ST_MakeEnvelope({bbox_str}, {srid}), way)"

    sql = f"""
    SELECT 'point' as tbl, osm_id, tags, 'POINT' as geom_type
    FROM osm_point
    WHERE tags->>'name' ILIKE :query {bbox_filter}

    UNION ALL

    SELECT 'line' as tbl, osm_id, tags, 'LINESTRING' as geom_type
    FROM osm_line
    WHERE tags->>'name' ILIKE :query {bbox_filter}

    UNION ALL

    SELECT 'polygon' as tbl, osm_id, tags, 'POLYGON' as geom_type
    FROM osm_polygon
    WHERE tags->>'name' ILIKE :query {bbox_filter}

    LIMIT :limit
    """
    result = conn.execute(sqlalchemy.text(sql), {"query": f"%{query}%", "limit": limit})
    hits = []
    for tbl, osm_id, tags, geom_type in result:
        osm_type = "node" if tbl == "point" else ("way" if osm_id > 0 else "relation")
        hits.append({
            "osm_type": osm_type,
            "osm_id": abs(osm_id),
            "name": tags.get("name", "[no name]"),
            "geom_type": geom_type,
        })
    return hits


def address_from_tags(tags: dict[str, str]) -> str | None:
    """Build address string from OSM tags."""
    keys = ["street", "housenumber"]
    if not all("addr:" + k in tags for k in keys):
        return None
    if context.get("street_number_first"):
        keys.reverse()
    return " ".join(tags["addr:" + k] for k in keys)


def address_node_label(tags: dict[str, str]) -> str | None:
    """Label for an OSM node based on tags."""
    address = address_from_tags(tags)
    return f"{tags['name']} ({address})" if "name" in tags else address
