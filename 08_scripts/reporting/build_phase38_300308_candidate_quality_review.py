#!/usr/bin/env python3
"""Build Phase 38 300308 targeted candidate quality review."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_targeted_candidate_inventory import TARGET_TICKER
from smr_targeted_candidate_quality_review import build_targeted_candidate_quality_review

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection) -> dict[str, Any]:
    return build_targeted_candidate_quality_review(conn, TARGET_TICKER)


def _public_row(row: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(row)
    cleaned.pop("calibrated_candidate", None)
    return cleaned


def render_markdown(payload: dict[str, Any]) -> str:
    review = payload.get("candidate_quality_review") or {}
    lines = [
        "# Phase 38 300308 Candidate Quality Review",
        "",
        f"- Candidates reviewed: {review.get('candidates_reviewed')}",
        f"- Eligible for persistence: {review.get('eligible_for_persistence')}",
        f"- Usable for promotion true: {review.get('usable_for_promotion_true')}",
        "",
        "## Quality Rows",
        "| Candidate | Variable | Score | Bucket | Action | Usage | Reasons |",
        "|---|---|---:|---|---|---|---|",
    ]
    for row in review.get("quality_rows") or []:
        lines.append(
            f"| {row.get('candidate_id')} | {row.get('variable')} | {row.get('quality_score')} | "
            f"{row.get('quality_bucket')} | {row.get('recommended_action')} | "
            f"{row.get('allowed_usage_after_review')} | {', '.join(row.get('review_reasons') or [])} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 38 300308 candidate quality review")
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
        public = dict(payload)
        body = dict(public.get("candidate_quality_review") or {})
        body["quality_rows"] = [_public_row(row) for row in body.get("quality_rows") or []]
        public["candidate_quality_review"] = body
        print(json.dumps(public, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
