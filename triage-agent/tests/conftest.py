import json
from pathlib import Path

import pytest


@pytest.fixture
def alert_payload():
    return json.loads((Path(__file__).parent.parent / "examples" / "alert.json").read_text())
