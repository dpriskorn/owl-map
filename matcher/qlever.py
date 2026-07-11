"""Qlever integration for Wikidata SPARQL queries."""

from __future__ import annotations

import requests


class QleverIntegrator:
    """Qlever SPARQL endpoint for Wikidata."""

    def __init__(
        self,
        endpoint: str = "https://qlever.cs.uni-freiburg.de/api/wikidata",
        user_agent: str = "owl-map/1.0 (https://github.com/dpriskorn/owl-map)",
    ) -> None:
        self.endpoint = endpoint
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    def execute_query(self, query: str) -> dict:
        """Execute a SPARQL query and return JSON results."""
        params = {"query": query, "action": "json_export"}
        response = self.session.get(self.endpoint, params=params, timeout=60)
        response.raise_for_status()
        return response.json()


qlever = QleverIntegrator()
