#!/usr/bin/env python3
"""Build Phase 39 next evidence priority update."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_evidence_contribution_analyzer import build_evidence_contribution
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str) -> dict:
    improved = build_evidence_contribution(conn, ticker).get("evidence_contribution", {}).get("variables_strengthened") or []
    lower_priority = [item for item in ("product_mix", "shipment", "order_visibility") if item in improved]
    return {
        "generated_at": now_ts(),
        "ticker": str(ticker or "").strip().upper(),
        "next_evidence_priority_update": {
            "completed_or_improved": improved,
            "remaining_high_priority": [
                {
                    "variable": "supplier_share",
                    "priority": "high_but_low_public_availability",
                    "recommended_mode": "scenario_analysis_only",
                    "do_not_do": [
                        "do not fabricate exact share",
                        "do not infer share from generic demand",
                    ],
                },
                {
                    "variable": "official_consensus",
                    "priority": "high",
                    "recommended_mode": "authorized_source_required",
                    "do_not_do": [
                        "do not treat internal proxy as official consensus",
                    ],
                },
                {
                    "variable": "confirmed_customer_allocation",
                    "priority": "high",
                    "recommended_mode": "customer-side public signal or company direct disclosure",
                    "do_not_do": [
                        "do not convert customer proxy into confirmed allocation",
                    ],
                },
            ],
            "lower_priority_after_phase38": lower_priority,
        },
        "safety": {
            "new_pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
            "supplier_share_public_availability_caveat": True,
            "official_consensus_requires_authorized_source": True,
        },
    }


def render_markdown(payload: dict) -> str:
    body = payload.get("next_evidence_priority_update") or {}
    lines = [
        f"# Phase 39 Next Evidence Priority Update: {payload.get('ticker')}",
        "",
        "## Completed Or Improved",
    ]
    lines.extend(f"- {item}" for item in body.get("completed_or_improved") or [])
    lines.extend(["", "## Remaining High Priority"])
    for item in body.get("remaining_high_priority") or []:
        lines.append(f"- {item.get('variable')}: {item.get('priority')} / {item.get('recommended_mode')}")
    lines.extend(["", "## Lower Priority After Phase 38"])
    lines.extend(f"- {item}" for item in body.get("lower_priority_after_phase38") or [])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 39 next evidence priority update")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", default="300308.SZ")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, args.ticker)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
