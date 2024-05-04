"""Match OSM and Wikidata items."""

CallParams = dict[str, str | int]

user_agent = (
    "osm-wikidata/0.2 (https://git.4angle.com/edward/owl-map; edward@4angle.com)"
)


def user_agent_headers() -> dict[str, str]:
    """User-Agent headers."""
    return {"User-Agent": user_agent}
