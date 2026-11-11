import os
import uuid

import pytest

from triage_agent.store import MemoryStore, PostgresStore

# The Postgres case needs a real database. Locally: start one and set TEST_DATABASE_URL
# (see the README). Without it, only the in-memory store is tested.
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")


def triage(alert="CheckoutHigh5xxRate"):
    return {
        "alert": alert,
        "fingerprint": uuid.uuid4().hex[:16],
        "severity": "critical",
        "runbook_url": None,
        "impact": "i",
        "likely_cause": "c",
        "top_errors": ["e"],
        "runbook_steps": [],
        "sources_missing": [],
        "model": "stub",
        "created_at": "2026-11-11T22:00:00+00:00",
    }


@pytest.fixture(params=["memory", "postgres"])
def store(request):
    if request.param == "memory":
        return MemoryStore()
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL not set")
    import psycopg

    pg = PostgresStore(TEST_DATABASE_URL)
    pg.migrate()
    pg.migrate()  # running it twice must be harmless
    with psycopg.connect(TEST_DATABASE_URL) as conn:
        conn.execute("TRUNCATE triages")
    return pg


def test_store_returns_triages_in_insertion_order(store):
    first, second = triage("A"), triage("B")
    store.add(first)
    store.add(second)
    assert store.all() == [first, second]


def test_empty_store_returns_empty_list(store):
    assert store.all() == []
