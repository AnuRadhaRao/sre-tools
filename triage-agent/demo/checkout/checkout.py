"""A tiny stand-in for a real service: the thing that breaks and gets alerted on.

GET  /checkout              answers 200, or 500 for a share of requests set by the fail rate
GET  /metrics               request counts in Prometheus text format
GET  /healthz               200 while the process is serving
POST /admin/fail-rate?rate= sets the share of /checkout requests that fail, 0.0 to 1.0
"""

import json
import os
import random
import signal
import threading
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit


class State:
    def __init__(self, fail_rate: float = 0.0):
        self._lock = threading.Lock()
        self.fail_rate = fail_rate
        self.requests: Counter[tuple[str, int]] = Counter()

    def record(self, path: str, code: int) -> None:
        with self._lock:
            self.requests[(path, code)] += 1

    def metrics(self) -> str:
        lines = [
            "# HELP http_requests_total Requests served, by path and status code.",
            "# TYPE http_requests_total counter",
        ]
        with self._lock:
            for (path, code), n in sorted(self.requests.items()):
                lines.append(f'http_requests_total{{path="{path}",code="{code}"}} {n}')
            lines += [
                "# HELP checkout_fail_rate Share of /checkout requests set to fail.",
                "# TYPE checkout_fail_rate gauge",
                f"checkout_fail_rate {self.fail_rate}",
            ]
        return "\n".join(lines) + "\n"


def make_server(port: int, state: State) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = urlsplit(self.path).path
            if path == "/healthz":
                self._send(200, {"status": "ok"})
            elif path == "/metrics":
                self._send_text(200, state.metrics())
            elif path == "/checkout":
                # Picks which requests fail; not used for anything security-related.
                failed = random.random() < state.fail_rate  # noqa: S311
                code = 500 if failed else 200
                state.record(path, code)
                self._send(code, {"order": "failed" if failed else "placed"})
            else:
                self._send(404, {"error": "not found"})

        def do_POST(self):
            url = urlsplit(self.path)
            if url.path != "/admin/fail-rate":
                return self._send(404, {"error": "not found"})
            try:
                rate = float(parse_qs(url.query)["rate"][0])
            except (KeyError, ValueError):
                return self._send(400, {"error": "pass ?rate= between 0.0 and 1.0"})
            if not 0.0 <= rate <= 1.0:
                return self._send(400, {"error": "pass ?rate= between 0.0 and 1.0"})
            state.fail_rate = rate
            self._send(200, {"fail_rate": rate})

        def _send(self, code, body):
            self._send_text(code, json.dumps(body), "application/json")

        def _send_text(self, code, text, content_type="text/plain; version=0.0.4"):
            payload = text.encode()
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, fmt, *args):
            pass  # /metrics is scraped every few seconds; logging each request is noise

    # Listen on all interfaces: inside a container that's how a published port reaches the app.
    return ThreadingHTTPServer(("0.0.0.0", port), Handler)  # noqa: S104


def main() -> None:
    state = State(float(os.environ.get("FAIL_RATE", "0")))
    server = make_server(int(os.environ.get("PORT", "8080")), state)
    signal.signal(signal.SIGTERM, lambda *_: threading.Thread(target=server.shutdown).start())
    print(f"checkout listening on :{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
