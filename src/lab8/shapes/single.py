"""Shape B — one ReAct agent. Student work.

Use `lab8.runtime.run_react` with max_steps=8. `decide` may pick a read tool.
It must not call `issue_refund`. After the loop, the host validates the quote
and is the only writer.

A decide() that trusts ticket text over the order row will fail hidden claims
where the customer overstates the delay or cites a superseded clause.

Per-order cap: an order may already have been refunded by an earlier claim.
The read tool `lookup_refund_history` shows how much. The host still enforces
the cap, so pass the full quote to `durability.issue_refund`, not a net amount.

Caps: stop at 8 steps. Count model calls in the Budget so cost stays comparable.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

from typing import Any

from lab8.db import connect
from lab8.durability import issue_refund
from lab8.mock_llm import complete
from lab8.runtime import run_react
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
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
        trace = Trace(make_run_id("single", claim_id, seed))
        trace.add("agent", {"mode": "bounded_read_only_react", "max_steps": 8})

        def decide(observation: dict[str, Any]) -> dict[str, Any]:
            # MockLLM has no structured tool-call API; the controller constrains
            # every turn to the next safe read action based on tool observations.
            complete(
                budget,
                seed=seed,
                purpose="single_decide",
                prompt=f"step={budget.model_calls + 1};last_tool={observation.get('last_tool', 'start')}",
            )
            last_tool = observation.get("last_tool")
            if last_tool is None:
                action = {"tool": "get_claim_view", "args": {"claim_id": claim_id}}
            elif last_tool == "get_claim_view":
                claim = observation["last_result"]
                if not claim["found"]:
                    return {"final": {"status": "failed", "error_reason": "unknown_claim", "proposal_amount": 0}}
                if not claim.get("order_id"):
                    return {"final": {"status": "needs_info", "error_reason": "missing_order_id", "proposal_amount": 0}}
                action = {
                    "tool": "lookup_order",
                    "args": {"order_id": claim["order_id"], "principal_id": claim["principal_id"]},
                }
            elif last_tool == "lookup_order":
                order_view = observation["last_result"]
                if not order_view["visible"]:
                    return {
                        "final": {
                            "status": "escalated",
                            "error_reason": order_view["reason"],
                            "proposal_amount": 0,
                        }
                    }
                action = {"tool": "compute_compensation", "args": {"order": order_view["order"]}}
            elif last_tool == "compute_compensation":
                quote = observation["last_result"]
                amount = int(quote["amount_vnd"])
                return {
                    "final": {
                        "status": "denied" if amount <= 0 else "quoted",
                        "error_reason": quote["reason"] if amount <= 0 else None,
                        "proposal_amount": amount,
                        "quote": quote,
                    }
                }
            else:
                return {"final": {"status": "failed", "error_reason": "unexpected_tool_state", "proposal_amount": 0}}
            trace.add("tool_selection", {"tool": action["tool"]})
            return action

        outcome = run_react(
            conn,
            budget,
            observation={"claim": {"claim_id": claim_id}},
            decide=decide,
            max_steps=8,
        )
        final = outcome["final"]
        status = final["status"]
        proposal = int(final.get("proposal_amount", 0))
        trace.add("react", {"stopped": outcome["stopped"], "status": status})
        if final.get("quote") is not None:
            quote = final["quote"]
            trace.add("quote", {
                "amount_vnd": proposal,
                "reason": quote["reason"],
                "clause_ids": quote["clause_ids"],
            })
        if proposal <= 0:
            return finish(
                conn, shape="single", claim_id=claim_id, seed=seed,
                status=status, proposal_amount=0, budget=budget, trace=trace,
                error_reason=final.get("error_reason"),
            )

        trace.add("host_call", {"operation": "issue_refund", "proposal_amount": proposal})
        trace.write()
        result = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
        if not result["ok"]:
            status = "failed" if result["conflict"] else "denied"
            return finish(
                conn, shape="single", claim_id=claim_id, seed=seed,
                status=status, proposal_amount=proposal, budget=budget, trace=trace,
                error_reason=result["reason"],
            )
        return finish(
            conn, shape="single", claim_id=claim_id, seed=seed,
            status="resolved", proposal_amount=proposal, budget=budget, trace=trace,
        )
    finally:
        conn.close()
