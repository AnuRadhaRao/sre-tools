import os
import signal
import sys
import threading

from .model import StubModel
from .server import TriageStore, make_server


def main() -> int:
    port = int(os.environ.get("PORT", "8080"))
    server = make_server(port, StubModel(), TriageStore())

    # Containers stop with SIGTERM. Finish in-flight requests instead of being killed.
    def shutdown(signum, _frame):
        print(f"received signal {signum}, shutting down", flush=True)
        threading.Thread(target=server.shutdown).start()

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    print(f"triage-agent listening on :{port} (model: stub)", flush=True)
    server.serve_forever()
    server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
