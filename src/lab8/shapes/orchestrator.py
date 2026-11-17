"""Shape C — orchestrator plus read-only investigators. Student work.

1. Build a handoff with `lab8.handoff.make_handoff`. Allowed tools are read-only.
   Never put parent_secret, raw headers, or the full claim row into facts.
2. `lab8.runtime.run_readonly_investigators` runs those tools.
3. The orchestrator quotes from the investigator's order view and calls
   `durability.issue_refund`. Investigators have no write registry.
   Pass the full quote; the host subtracts earlier refunds on the same order.
   `lookup_refund_history` is a read-only tool you may hand to an investigator.
4. Trace the sanitized handoff, not the parent context.

An LLM summary of the parent context is not a sanitizer. Use the allowlist.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

from lab8.db import connect
from lab8.durability import issue_refund
from lab8.handoff import make_handoff
from lab8.runtime import run_readonly_investigators
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish, safe_dump
from lab8.tools import get_claim_view, tool_cost
from lab8.trace import Trace


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        budget = Budget()
        trace = Trace(make_run_id("orchestrator", claim_id, seed))
        budget.add_tool(tool_cost())
        claim = get_claim_view(conn, claim_id)
        trace.add("claim", {"found": claim["found"], "claim_id": claim_id})
        if not claim["found"]:
            return finish(
                conn, shape="orchestrator", claim_id=claim_id, seed=seed,
                status="failed", proposal_amount=0, budget=budget, trace=trace,
                error_reason="unknown_claim",
            )
        if not claim.get("order_id"):
            return finish(
                conn, shape="orchestrator", claim_id=claim_id, seed=seed,
                status="needs_info", proposal_amount=0, budget=budget, trace=trace,
                error_reason="missing_order_id",
            )

        handoff = make_handoff(
            request_id=f"REQ-{claim_id}",
            claim_id=claim_id,
            task="verify_order_and_compute_entitlement",
            facts={},
            allowed_tools=["lookup_order", "lookup_policy", "lookup_refund_history", "compute_compensation"],
        )
        trace.add("handoff", safe_dump(handoff))
        investigated = run_readonly_investigators(
            conn, budget, handoff, principal_id=claim["principal_id"]
        )
        tools = investigated["tools"]
        order_view = tools.get("lookup_order", {})
        trace.add("investigation", {
            "claim_view": investigated["claim_view"],
            "order_visible": bool(order_view.get("visible")),
            "order_reason": order_view.get("reason"),
            "policy_count": len((tools.get("lookup_policy") or {}).get("policies") or []),
            "refund_history": tools.get("lookup_refund_history"),
        })
        if not order_view.get("visible"):
            return finish(
                conn, shape="orchestrator", claim_id=claim_id, seed=seed,
                status="escalated", proposal_amount=0, budget=budget, trace=trace,
                error_reason=order_view.get("reason", "not_found"),
            )

        quote = tools.get("compute_compensation")
        if quote is None:
            return finish(
                conn, shape="orchestrator", claim_id=claim_id, seed=seed,
                status="failed", proposal_amount=0, budget=budget, trace=trace,
                error_reason="investigator_missing_quote",
            )
        proposal = int(quote["amount_vnd"])
        trace.add("quote", {
            "amount_vnd": proposal,
            "reason": quote["reason"],
            "clause_ids": quote["clause_ids"],
        })
        if proposal <= 0:
            return finish(
                conn, shape="orchestrator", claim_id=claim_id, seed=seed,
                status="denied", proposal_amount=0, budget=budget, trace=trace,
                error_reason=quote["reason"],
            )

        trace.add("host_call", {"operation": "issue_refund", "proposal_amount": proposal})
        trace.write()
        outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
        if not outcome["ok"]:
            status = "failed" if outcome["conflict"] else "denied"
            return finish(
                conn, shape="orchestrator", claim_id=claim_id, seed=seed,
                status=status, proposal_amount=proposal, budget=budget, trace=trace,
                error_reason=outcome["reason"],
            )
        return finish(
            conn, shape="orchestrator", claim_id=claim_id, seed=seed,
            status="resolved", proposal_amount=proposal, budget=budget, trace=trace,
        )
    finally:
        conn.close()
