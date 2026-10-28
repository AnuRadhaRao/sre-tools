from typing import Protocol

from .alerts import Alert

# Every model must return exactly these keys. The pipeline checks this before anything is posted.
SUMMARY_FIELDS = ("impact", "likely_cause", "top_errors", "runbook_steps")


class Model(Protocol):
    name: str

    def summarize(self, alert: Alert, context: dict) -> dict: ...


class StubModel:
    """Deterministic stand-in for an LLM, so tests and CI never depend on one."""

    name = "stub"

    def summarize(self, alert: Alert, context: dict) -> dict:
        errors = context.get("top_errors", [])
        tickets = context.get("tickets", [])
        return {
            "impact": f"{len(tickets)} related customer ticket(s); severity {alert.severity}",
            "likely_cause": errors[0] if errors else alert.description or "not enough context",
            "top_errors": errors[:3],
            "runbook_steps": context.get("runbook_steps", []),
        }
