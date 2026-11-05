from dataclasses import dataclass, field


@dataclass(frozen=True)
class Alert:
    name: str
    status: str
    severity: str
    summary: str
    description: str
    runbook_url: str | None
    starts_at: str
    fingerprint: str
    labels: dict = field(default_factory=dict)


def parse_alertmanager(payload: dict) -> list[Alert]:
    """Turn an Alertmanager webhook body (version 4) into alerts. Raises ValueError if it isn't one."""
    if not isinstance(payload, dict) or not isinstance(payload.get("alerts"), list):
        raise ValueError("expected an Alertmanager webhook body with an 'alerts' list")

    alerts = []
    for raw in payload["alerts"]:
        labels = raw.get("labels", {})
        annotations = raw.get("annotations", {})
        if "alertname" not in labels:
            raise ValueError("alert is missing labels.alertname")
        alerts.append(
            Alert(
                name=labels["alertname"],
                status=raw.get("status", payload.get("status", "firing")),
                severity=labels.get("severity", "unknown"),
                summary=annotations.get("summary", ""),
                description=annotations.get("description", ""),
                runbook_url=annotations.get("runbook_url"),
                starts_at=raw.get("startsAt", ""),
                fingerprint=raw.get("fingerprint", ""),
                labels=labels,
            )
        )
    return alerts
