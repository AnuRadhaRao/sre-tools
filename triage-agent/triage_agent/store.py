"""Where triages are kept: in memory by default, or in Postgres when DATABASE_URL is set."""

import json
import threading
from importlib import resources
from typing import Protocol


class Store(Protocol):
    def add(self, item: dict) -> None: ...
    def all(self) -> list[dict]: ...


class MemoryStore:
    """Triages in process memory. Lost on restart; fine for tests and a quick local run."""

    def __init__(self):
        self._lock = threading.Lock()
        self._items: list[dict] = []

    def add(self, item: dict) -> None:
        with self._lock:
            self._items.append(item)

    def all(self) -> list[dict]:
        with self._lock:
            return list(self._items)


class PostgresStore:
    """Triages in a `triages` table. The full triage is kept as JSONB next to the
    columns worth filtering on, so new triage fields need no schema change."""

    def __init__(self, dsn: str):
        import psycopg  # only needed when a database is configured

        self._psycopg = psycopg
        self._dsn = dsn

    def _connect(self):
        return self._psycopg.connect(self._dsn, connect_timeout=5)

    def migrate(self) -> None:
        """Create the schema if it isn't there yet. Safe to run on every start."""
        schema = resources.files(__package__).joinpath("schema.sql").read_text()
        with self._connect() as conn:
            conn.execute(schema)

    def add(self, item: dict) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO triages (alert, fingerprint, severity, created_at, body)"
                " VALUES (%s, %s, %s, %s, %s)",
                (
                    item["alert"],
                    item["fingerprint"],
                    item["severity"],
                    item["created_at"],
                    json.dumps(item),
                ),
            )

    def all(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT body FROM triages ORDER BY id").fetchall()
        return [row[0] for row in rows]
