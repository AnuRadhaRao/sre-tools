import pytest

from triage_agent.alerts import parse_alertmanager
from triage_agent.model import StubModel
from triage_agent.triage import triage


@pytest.fixture
def alert(alert_payload):
    return parse_alertmanager(alert_payload)[0]


def test_stub_triage_uses_context(alert):
    sources = {
        "logs": lambda a: {"top_errors": ["TimeoutError: db pool exhausted", "HTTP 502 from payments"]},
        "tickets": lambda a: {"tickets": ["CUST-1", "CUST-2"]},
        "runbook": lambda a: {"runbook_steps": ["Check db pool size", "Restart checkout"]},
    }
    result = triage(alert, StubModel(), sources)
    assert result.likely_cause == "TimeoutError: db pool exhausted"
    assert result.impact.startswith("2 related customer ticket(s)")
    assert result.runbook_steps == ["Check db pool size", "Restart checkout"]
    assert result.sources_missing == []


def test_failing_source_is_reported_not_fatal(alert):
    def broken(_):
        raise ConnectionError("chat is down")

    result = triage(alert, StubModel(), {"chat": broken})
    assert result.sources_missing == ["chat"]
    assert result.likely_cause == alert.description


def test_rejects_model_output_with_wrong_fields(alert):
    class BadModel:
        name = "bad"

        def summarize(self, alert, context):
            return {"impact": "?"}

    with pytest.raises(ValueError, match="expected"):
        triage(alert, BadModel())
