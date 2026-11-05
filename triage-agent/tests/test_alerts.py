import pytest

from triage_agent.alerts import parse_alertmanager


def test_parses_example(alert_payload):
    [alert] = parse_alertmanager(alert_payload)
    assert alert.name == "CheckoutHigh5xxRate"
    assert alert.severity == "critical"
    assert alert.runbook_url == "http://runbooks/checkout-5xx.md"


def test_defaults_when_annotations_missing():
    [alert] = parse_alertmanager({"alerts": [{"labels": {"alertname": "X"}}]})
    assert alert.severity == "unknown" and alert.runbook_url is None and alert.status == "firing"


@pytest.mark.parametrize("bad", [None, {}, {"alerts": "nope"}, {"alerts": [{"labels": {}}]}])
def test_rejects_non_alertmanager_bodies(bad):
    with pytest.raises(ValueError):
        parse_alertmanager(bad)
