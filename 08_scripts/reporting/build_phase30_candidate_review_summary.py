#!/usr/bin/env python3
"""Build Phase 30 semantic evidence candidate review summary."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_phase25_utils import resolve_phase25_tickers
from smr_semantic_evidence_persistence import build_semantic_evidence_candidates, flatten_candidates
from smr_semantic_evidence_quality import score_candidates
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _preview(text: str | None, limit: int = 60) -> str:
    normalized = " ".join(str(text or "").split())
    return normalized[:limit] + ("..." if len(normalized) > limit else "")


def build_payload(conn: sqlite3.Connection, *, tickers: str | None = None) -> dict:
    resolved = resolve_phase25_tickers(tickers)
    candidate_payload = build_semantic_evidence_candidates(conn, ",".join(resolved), use_real_sources=True, use_text_cache=True, mode="mock")
    candidates = flatten_candidates(candidate_payload)
    assessments = {item.get("evidence_id"): item for item in score_candidates(candidates)}
    rows = []
    reject_reasons = Counter()
    for candidate in candidates:
        quality = assessments.get(candidate.get("evidence_id")) or {}
        noise = quality.get("noise") or {}
        if quality.get("acceptance_recommendation") == "reject":
            reject_reasons.update(noise.get("noise_types") or quality.get("reasons") or ["quality_below_threshold"])
        rows.append(
            {
                "ticker": candidate.get("ticker"),
                "evidence_id": candidate.get("evidence_id"),
                "variable_type": candidate.get("variable_type"),
                "quality_score": quality.get("quality_score"),
                "quality_bucket": quality.get("quality_bucket"),
                "recommendation": quality.get("acceptance_recommendation"),
                "quoted_span_preview": _preview(candidate.get("quoted_span")),
                "limitations": quality.get("limitations") or [],
            }
        )
    recommendation_counts = Counter(row.get("recommendation") for row in rows)
    bucket_counts = Counter(row.get("quality_bucket") for row in rows)
    return {
        "generated_at": now_ts(),
        "summary": {
            "candidates_total": len(rows),
            "persist_candidate": recommendation_counts.get("persist_candidate", 0),
            "review_required": recommendation_counts.get("review_required", 0),
            "reject": recommendation_counts.get("reject", 0),
            "high_quality": bucket_counts.get("high_quality", 0),
            "usable": bucket_counts.get("usable", 0),
            "weak_but_usable": bucket_counts.get("weak_but_usable", 0),
            "top_reject_reasons": [reason for reason, _ in reject_reasons.most_common(5)],
        },
        "rows": rows,
    }


def render_markdown(payload: dict) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 30 Semantic Evidence Candidate Review Summary",
        "",
        "## Overall",
        f"- Total candidates: {summary.get('candidates_total')}",
        f"- Persist candidate: {summary.get('persist_candidate')}",
        f"- Review required: {summary.get('review_required')}",
        f"- Rejected: {summary.get('reject')}",
        f"- High quality: {summary.get('high_quality')}",
        f"- Usable: {summary.get('usable')}",
        f"- Weak but usable: {summary.get('weak_but_usable')}",
        "",
        "## Top Reject Reasons",
        "| Reason | Count |",
        "|---|---|",
    ]
    reason_counts = Counter()
    for reason in summary.get("top_reject_reasons") or []:
        reason_counts[reason] += 1
    for reason, count in reason_counts.items():
        lines.append(f"| {reason} | {count} |")
    lines.extend(["", "## Candidate Samples", "| Ticker | Variable | Score | Recommendation | Quoted Span | Limitation |", "|---|---|---|---|---|---|"])
    for row in (payload.get("rows") or [])[:20]:
        lines.append(
            f"| {row.get('ticker')} | {row.get('variable_type')} | {row.get('quality_score')} | {row.get('recommendation')} | "
            f"{row.get('quoted_span_preview')} | {'; '.join(row.get('limitations') or [])} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 30 candidate review summary")
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
