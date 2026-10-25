import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def extraction_2003():
    """Datalab balanced extraction of the April 1, 2003 minutes (entry 151897), meta stripped."""
    return json.loads((FIXTURES / "extraction_2003-04-01_151897.json").read_text())
