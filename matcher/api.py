"""Unified API interface.

Imports from osm and qwikidata modules to provide
a consistent API for the application.
"""

from matcher.osm import (
    address_from_tags,
    address_node_label,
    drop_way_area,
    get_osm_in_bbox,
    is_street_number_first,
    search_osm,
)
from matcher.qwikidata import (
    get_item_coordinates,
    wikidata_isa_counts,
    wikidata_items,
    wikidata_items_count,
)

__all__ = [
    "address_from_tags",
    "address_node_label",
    "drop_way_area",
    "get_item_coordinates",
    "get_osm_in_bbox",
    "is_street_number_first",
    "search_osm",
    "wikidata_isa_counts",
    "wikidata_items",
    "wikidata_items_count",
]
