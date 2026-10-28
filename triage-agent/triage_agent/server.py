import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .alerts import parse_alertmanager
from .triage import triage

MAX_BODY_BYTES = 1_000_000


class TriageStore:
    """Recent triages in memory. Persistence comes with the database."""

    def __init__(self):
        self._lock = threading.Lock()
        self._items: list[dict] = []

    def add(self, item: dict) -> None:
        with self._lock:
            self._items.append(item)

    def all(self) -> list[dict]:
        with self._lock:
            return list(self._items)


def make_server(port: int, model, store: TriageStore, sources: dict | None = None) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/healthz":
                self._send(200, {"status": "ok"})
            elif self.path == "/triages":
                self._send(200, store.all())
            else:
                self._send(404, {"error": "not found"})

        def do_POST(self):
            if self.path != "/webhook/alertmanager":
                return self._send(404, {"error": "not found"})
            length = int(self.headers.get("Content-Length", 0))
            if length > MAX_BODY_BYTES:
                return self._send(413, {"error": "body too large"})
            try:
                alerts = parse_alertmanager(json.loads(self.rfile.read(length) or b"null"))
            except (ValueError, json.JSONDecodeError) as exc:
                return self._send(400, {"error": str(exc)})

            results = []
            for alert in alerts:
                if alert.status != "firing":
                    continue  # resolved notifications need no triage
                result = triage(alert, model, sources).to_dict()
                store.add(result)
                results.append(result)
            self._send(200, results)

        def _send(self, code, body):
            payload = json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, fmt, *args):
            # One line per request on stdout, so `docker logs` shows it.
            print(f"{self.address_string()} {fmt % args}", flush=True)

    return ThreadingHTTPServer(("0.0.0.0", port), Handler)
