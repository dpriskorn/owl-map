"""Wikidata REST API client with SQLite cache for labels and aliases."""

from __future__ import annotations

import json
import os
import time

import requests
import sqlalchemy


DEFAULT_CACHE_TTL = 86400  # 24 hours
CACHE_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "wikidata_cache.db")
_engine = None
_session = None


def _get_engine():
    global _engine
    if _engine is None:
        _engine = sqlalchemy.create_engine(f"sqlite:///{CACHE_DB_PATH}")
    return _engine


def _get_session():
    global _session
    if _session is None:
        _session = sqlalchemy.orm.sessionmaker(bind=_get_engine())()
    return _session


def init_cache():
    """Create cache tables if they don't exist."""
    engine = _get_engine()
    with engine.connect() as conn:
        conn.execute(sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS labels_cache (
                qid TEXT PRIMARY KEY,
                labels_json TEXT NOT NULL,
                fetched_at INTEGER NOT NULL
            )
        """))
        conn.execute(sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS aliases_cache (
                qid TEXT PRIMARY KEY,
                aliases_json TEXT NOT NULL,
                fetched_at INTEGER NOT NULL
            )
        """))
        conn.commit()


def _is_cache_valid(fetched_at: int, ttl: int = DEFAULT_CACHE_TTL) -> bool:
    """Check if cache entry is still valid."""
    return (time.time() - fetched_at) < ttl


class WikidataRestClient:
    """Client for Wikidata REST API with SQLite caching."""

    BASE_URL = "https://www.wikidata.org/w/rest.php/wikibase/v1"
    USER_AGENT = "owl-map/1.0 (https://github.com/dpriskorn/owl-map)"

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.USER_AGENT})
        self.cache_ttl = int(os.getenv("WIKIDATA_CACHE_TTL", DEFAULT_CACHE_TTL))
        init_cache()

    def _get_cached_labels(self, qids: list[str]) -> tuple[dict, list[str]]:
        """Get cached labels, returns (cached, missing_qids)."""
        if not qids:
            return {}, []

        session = _get_session()
        result = {}
        missing = []

        placeholders = ",".join([f":{i}" for i in range(len(qids))])
        rows = session.execute(
            sqlalchemy.text(f"""
                SELECT qid, labels_json, fetched_at FROM labels_cache
                WHERE qid IN ({placeholders})
            """),
            {str(i): qid for i, qid in enumerate(qids)},
        ).fetchall()

        cached_qids = set()
        for row in rows:
            if _is_cache_valid(row[2], self.cache_ttl):
                result[row[0]] = json.loads(row[1])
                cached_qids.add(row[0])
            else:
                missing.append(row[0])

        missing.extend(qid for qid in qids if qid not in cached_qids)
        return result, missing

    def _set_cached_labels(self, labels_map: dict[str, dict]) -> None:
        """Cache labels map."""
        if not labels_map:
            return

        session = _get_session()
        now = int(time.time())
        for qid, labels in labels_map.items():
            session.execute(
                sqlalchemy.text("""
                    INSERT OR REPLACE INTO labels_cache (qid, labels_json, fetched_at)
                    VALUES (:qid, :labels_json, :fetched_at)
                """),
                {"qid": qid, "labels_json": json.dumps(labels), "fetched_at": now},
            )
        session.commit()

    def get_labels(self, qids: list[str]) -> dict[str, dict]:
        """Get labels for multiple QIDs, using cache when possible."""
        if not qids:
            return {}

        cached, missing = self._get_cached_labels(qids)

        if missing:
            fetched = self._fetch_labels_batch(missing)
            self._set_cached_labels(fetched)
            cached.update(fetched)

        return cached

    def _fetch_labels_batch(self, qids: list[str]) -> dict[str, dict]:
        """Fetch labels from Wikidata REST API in batch."""
        result = {}
        for qid in qids:
            try:
                url = f"{self.BASE_URL}/entities/items/{qid}/labels"
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                result[qid] = response.json()
            except Exception:
                result[qid] = {}
        return result

    def _get_cached_aliases(self, qid: str) -> tuple[list, bool]:
        """Get cached aliases, returns (cached_aliases, is_valid)."""
        session = _get_session()
        row = session.execute(
            sqlalchemy.text("""
                SELECT aliases_json, fetched_at FROM aliases_cache WHERE qid = :qid
            """),
            {"qid": qid},
        ).fetchone()

        if row and _is_cache_valid(row[1], self.cache_ttl):
            return json.loads(row[0]), True
        return [], False

    def _set_cached_aliases(self, qid: str, aliases: list) -> None:
        """Cache aliases for a QID."""
        session = _get_session()
        now = int(time.time())
        session.execute(
            sqlalchemy.text("""
                INSERT OR REPLACE INTO aliases_cache (qid, aliases_json, fetched_at)
                VALUES (:qid, :aliases_json, :fetched_at)
            """),
            {"qid": qid, "aliases_json": json.dumps(aliases), "fetched_at": now},
        )
        session.commit()

    def get_aliases(self, qid: str) -> list[str]:
        """Get aliases for a single QID, using cache when possible."""
        cached, valid = self._get_cached_aliases(qid)
        if valid:
            return cached

        aliases = self._fetch_aliases(qid)
        self._set_cached_aliases(qid, aliases)
        return aliases

    def _fetch_aliases(self, qid: str) -> list[str]:
        """Fetch aliases from Wikidata REST API."""
        try:
            url = f"{self.BASE_URL}/entities/items/{qid}/aliases"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json().get("aliases", [])
        except Exception:
            return []


wikidata_client = WikidataRestClient()
