import json
import threading
import urllib.error
import urllib.request

import pytest

from checkout import State, make_server


@pytest.fixture
def app():
    state = State()
    srv = make_server(0, state)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}", state
    srv.shutdown()
    srv.server_close()


def call(url, method="GET"):
    req = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as err:
        return err.code, err.read().decode()


def test_healthy_checkout_places_orders(app):
    url, _ = app
    assert call(f"{url}/healthz")[0] == 200
    assert call(f"{url}/checkout") == (200, json.dumps({"order": "placed"}))


def test_fail_rate_one_breaks_every_checkout(app):
    url, state = app
    assert call(f"{url}/admin/fail-rate?rate=1", "POST")[0] == 200
    assert state.fail_rate == 1.0
    assert all(call(f"{url}/checkout")[0] == 500 for _ in range(5))


@pytest.mark.parametrize("query", ["", "?rate=abc", "?rate=1.5", "?rate=-0.1"])
def test_bad_fail_rate_is_rejected(app, query):
    url, state = app
    assert call(f"{url}/admin/fail-rate{query}", "POST")[0] == 400
    assert state.fail_rate == 0.0


def test_metrics_count_requests_by_code(app):
    url, _ = app
    call(f"{url}/checkout")
    call(f"{url}/admin/fail-rate?rate=1", "POST")
    call(f"{url}/checkout")
    status, body = call(f"{url}/metrics")
    assert status == 200
    assert 'http_requests_total{path="/checkout",code="200"} 1' in body
    assert 'http_requests_total{path="/checkout",code="500"} 1' in body
    assert "checkout_fail_rate 1.0" in body
