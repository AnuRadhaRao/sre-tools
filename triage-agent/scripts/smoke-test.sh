#!/usr/bin/env sh
# End-to-end check of the running Compose stack. It breaks checkout, waits for
# the alert to travel Prometheus -> Alertmanager -> agent, then restarts the
# agent and checks the triage is still there, so it came from Postgres.
#
# Run it against a fresh stack:
#   docker compose up -d --build --wait && scripts/smoke-test.sh
set -eu
cd "$(dirname "$0")/.."

AGENT=${AGENT_URL:-http://localhost:8080}
CHECKOUT=${CHECKOUT_URL:-http://localhost:8081}
TIMEOUT=${SMOKE_TIMEOUT:-180}
ALERT=CheckoutHigh5xxRate

# Prints the stored triage for $ALERT and succeeds, or fails if there is none yet.
find_triage() {
  curl -fsS "$AGENT/triages" | python3 -c '
import json, sys
found = [t for t in json.load(sys.stdin) if t["alert"] == sys.argv[1]]
if not found:
    sys.exit(1)
print(json.dumps(found[-1], indent=2))
' "$ALERT"
}

wait_for_triage() {
  start=$(date +%s)
  until find_triage >/dev/null 2>&1; do
    if [ $(($(date +%s) - start)) -ge "$TIMEOUT" ]; then
      echo "FAIL: no $ALERT triage after ${TIMEOUT}s" >&2
      exit 1
    fi
    sleep 5
  done
  echo "$(($(date +%s) - start))"
}

if find_triage >/dev/null 2>&1; then
  echo "FAIL: a $ALERT triage already exists. Start from a fresh stack: docker compose down -v" >&2
  exit 1
fi

echo "Breaking checkout: 80% of requests now fail"
curl -fsS -X POST "$CHECKOUT/admin/fail-rate?rate=0.8" >/dev/null
trap 'curl -fsS -X POST "$CHECKOUT/admin/fail-rate?rate=0" >/dev/null || true' EXIT

echo "Waiting up to ${TIMEOUT}s for the agent to triage $ALERT"
elapsed=$(wait_for_triage)
echo "ok: triage stored after ${elapsed}s"

echo "Restarting the agent: the triage must come back from Postgres"
docker compose restart agent >/dev/null 2>&1
docker compose up -d --wait agent >/dev/null 2>&1
find_triage >/dev/null || { echo "FAIL: triage missing after agent restart" >&2; exit 1; }
echo "ok: triage survived the restart"
find_triage
