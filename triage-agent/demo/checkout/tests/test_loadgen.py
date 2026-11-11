import threading

from checkout import State, make_server
from loadgen import hit


def test_hit_returns_status_codes_and_counts_requests():
    state = State()
    srv = make_server(0, state)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_port}/checkout"
    try:
        assert hit(url) == 200
        state.fail_rate = 1.0
        assert hit(url) == 500
        assert state.requests[("/checkout", 200)] == 1
        assert state.requests[("/checkout", 500)] == 1
    finally:
        srv.shutdown()
        srv.server_close()


def test_hit_survives_checkout_being_down():
    assert hit("http://127.0.0.1:9/checkout") == 0
