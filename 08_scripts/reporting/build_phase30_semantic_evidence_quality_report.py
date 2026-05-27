#!/usr/bin/env python3
"""Build Phase 30 semantic evidence quality report."""

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
from smr_phase25_utils import resolve_phase25_tickers
from smr_semantic_evidence_persistence import build_semantic_evidence_candidates, flatten_candidates
from smr_semantic_evidence_quality import score_candidates, summarize_quality
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, *, tickers: str | None = None) -> dict:
    resolved = resolve_phase25_tickers(tickers)
    candidate_payload = build_semantic_evidence_candidates(conn, ",".join(resolved), use_real_sources=True, use_text_cache=True, mode="mock")
    candidates = flatten_candidates(candidate_payload)
    assessments = score_candidates(candidates)
    quality_summary = summarize_quality(assessments)
    return {
        "generated_at": now_ts(),
        "summary": {
            "tickers_checked": len(resolved),
            "candidates_total": len(candidates),
            "quality_scored": len(assessments),
            "high_quality": quality_summary["quality_distribution"].get("high_quality", 0),
            "usable": quality_summary["quality_distribution"].get("usable", 0),
            "weak_but_usable": quality_summary["quality_distribution"].get("weak_but_usable", 0),
            "review_required": quality_summary["quality_distribution"].get("review_required", 0),
            "reject": quality_summary["quality_distribution"].get("reject", 0),
        },
        **quality_summary,
        "rows": assessments,
        "safety": {
            "usable_for_promotion_true": 0,
            "semantic_evidence_direct_promotion": False,
        },
    }


def render_markdown(payload: dict) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 30 Semantic Evidence Quality Report",
        "",
        "## Overall",
        f"- Total candidates: {summary.get('candidates_total')}",
        f"- Quality scored: {summary.get('quality_scored')}",
        f"- High quality: {summary.get('high_quality')}",
        f"- Usable: {summary.get('usable')}",
        f"- Weak but usable: {summary.get('weak_but_usable')}",
        f"- Review required: {summary.get('review_required')}",
        f"- Rejected: {summary.get('reject')}",
        "",
        "## Quality Distribution",
        "| Bucket | Count |",
        "|---|---|",
    ]
    for bucket, count in (payload.get("quality_distribution") or {}).items():
        lines.append(f"| {bucket} | {count} |")
    lines.extend(["", "## Candidate Samples", "| Ticker | Variable | Score | Bucket | Recommendation |", "|---|---|---|---|---|"])
    for row in (payload.get("rows") or [])[:20]:
        lines.append(
            f"| {row.get('ticker')} | {row.get('variable_type')} | {row.get('quality_score')} | "
            f"{row.get('quality_bucket')} | {row.get('acceptance_recommendation')} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 30 semantic evidence quality report")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--tickers")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, tickers=args.tickers)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
