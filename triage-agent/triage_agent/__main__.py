import os
import signal
import sys
import threading

from .model import StubModel
from .server import make_server
from .store import MemoryStore, PostgresStore, Store


def make_store() -> tuple[Store, str]:
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        return MemoryStore(), "memory"
    store = PostgresStore(dsn)
    store.migrate()  # also fails fast if the database is unreachable
    return store, "postgres"


def main() -> int:
    port = int(os.environ.get("PORT", "8080"))
    store, store_name = make_store()
    server = make_server(port, StubModel(), store)

    # Containers stop with SIGTERM. Finish in-flight requests instead of being killed.
    def shutdown(signum, _frame):
        print(f"received signal {signum}, shutting down", flush=True)
        threading.Thread(target=server.shutdown).start()

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    print(f"triage-agent listening on :{port} (model: stub, store: {store_name})", flush=True)
    server.serve_forever()
    server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
