#!/usr/bin/env python3
"""Build Phase 39 evidence-strengthened research packet for 300308.SZ."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parents[0]
VERIFICATION_DIR = Path(__file__).resolve().parents[1] / "verification"
for path in (LIB_DIR, REPORTING_DIR, VERIFICATION_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase38_300308_evidence_chain_refresh import build_payload as build_chain_refresh
from build_phase39_300308_evidence_contribution import build_payload as build_contribution
from validate_phase38_300308_research_packet_post_persistence import build_payload as build_revalidation
from smr_agents import DB_PATH
from smr_targeted_candidate_inventory import TARGET_TICKER
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _point(variable: str) -> str:
    return f"{variable} evidence strengthened"


def build_payload(conn: sqlite3.Connection) -> dict:
    refresh = build_chain_refresh(conn).get("evidence_chain_refresh") or {}
    revalidation = build_revalidation(conn).get("research_packet_post_persistence") or {}
    contribution = build_contribution(conn).get("evidence_contribution") or {}
    variables = contribution.get("variables_strengthened") or []
    return {
        "generated_at": now_ts(),
        "ticker": TARGET_TICKER,
        "evidence_strengthened_packet": {
            "research_quality_before": revalidation.get("research_quality_before") or "medium_low",
            "research_quality_after": revalidation.get("research_quality_after") or "medium_low",
            "quality_delta": revalidation.get("quality_delta") or "strengthened_with_new_supporting_evidence",
            "evidence_before": refresh.get("evidence_before", 0),
            "evidence_after": refresh.get("evidence_after", 0),
            "new_evidence_written": refresh.get("new_candidates_written", 0),
            "thesis_update": {
                "before": "AI optical interconnect exposure is plausible but needs more evidence.",
                "after": (
                    "AI optical interconnect exposure is better supported by product mix, order visibility "
                    "and shipment-related evidence, but key commercialization variables remain missing."
                ),
            },
            "strengthened_points": [_point(variable) for variable in variables],
            "new_evidence_added": refresh.get("new_evidence_ids") or [],
            "remaining_uncertainties": [
                "supplier share unconfirmed",
                "official consensus missing",
                "confirmed customer allocation missing",
            ],
            "why_not_pending": {
                "promotion_allowed": False,
                "core_reasons": [
                    "supplier share unconfirmed",
                    "official consensus missing",
                    "confirmed customer allocation missing",
                ],
            },
            "next_evidence_priority": ["supplier_share", "official_consensus", "confirmed_customer_allocation"],
            "promotion_boundary": {
                "promotion_allowed": False,
                "new_pending_created": False,
                "paper_order_created": False,
                "reason": "research packet strengthened, but investment gate remains blocked by missing key variables",
            },
        },
        "safety": {
            "packet_is_investment_memo": False,
            "trade_recommendation_generated": False,
            "target_price_generated": False,
            "position_guidance_generated": False,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def render_markdown(payload: dict) -> str:
    packet = payload.get("evidence_strengthened_packet") or {}
    lines = [
        "# Phase 39 Evidence-Strengthened Research Packet: 300308.SZ",
        "",
        "## What Changed",
        f"- Quality delta: {packet.get('quality_delta')}",
        f"- Evidence before: {packet.get('evidence_before')}",
        f"- Evidence after: {packet.get('evidence_after')}",
        "",
        "## New Evidence Added",
    ]
    lines.extend(f"- {item}" for item in packet.get("new_evidence_added") or [])
    lines.extend(["", "## Strengthened Research Points"])
    lines.extend(f"- {item}" for item in packet.get("strengthened_points") or [])
    lines.extend(["", "## Still Missing"])
    lines.extend(f"- {item}" for item in packet.get("remaining_uncertainties") or [])
    lines.extend(["", "## Updated Thesis"])
    thesis = packet.get("thesis_update") or {}
    lines.append(f"- Before: {thesis.get('before')}")
    lines.append(f"- After: {thesis.get('after')}")
    lines.extend(["", "## Why Not Pending"])
    lines.extend(f"- {item}" for item in (packet.get("why_not_pending") or {}).get("core_reasons") or [])
    lines.extend(["", "## Next Evidence Priority"])
    lines.extend(f"- {item}" for item in packet.get("next_evidence_priority") or [])
    lines.extend(["", "## Promotion Boundary"])
    boundary = packet.get("promotion_boundary") or {}
    lines.append(f"- Promotion allowed: {boundary.get('promotion_allowed')}")
    lines.append(f"- Reason: {boundary.get('reason')}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 39 300308 evidence-strengthened packet")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
