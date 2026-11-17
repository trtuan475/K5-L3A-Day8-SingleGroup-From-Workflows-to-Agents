import json
from pathlib import Path

import pytest

from lab8.db import init_store
from lab8.metrics import artifact_blob
from lab8.shapes import SHAPES
from tests.conftest import BY_ID, CLAIMS, WORLD


@pytest.mark.parametrize("shape", ["workflow", "single", "orchestrator"])
def test_student_shape_trace_omits_claim_secrets(tmp_path, shape):
    store = tmp_path / f"{shape}.sqlite"
    init_store(store, WORLD, CLAIMS).close()

    result = SHAPES[shape]("C-010", seed=11, store_path=str(store))
    trace = json.loads(Path(result.trace_path).read_text(encoding="utf-8"))
    artifacts = artifact_blob(result.as_dict())

    assert trace["run_id"] == result.run_id
    assert isinstance(trace["events"], list)
    for forbidden in BY_ID["C-010"]["expected"]["forbid_substrings"]:
        assert forbidden not in artifacts
