"""Steady traffic against checkout, so the error rate has something to measure."""

import os
import signal
import sys
import time
import urllib.error
import urllib.request

TARGET = os.environ.get("TARGET", "http://checkout:8080/checkout")
INTERVAL = float(os.environ.get("INTERVAL_SECONDS", "0.2"))


def hit(url: str) -> int:
    try:
        # TARGET is a fixed http:// URL from the compose file, so S310 doesn't apply.
        with urllib.request.urlopen(url, timeout=2) as resp:  # noqa: S310
            return resp.status
    except urllib.error.HTTPError as err:
        return err.code
    except OSError:
        return 0  # checkout down or restarting; keep going


def main() -> None:
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    print(f"loadgen: GET {TARGET} every {INTERVAL}s", flush=True)
    while True:
        hit(TARGET)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
