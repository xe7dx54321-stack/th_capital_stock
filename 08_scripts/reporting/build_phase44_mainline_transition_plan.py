#!/usr/bin/env python3
"""Build Phase 44 mainline transition plan."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload() -> dict:
    return {
        "generated_at": now_ts(),
        "mainline_transition_plan": {
            "current_branch": "manual_intake_governance",
            "branch_status": "closed_after_phase44",
            "next_phase": "phase45_final_research_packet_review",
            "rationale": [
                "manual candidates reviewed",
                "allowed usage finalized",
                "audit written",
                "research impact revalidated",
            ],
            "do_not_continue_with": [
                "more manual candidate governance phases",
                "more dashboard-only phases",
                "more lifecycle-only phases",
            ],
            "phase45_goal": (
                "Evaluate whether 300308.SZ has enough evidence for a formal research conclusion "
                "and paper watchlist consideration, still not automatic pending."
            ),
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_allowed_true": 0,
        },
        "safety": {
            "branch_closed": True,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def render_markdown(payload: dict) -> str:
    body = payload.get("mainline_transition_plan") or {}
    lines = ["# Phase 44 Mainline Transition Plan", "", "## Summary"]
    for key in ("current_branch", "branch_status", "next_phase", "phase45_goal"):
        lines.append(f"- {key}: {body.get(key)}")
    lines.extend(["", "## Rationale"])
    lines.extend(f"- {item}" for item in body.get("rationale") or [])
    lines.extend(["", "## Do Not Continue With"])
    lines.extend(f"- {item}" for item in body.get("do_not_continue_with") or [])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 44 mainline transition plan")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    payload = build_payload()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
