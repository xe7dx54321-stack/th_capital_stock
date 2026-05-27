#!/usr/bin/env python3
"""Build Phase 30 semantic evidence hardening summary."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
VERIFICATION_DIR = Path(__file__).resolve().parents[1] / "verification"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
if str(VERIFICATION_DIR) not in sys.path:
    sys.path.insert(0, str(VERIFICATION_DIR))

from validate_phase30_post_persistence_audit import build_payload as build_audit_payload
from smr_agents import DB_PATH
from smr_phase25_utils import resolve_phase25_tickers
from smr_semantic_evidence_persistence import build_semantic_evidence_candidates, flatten_candidates, guard_semantic_evidence_candidates
from smr_semantic_evidence_quality import summarize_quality
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, *, tickers: str | None = None) -> dict:
    resolved = resolve_phase25_tickers(tickers)
    candidate_payload = build_semantic_evidence_candidates(conn, ",".join(resolved), use_real_sources=True, use_text_cache=True, mode="mock")
    candidates = flatten_candidates(candidate_payload)
    guarded = guard_semantic_evidence_candidates(candidates, reject_noisy=True)
    quality_summary = summarize_quality(guarded["quality_assessments"])
    audit = build_audit_payload(conn, tickers=",".join(resolved))
    guard_summary = guarded.get("summary") or {}
    audit_summary = audit.get("summary") or {}
    return {
        "generated_at": now_ts(),
        "summary": {
            "tickers_checked": len(resolved),
            "candidates_total": len(candidates),
            "quality_scored": guard_summary.get("quality_scored", 0),
            "eligible_for_persistence": guard_summary.get("eligible_for_persistence", 0),
            "rejected_by_quality": guard_summary.get("rejected_by_quality", 0),
            "rejected_by_noise": guard_summary.get("rejected_by_noise", 0),
            "review_required": guard_summary.get("review_required", 0),
            "persisted_candidates": audit_summary.get("persisted_candidates", 0),
            "variable_packs_updated": audit_summary.get("variable_packs_updated", 0),
            "new_pending_created": 0,
        },
        "quality_distribution": quality_summary.get("quality_distribution") or {},
        "noise_distribution": quality_summary.get("noise_distribution") or {},
        "post_persistence_impact": audit_summary,
        "safety": {
            "usable_for_promotion_true": guard_summary.get("usable_for_promotion_true", 0),
            "semantic_evidence_alone_pending": False,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def render_markdown(payload: dict) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 30 Semantic Evidence Quality & Persistence Hardening Summary",
        "",
        "## Overall",
        f"- Total candidates: {summary.get('candidates_total')}",
        f"- Eligible for persistence: {summary.get('eligible_for_persistence')}",
        f"- Rejected by quality: {summary.get('rejected_by_quality')}",
        f"- Rejected by noise: {summary.get('rejected_by_noise')}",
        f"- Persisted candidates: {summary.get('persisted_candidates')}",
        f"- Variable packs updated: {summary.get('variable_packs_updated')}",
        f"- New pending: {summary.get('new_pending_created')}",
        "",
        "## Quality Distribution",
        "| Bucket | Count |",
        "|---|---|",
    ]
    for bucket, count in (payload.get("quality_distribution") or {}).items():
        lines.append(f"| {bucket} | {count} |")
    lines.extend(["", "## Noise Distribution", "| Noise Type | Count |", "|---|---|"])
    for noise_type, count in (payload.get("noise_distribution") or {}).items():
        lines.append(f"| {noise_type} | {count} |")
    lines.extend(["", "## Post-Persistence Impact", "| Metric | Count |", "|---|---|"])
    for metric, count in (payload.get("post_persistence_impact") or {}).items():
        lines.append(f"| {metric} | {count} |")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 30 semantic evidence hardening summary")
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
