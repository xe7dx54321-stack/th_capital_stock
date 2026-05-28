#!/usr/bin/env python3
"""Build Phase 45 final research asset summary."""

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
from smr_final_research_asset_aggregator import build_final_research_asset_summary
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str = TARGET_REVIEW_TICKER) -> dict:
    return build_final_research_asset_summary(conn, ticker)


def render_markdown(payload: dict) -> str:
    body = payload.get("final_research_asset_summary") or {}
    chain = body.get("evidence_chain") or {}
    lines = [f"# Phase 45 Final Research Asset Summary: {payload.get('ticker')}", ""]
    lines.extend(["## Completed Stages"])
    lines.extend(f"- {stage}" for stage in body.get("research_asset_stages_completed") or [])
    lines.extend(["", "## Evidence Chain"])
    for key in ("evidence_before_targeted_execution", "evidence_after_persistence", "manual_candidates_reviewed"):
        lines.append(f"- {key}: {chain.get(key)}")
    lines.extend(["", "## Strengthened Variables"])
    lines.extend(f"- {item}" for item in body.get("strengthened_variables") or [])
    lines.extend(["", "## Manual Candidate Results"])
    for key, value in (body.get("manual_candidate_results") or {}).items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Remaining Core Gaps"])
    lines.extend(f"- {item}" for item in body.get("remaining_core_gaps") or [])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 45 final research asset summary")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", default=TARGET_REVIEW_TICKER)
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
