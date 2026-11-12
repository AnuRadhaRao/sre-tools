# triage-agent

A service that receives an alert and returns a short triage summary for the on-call engineer: impact, likely cause, top errors and runbook steps.

It's a personal project. The goal is an AI agent that pulls together chat history, customer tickets, logs and the runbook for an incoming alert, so the on-call engineer can triage quickly. All the data in this repo is made up. I'm also using it to practise the ideas from TechWorld with Nana's [Docker Tutorial for Beginners](https://www.youtube.com/playlist?list=PLy7NrYWoggjwPggqtFsI_zMAwvG0SqYCb) playlist.

## What works today

- `POST /webhook/alertmanager` accepts an [Alertmanager webhook](https://prometheus.io/docs/alerting/latest/configuration/#webhook_config) body, triages each firing alert, and returns the results. Resolved alerts are skipped.
- `GET /triages` lists stored triages, oldest first. With `DATABASE_URL` set they're kept in Postgres and survive restarts; without it they're held in memory.
- `GET /healthz` returns `200 {"status": "ok"}` while the process is serving.
- The summary comes from a **stub model**, a deterministic stand-in for an LLM. It fills in fields from the alert and from any context sources. No context sources are connected yet.
- Every model's output is checked for the four summary fields before it's returned. A context source that fails is listed in `sources_missing` instead of failing the triage.

Apart from the Postgres driver ([psycopg](https://www.psycopg.org/psycopg3/)), it uses only the Python standard library. The agent creates its table on start ([`schema.sql`](triage_agent/schema.sql)); the full triage is stored as JSONB next to the columns worth filtering on.

## Run locally

Requires Python 3.10 or later.

```sh
cd triage-agent
pip install -r requirements.txt
PORT=8080 python3 -m triage_agent      # in-memory store; set DATABASE_URL to use Postgres
curl -X POST localhost:8080/webhook/alertmanager \
  -H 'Content-Type: application/json' -d @examples/alert.json
```

`examples/alert.json` is a made-up alert. The service stops cleanly on `SIGTERM` or `Ctrl+C`.

## Run in Docker

```sh
cd triage-agent
docker build -t triage-agent:dev .
docker run --rm -p 8080:8080 triage-agent:dev
```

Then send `examples/alert.json` as above.

The Dockerfile has three stages:

| Stage | Base | What it does |
| --- | --- | --- |
| `test` | `python:3.12-slim` | Installs pytest and runs the test suite. A failing test fails the build. |
| `build` | `python:3.12-alpine` | Byte-compiles the package. |
| `runtime` | `python:3.12-alpine` | Holds only the compiled package. This is the image you run. |

Base images are pinned by digest, so a rebuild uses the same bases until the pin is updated. The runtime image is about 99 MB. That was 74 MB before the Postgres driver was added (psycopg's binary wheel bundles libpq), and 177 MB with the earlier single-stage `python:3.12-slim` build. It runs the app with `python -m triage_agent`, so `docker stop` reaches the process directly and it shuts down in under a second.

The runtime image also:

- runs as an unprivileged user (uid `10001`), so the app can read its code but can't change it;
- has a `HEALTHCHECK` that calls `/healthz` every 30 seconds, so `docker ps` shows `healthy` or `unhealthy`;
- carries standard [OCI labels](https://github.com/opencontainers/image-spec/blob/main/annotations.md) for the title, source, version and git commit. Pass the last two at build time:

```sh
docker build -t triage-agent:dev \
  --build-arg VERSION=0.1.0 --build-arg REVISION=$(git rev-parse --short HEAD) .
docker inspect -f '{{json .Config.Labels}}' triage-agent:dev
```

## Run the stack with Compose

`compose.yaml` runs the agent with everything it needs to receive a real alert, on one network called `triage`:

```text
loadgen ──> checkout <── scrape ── prometheus ──> alertmanager ──> agent ──> postgres <── adminer
```

| Service | Port | What it is |
| --- | --- | --- |
| `agent` | 8080 | This service. |
| `checkout` | 8081 | A small demo service in [`demo/checkout`](demo/checkout/checkout.py) that can be broken on purpose. It serves `/metrics` in Prometheus format. |
| `loadgen` | none | Sends steady traffic to `checkout`, so it has an error rate. |
| `prometheus` | 9090 | Scrapes `checkout` and evaluates [`monitoring/rules.yml`](monitoring/rules.yml). |
| `alertmanager` | 9093 | Sends every alert to the agent's webhook ([`monitoring/alertmanager.yml`](monitoring/alertmanager.yml)). |
| `postgres` | none | Stores triages on the named volume `pgdata`. Not published to the host. |
| `adminer` | 8082 | Web UI for the database. Log in with server `postgres`, user `triage` and the password from `.env`. |

Startup is ordered by health, not just by start: the agent and Adminer wait for Postgres, Alertmanager waits for the agent, and Prometheus and `loadgen` wait for `checkout`. The agent and `checkout` images use the same pattern: tests gate the build, the runtime is Alpine, and the app runs as a non-root user with a health check. Third-party images are pinned by version and digest.

Break `checkout` and watch the alert arrive:

The database password comes from a git-ignored `.env` file:

```sh
cd triage-agent
cp .env.example .env                                   # then change POSTGRES_PASSWORD
docker compose up -d --build --wait                   # returns once everything is healthy
curl -X POST 'localhost:8081/admin/fail-rate?rate=0.8' # 80% of checkouts now fail
# about a minute later: the rule fires (30s window, 30s "for"), Alertmanager groups it for 10s
curl -s localhost:8080/triages                         # the agent's triage of CheckoutHigh5xxRate
curl -X POST 'localhost:8081/admin/fail-rate?rate=0'   # fix it again
docker compose down && docker compose up -d --wait     # triages are still there afterwards
curl -s localhost:8080/triages
docker compose down -v                                 # -v also deletes the pgdata volume
```

The rule's windows are seconds rather than minutes so the demo is quick. Inside the network, services reach each other by name, for example `http://agent:8080/healthz`.

## Image registry

The image is never published to a public registry. It's kept in a private Docker Hub repository, `anuradhaarao12/devopslearning`. That one repository holds images for several projects, so tags are prefixed with the project name.

```sh
docker login
docker tag triage-agent:dev anuradhaarao12/devopslearning:triage-agent-0.1.0
docker push anuradhaarao12/devopslearning:triage-agent-0.1.0
```

Pulling it needs Docker Hub credentials with access to that repository.

## Test

```sh
cd triage-agent
pip install -r requirements-dev.txt
pytest
```

The store tests also run against Postgres when `TEST_DATABASE_URL` is set; without it, those cases are skipped and only the in-memory store is tested:

```sh
docker run -d --name pg-test -e POSTGRES_PASSWORD=test -p 15432:5432 postgres:17.10-alpine
TEST_DATABASE_URL=postgresql://postgres:test@127.0.0.1:15432/postgres pytest
docker rm -f pg-test
```
