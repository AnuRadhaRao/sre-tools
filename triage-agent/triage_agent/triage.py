from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from .alerts import Alert
from .model import SUMMARY_FIELDS, Model


@dataclass(frozen=True)
class Triage:
    alert: str
    fingerprint: str
    severity: str
    runbook_url: str | None
    impact: str
    likely_cause: str
    top_errors: list
    runbook_steps: list
    sources_missing: list
    model: str
    created_at: str

    def to_dict(self) -> dict:
        return asdict(self)


def gather_context(alert: Alert, sources: dict) -> tuple[dict, list]:
    """Ask each source for context. A failing source is recorded as missing, never fatal."""
    context, missing = {}, []
    for name, fetch in sources.items():
        try:
            context.update(fetch(alert))
        except Exception:
            missing.append(name)
    return context, missing


def triage(alert: Alert, model: Model, sources: dict | None = None) -> Triage:
    context, missing = gather_context(alert, sources or {})
    summary = model.summarize(alert, context)
    if set(summary) != set(SUMMARY_FIELDS):
        raise ValueError(f"model {model.name} returned fields {sorted(summary)}, expected {sorted(SUMMARY_FIELDS)}")
    return Triage(
        alert=alert.name,
        fingerprint=alert.fingerprint,
        severity=alert.severity,
        runbook_url=alert.runbook_url,
        sources_missing=missing,
        model=model.name,
        created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **summary,
    )
