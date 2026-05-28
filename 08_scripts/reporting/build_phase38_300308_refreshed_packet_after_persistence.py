#!/usr/bin/env python3
"""Build Phase 38 refreshed 300308 packet after candidate persistence."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parents[0]
VERIFICATION_DIR = Path(__file__).resolve().parents[1] / "verification"
for path in (LIB_DIR, REPORTING_DIR, VERIFICATION_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase38_300308_evidence_chain_refresh import build_payload as build_chain_refresh
from validate_phase38_300308_research_packet_post_persistence import build_payload as build_revalidation
from smr_agents import DB_PATH
from smr_targeted_candidate_inventory import TARGET_TICKER
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection) -> dict[str, Any]:
    refresh = build_chain_refresh(conn).get("evidence_chain_refresh") or {}
    revalidation = build_revalidation(conn).get("research_packet_post_persistence") or {}
    return {
        "generated_at": now_ts(),
        "ticker": TARGET_TICKER,
        "refreshed_packet_after_persistence": {
            "research_quality_before": revalidation.get("research_quality_before"),
            "research_quality_after": revalidation.get("research_quality_after"),
            "new_evidence_written": refresh.get("new_candidates_written", 0),
            "research_quality_delta": revalidation.get("quality_delta"),
            "variables_improved": revalidation.get("variables_improved") or [],
            "still_missing": revalidation.get("still_missing") or [],
            "why_not_pending": {
                "promotion_allowed": False,
                "core_reasons": [
                    "supplier share unconfirmed",
                    "official consensus missing",
                    "customer allocation not confirmed",
                ],
            },
            "promotion_boundary": {
                "promotion_allowed": False,
                "new_pending_created": False,
                "paper_order_created": False,
            },
        },
        "safety": {
            "packet_is_investment_report": False,
            "trade_recommendation_generated": False,
            "target_price_generated": False,
            "position_guidance_generated": False,
            "promotion_rules_relaxed": False,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    packet = payload.get("refreshed_packet_after_persistence") or {}
    why = packet.get("why_not_pending") or {}
    lines = [
        "# Phase 38 300308 Refreshed Packet After Persistence",
        "",
        "## Before / After",
        f"- Research quality before: {packet.get('research_quality_before')}",
        f"- Research quality after: {packet.get('research_quality_after')}",
        f"- New evidence written: {packet.get('new_evidence_written')}",
        f"- Delta: {packet.get('research_quality_delta')}",
        "",
        "## Variables Improved",
    ]
    lines.extend(f"- {item}" for item in packet.get("variables_improved") or [])
    lines.extend(["", "## Still Missing"])
    lines.extend(f"- {item}" for item in packet.get("still_missing") or [])
    lines.extend(["", "## Why Not Pending"])
    lines.append(f"- Promotion allowed: {why.get('promotion_allowed')}")
    lines.extend(f"- {item}" for item in why.get("core_reasons") or [])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 38 refreshed 300308 packet after persistence")
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
