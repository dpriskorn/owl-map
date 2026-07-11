"""Test wikidata coordinate handling."""

from matcher.wikidata import read_location_statement, read_coords


def test_read_coords_with_deprecated() -> None:
    """Test that deprecated coordinates are filtered out."""
    claims = {
        "P625": [
            {
                "mainsnak": {
                    "snaktype": "value",
                    "property": "P625",
                    "datavalue": {
                        "value": {
                            "latitude": 52.0,
                            "longitude": 0.0,
                            "globe": "http://www.wikidata.org/entity/Q2",
                        },
                        "type": "globecoordinate",
                    },
                },
                "type": "statement",
                "rank": "deprecated",
            },
        ],
    }
    coords = read_location_statement(claims, "P625")
    assert coords == []


def test_read_coords_with_normal() -> None:
    """Test that normal rank coordinates are kept."""
    claims = {
        "P625": [
            {
                "mainsnak": {
                    "snaktype": "value",
                    "property": "P625",
                    "datavalue": {
                        "value": {
                            "latitude": 52.0,
                            "longitude": 0.0,
                            "globe": "http://www.wikidata.org/entity/Q2",
                        },
                        "type": "globecoordinate",
                    },
                },
                "type": "statement",
                "rank": "normal",
            },
        ],
    }
    coords = read_location_statement(claims, "P625")
    assert len(coords) == 1
    assert coords[0]["latitude"] == 52.0
    assert coords[0]["longitude"] == 0.0


def test_read_coords_with_preferred() -> None:
    """Test that preferred rank coordinates are kept."""
    claims = {
        "P625": [
            {
                "mainsnak": {
                    "snaktype": "value",
                    "property": "P625",
                    "datavalue": {
                        "value": {
                            "latitude": 52.0,
                            "longitude": 0.0,
                            "globe": "http://www.wikidata.org/entity/Q2",
                        },
                        "type": "globecoordinate",
                    },
                },
                "type": "statement",
                "rank": "preferred",
            },
        ],
    }
    coords = read_location_statement(claims, "P625")
    assert len(coords) == 1
    assert coords[0]["latitude"] == 52.0
    assert coords[0]["longitude"] == 0.0


def test_read_coords_mixed_ranks() -> None:
    """Test that only non-deprecated coordinates are returned."""
    claims = {
        "P625": [
            {
                "mainsnak": {
                    "snaktype": "value",
                    "property": "P625",
                    "datavalue": {
                        "value": {
                            "latitude": 52.0,
                            "longitude": 0.0,
                            "globe": "http://www.wikidata.org/entity/Q2",
                        },
                        "type": "globecoordinate",
                    },
                },
                "type": "statement",
                "rank": "deprecated",
            },
            {
                "mainsnak": {
                    "snaktype": "value",
                    "property": "P625",
                    "datavalue": {
                        "value": {
                            "latitude": 53.0,
                            "longitude": 1.0,
                            "globe": "http://www.wikidata.org/entity/Q2",
                        },
                        "type": "globecoordinate",
                    },
                },
                "type": "statement",
                "rank": "normal",
            },
        ],
    }
    coords = read_location_statement(claims, "P625")
    assert len(coords) == 1
    assert coords[0]["latitude"] == 53.0
    assert coords[0]["longitude"] == 1.0
