"""Utility functions."""

import json
import math
import os.path
import re
import typing
from datetime import date
from itertools import islice
from typing import Any

import user_agents

from matcher.config import config as app_config
from num2words import num2words

metres_per_mile = 1609.344
feet_per_metre = 3.28084
feet_per_mile = 5280

T = typing.TypeVar("T")


def chunk(it: typing.Iterable[T], size: int) -> typing.Iterator[tuple[T, ...]]:
    """Split an iterable into chunks of the given size."""
    it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())


def flatten(top_list: list[list[T]]) -> list[T]:
    """Flatten a list."""
    return [item for sub_list in top_list for item in sub_list]


def drop_start(s: str, start: str) -> str:
    """Remove string prefix, otherwise throw an error."""
    assert s.startswith(start)
    return s[len(start) :]


def remove_start(s: str, start: str) -> str:
    """Remove a string prefix, if present."""
    return s[len(start) :] if s.startswith(start) else s


def normalize_url(url: str) -> str:
    """Standardize URLs to help in comparison."""
    for start in "http://", "https://", "www.":
        url = remove_start(url, start)
    return url.rstrip("/")


def contains_digit(s: str) -> bool:
    """Check if string contains a digit."""
    return any(c.isdigit() for c in s)


def cache_dir() -> str:
    """Get cache dir location."""
    return app_config["CACHE_DIR"]


def cache_filename(filename: str) -> str:
    """Get absolute path for cache file."""
    return os.path.join(cache_dir(), filename)


def load_from_cache(filename: str) -> Any:
    """Load JSON data from cache."""
    return json.load(open(cache_filename(filename)))


def get_radius(radius_str: str | None = None, default: int = 1000) -> int:
    """Parse radius from string or return default."""
    if radius_str and radius_str.isdigit():
        return int(radius_str)
    return default


def get_int_arg(value: str | None = None) -> int | None:
    """Convert a string value to integer."""
    if value and value.isdigit():
        return int(value)
    return None


def calc_chunk_size(area_in_sq_km: float, size: int = 22) -> int:
    """Work out the size of a chunk."""
    side = math.sqrt(area_in_sq_km)
    return max(1, math.ceil(side / size))


def file_missing_or_empty(filename: str) -> bool:
    """Check if a file is missing or empty."""
    return os.path.exists(filename) or os.stat(filename).st_size == 0


def is_bot(user_agent: str | None = None) -> bool:
    """Is the current request from a web robot."""
    return bool(user_agent and user_agents.parse(user_agent).is_bot)


def log_location() -> str:
    """Get log location from config."""
    return app_config["LOG_DIR"]


def capfirst(value: str) -> str:
    """Uppercase first letter of string, leave rest as is."""
    return value[0].upper() + value[1:] if value else value


def any_upper(value: str) -> bool:
    """Check if string contains any uppercase characters."""
    return any(c.isupper() for c in value)


def get_free_space(free_space_path: str) -> int:
    """Return the amount of available free space."""
    s = os.statvfs(free_space_path)
    return s.f_bsize * s.f_bavail


def metric_display_distance(units: str, dist: float) -> str | None:
    """Convert distance from metres to the specified metric units."""
    if units == "km_and_metres":
        units = "km" if dist > 500 else "metres"
    if units == "metres":
        return f"{dist:,.0f} m"
    if units == "km":
        return f"{dist / 1000:,.2f} km"

    return None


def display_distance(units: str, dist: float) -> str | None:
    """Convert distance from metres to the specified units."""
    if units in ("miles_and_feet", "miles_and_yards"):
        total_feet = dist * feet_per_metre
        miles = total_feet / feet_per_mile

        if miles > 0.5:
            return f"{miles:,.2f} miles"
        else:
            return {
                "miles_and_feet": f"{total_feet:,.0f} feet",
                "miles_and_yards": f"{total_feet / 3:,.0f} yards",
            }[units]

    if units == "miles_and_metres":
        miles = dist / metres_per_mile
        return f"{miles:,.2f} miles" if miles > 0.5 else f"{dist:,.0f} metres"

    return metric_display_distance(units, dist)


def is_in_range(address_range: str, address: str) -> bool:
    """Check if an address is within a range."""
    re_range = re.compile(r"\b(\d+) ?(?:to|-) ?(\d+)\b", re.I)
    re_number_list = re.compile(r"\b([\d, ]+) (?:and|&) (\d+)\b", re.I)
    re_number = re.compile(r"^(?:No\.?|Number)? ?(\d+)\b")

    m_number = re_number.match(address)
    if not m_number:
        return False

    m_range = re_range.search(address_range)
    if m_range:
        start, end = int(m_range.group(1)), int(m_range.group(2))
        if re_range.search(address):
            return False
        return start <= int(m_number.group(1)) <= end

    m_list = re_number_list.search(address_range)
    if m_list:
        numbers = {n.strip() for n in m_list.group(1).split(",")} | {m_list.group(2)}
        if re_number_list.search(address):
            return False
        return m_number.group(1) in numbers

    return False


class WikibaseTime(typing.TypedDict):
    """Wikibase Time dict."""

    precision: int
    time: str


def format_wikibase_time(v: WikibaseTime) -> str | None:
    """Format Wikibase time value into human readable string."""
    t = v["time"]

    ordinal_num: str
    match v["precision"]:
        case 11:  # year, month and day
            return date.fromisoformat(t[1:11]).strftime("%-d %B %Y")
        case 10:  # year and month
            return date.fromisoformat(t[1:8] + "-01").strftime("%B %Y")
        case 9:  # year
            return t[1:5]
        case 8:  # decade
            return f"{t[1:4]}0s"
        case 7:  # century
            century = ((int(t[:5]) - 1) // 100) + 1
            ordinal_num = num2words(abs(century), to="ordinal_num")
            return f"{ordinal_num} century{' BC' if century < 0 else ''}"
        case 6:  # millennium
            millennium = ((int(t[:5]) - 1) // 1000) + 1
            ordinal_num = num2words(abs(millennium), to="ordinal_num")
            return f"{ordinal_num} millennium{' BC' if millennium < 0 else ''}"
        case _:  # not handled
            return None
