"""Database models for OSM data only."""

from __future__ import annotations

import abc
import json
import re
import typing

import sqlalchemy
from geoalchemy2 import Geometry
from sqlalchemy import func
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (
    Mapped,
    QueryPropertyDescriptor,
    column_property,
    deferred,
    mapped_column,
    registry,
)
from sqlalchemy.orm.decl_api import DeclarativeMeta
from sqlalchemy.schema import Column
from sqlalchemy.types import Float, Integer, String

from .database import session

mapper_registry = registry()


class Base(metaclass=DeclarativeMeta):
    """Database model base class."""

    __abstract__ = True

    registry = mapper_registry
    metadata = mapper_registry.metadata
    query: QueryPropertyDescriptor = session.query_property()

    __init__ = mapper_registry.constructor


re_point = re.compile(r"^POINT\((.+) (.+)\)$")


class MapMixin:
    """Map base class for OSM tables."""

    @declared_attr
    def __tablename__(cls):
        return "osm_" + cls.__name__.lower()

    src_id = Column("osm_id", Integer, primary_key=True, autoincrement=False)
    name = Column(String)
    admin_level = Column(String)
    boundary = Column(String)

    tags: Mapped[postgresql.hstore] = mapped_column(postgresql.HSTORE)

    @declared_attr
    def way(cls):
        return deferred(
            Column(Geometry("GEOMETRY", srid=4326, spatial_index=True), nullable=False)
        )

    @declared_attr
    def kml(cls) -> Mapped[str]:
        """Get object in KML format."""
        return column_property(func.ST_AsKML(cls.way), deferred=True)

    @declared_attr
    def geojson_str(cls) -> Mapped[str]:
        """Get object as GeoJSON string."""
        return column_property(
            func.ST_AsGeoJSON(cls.way, maxdecimaldigits=6), deferred=True
        )

    @declared_attr
    def as_EWKT(cls) -> Mapped[str]:
        """As EWKT."""
        return column_property(func.ST_AsEWKT(cls.way), deferred=True)

    @hybrid_property
    def has_street_address(self) -> bool:
        """Object has street address."""
        return "addr:housenumber" in self.tags and "addr:street" in self.tags

    def display_name(self) -> str:
        """Name for display."""
        for key in "bridge:name", "tunnel:name", "lock_name":
            if key in self.tags:
                return typing.cast(str, self.tags[key])

        return typing.cast(
            str,
            self.name
            or self.tags.get("addr:housename")
            or self.tags.get("inscription"),
        )

    def geojson(self) -> dict[str, typing.Any]:
        """Object GeoJSON parsed into Python data structure."""
        return typing.cast(dict[str, typing.Any], json.loads(self.geojson_str))

    def get_centroid(self) -> tuple[float, float]:
        """Centroid."""
        centroid = session.query(func.ST_AsText(func.ST_Centroid(self.way))).scalar()
        assert centroid
        assert (m := re_point.match(centroid))
        lon, lat = m.groups()
        return (float(lat), float(lon))

    @classmethod
    def coords_within(cls, lat: float, lon: float):
        point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
        return cls.query.filter(
            cls.admin_level.isnot(None), func.ST_Within(point, cls.way)
        ).order_by(cls.area)

    @property
    def id(self) -> int:
        """OSM id."""
        return abs(self.src_id)

    @property
    @abc.abstractmethod
    def type(self) -> str:
        """OSM type."""

    @property
    def identifier(self) -> str:
        """OSM identifier."""
        return f"{self.type}/{self.id}"

    @property
    def osm_url(self):
        """OSM URL."""
        return f"https://www.openstreetmap.org/{self.type}/{self.id}"


class Point(MapMixin, Base):
    """OSM point."""

    type = "node"


class Line(MapMixin, Base):
    """OSM line."""

    @property
    def type(self) -> str:
        """OSM type."""
        return "way" if self.src_id > 0 else "relation"

    @classmethod
    def get_osm(cls, osm_type: str, osm_id: int):
        src_id = osm_id * {"way": 1, "relation": -1}[osm_type]
        return cls.query.get(src_id)


class Polygon(MapMixin, Base):
    """OSM polygon."""

    way_area = Column(Float)

    @classmethod
    def get_osm(cls, osm_type: str, osm_id: int):
        src_id = osm_id * {"way": 1, "relation": -1}[osm_type]
        return cls.query.get(src_id)

    @property
    def type(self) -> str:
        """Polygon is either a way or a relation."""
        return "way" if self.src_id > 0 else "relation"

    @declared_attr
    def area(cls) -> sqlalchemy.orm.properties.ColumnProperty:
        """Polygon area."""
        return column_property(func.ST_Area(cls.way, False), deferred=True)

    @hybrid_property
    def area_in_sq_km(self) -> float:
        """Size of area in square km."""
        area: float = self.area
        return area / (1000 * 1000)
