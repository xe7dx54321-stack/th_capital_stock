#!/usr/bin/env python3
"""Build Phase 37 refreshed research packet for 300308.SZ."""

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

from validate_phase37_300308_post_acquisition_revalidation import build_payload as build_revalidation
from smr_agents import DB_PATH
from smr_targeted_evidence_candidate_builder import build_targeted_evidence_candidates
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection) -> dict[str, Any]:
    revalidation = build_revalidation(conn)
    body = revalidation.get("post_acquisition_revalidation") or {}
    candidates = build_targeted_evidence_candidates(conn, "300308.SZ", mode="dry_run")
    candidate_rows = (candidates.get("targeted_evidence_candidates") or {}).get("candidate_rows") or []
    return {
        "generated_at": now_ts(),
        "ticker": "300308.SZ",
        "refreshed_research_packet": {
            "research_quality_before": body.get("research_quality_before"),
            "research_quality_after": body.get("research_quality_after"),
            "delta": body.get("research_quality_delta"),
            "new_evidence_added": [row.get("evidence_id") for row in candidate_rows],
            "variables_improved": body.get("variables_improved") or [],
            "still_missing": body.get("still_missing_variables") or [],
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
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    packet = payload.get("refreshed_research_packet") or {}
    why = packet.get("why_not_pending") or {}
    lines = [
        "# Phase 37 300308 Refreshed Research Packet",
        "",
        "## Before / After",
        f"- Research quality before: {packet.get('research_quality_before')}",
        f"- Research quality after: {packet.get('research_quality_after')}",
        f"- Delta: {packet.get('delta')}",
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
    parser = argparse.ArgumentParser(description="Build Phase 37 refreshed 300308 research packet")
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
