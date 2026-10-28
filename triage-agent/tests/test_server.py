import json
import threading
import urllib.error
import urllib.request

import pytest

from triage_agent.model import StubModel
from triage_agent.server import TriageStore, make_server


@pytest.fixture
def app():
    srv = make_server(0, StubModel(), TriageStore())
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()
    srv.server_close()


def call(url, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=2) as resp:
        return resp.status, json.load(resp)


def test_healthz(app):
    assert call(f"{app}/healthz") == (200, {"status": "ok"})


def test_webhook_triages_firing_alerts_and_stores_them(app, alert_payload):
    status, results = call(f"{app}/webhook/alertmanager", alert_payload)
    assert status == 200 and results[0]["alert"] == "CheckoutHigh5xxRate"
    assert call(f"{app}/triages")[1] == results


def test_resolved_alerts_are_skipped(app, alert_payload):
    alert_payload["alerts"][0]["status"] = "resolved"
    assert call(f"{app}/webhook/alertmanager", alert_payload) == (200, [])


def test_bad_body_is_400(app):
    with pytest.raises(urllib.error.HTTPError) as exc:
        call(f"{app}/webhook/alertmanager", {"not": "alertmanager"})
    assert exc.value.code == 400
