import lab8.shapes.swarm_reference as swarm_reference
from lab8.db import init_store
from lab8.shapes.swarm_reference import run_claim
from tests.conftest import CLAIMS, WORLD


def test_disabling_ticket_delay_override_fixes_seed_55_claim(tmp_path, monkeypatch):
    baseline_store = tmp_path / "baseline.sqlite"
    init_store(baseline_store, WORLD, CLAIMS).close()
    baseline = run_claim("C-002", seed=55, store_path=str(baseline_store))

    monkeypatch.setattr(swarm_reference, "parse_delay_days", lambda _ticket: None)
    verified_store = tmp_path / "verified.sqlite"
    init_store(verified_store, WORLD, CLAIMS).close()
    verified = run_claim("C-002", seed=55, store_path=str(verified_store))

    assert (baseline.status, baseline.proposal_amount) == ("resolved", 20000)
    assert (verified.status, verified.proposal_amount) == ("denied", 0)
    assert verified.refund_effects == []
    assert baseline.model_calls == verified.model_calls
    assert baseline.tool_calls == verified.tool_calls + 1
    assert baseline.cost_estimate > verified.cost_estimate
