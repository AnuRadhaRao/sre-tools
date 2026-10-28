# triage-agent

A service that receives an alert and returns a short triage summary for the on-call engineer: impact, likely cause, top errors and runbook steps.

It's a personal project. The goal is an AI agent that pulls together chat history, customer tickets, logs and the runbook for an incoming alert, so the on-call engineer can triage quickly. All the data in this repo is made up. I'm also using it to practise the ideas from TechWorld with Nana's [Docker Tutorial for Beginners](https://www.youtube.com/playlist?list=PLy7NrYWoggjwPggqtFsI_zMAwvG0SqYCb) playlist.

## What works today

- `POST /webhook/alertmanager` accepts an [Alertmanager webhook](https://prometheus.io/docs/alerting/latest/configuration/#webhook_config) body, triages each firing alert, and returns the results. Resolved alerts are skipped.
- `GET /triages` lists the triages made since the service started. They are held in memory only.
- `GET /healthz` returns `200 {"status": "ok"}` while the process is serving.
- The summary comes from a **stub model**, a deterministic stand-in for an LLM. It fills in fields from the alert and from any context sources. No context sources are connected yet.
- Every model's output is checked for the four summary fields before it's returned. A context source that fails is listed in `sources_missing` instead of failing the triage.

It uses only the Python standard library.

## Run locally

Requires Python 3.10 or later.

```sh
cd triage-agent
PORT=8080 python3 -m triage_agent
curl -X POST localhost:8080/webhook/alertmanager \
  -H 'Content-Type: application/json' -d @examples/alert.json
```

`examples/alert.json` is a made-up alert. The service stops cleanly on `SIGTERM` or `Ctrl+C`.

## Test

```sh
cd triage-agent
pip install -r requirements-dev.txt
pytest
```
