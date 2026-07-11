"""GeoIP lookup using MaxMind DB."""

from __future__ import annotations

import typing

import maxminddb

_reader: maxminddb.Reader | None = None


def init_reader(path: str) -> None:
    """Initialize the MaxMind GeoIP reader."""
    global _reader
    _reader = maxminddb.open_database(path)


def close_reader() -> None:
    """Close the MaxMind GeoIP reader."""
    global _reader
    if _reader:
        _reader.close()
        _reader = None


def get_location(ip: str) -> dict[str, typing.Any] | None:
    """Get location data for an IP address."""
    if _reader is None:
        return None
    record = _reader.get(ip)
    if record and "location" in record:
        return typing.cast(dict[str, typing.Any], record["location"])
    return None
