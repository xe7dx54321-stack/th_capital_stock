#!/usr/bin/env python3
"""Build a daily summary for Phase 6 multi-ticker live validation."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_paths import project_path
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts


SCRIPT_NAME = "build_phase6_daily_live_summary.py"


def loads_json(raw: str | None, fallback: Any) -> Any:
    if raw in (None, ""):
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def load_latest_phase6_validation(conn: sqlite3.Connection) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT payload_json
        FROM task_registry_entry
        WHERE entity_type='phase6_multi_ticker_live_validation'
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """
    ).fetchone()
    if not row:
        return None
    return loads_json(row[0], {})


def bucket_for_result(item: dict[str, Any]) -> str:
    status = str(item.get("status") or "").lower()
    if status == "pending_human_review":
        return "pending_human_review"
    if status == "candidate_shadow":
        return "candidate_shadow"
    if status in {"observation_only", "observation", "watch"}:
        return "observation_only"
    if item.get("summary_bucket") in {"blocked_by_data", "blocked_by_evidence"}:
        return str(item.get("summary_bucket"))
    missing = {str(value) for value in item.get("missing_requirements") or []}
    if any(token in missing for token in {"daily_bar_fresh", "news_health", "relevant_filings_health", "fundamentals_snapshot", "fundamentals_snapshot_fresh_or_explainable"}):
        return "blocked_by_data"
    if any(token.startswith("lint:") or token in {"core_claim_evidence_quality", "two_independent_evidence_sources", "primary_evidence_for_fundamental_claims"} for token in missing):
        return "blocked_by_evidence"
    if item.get("promotion_allowed"):
        return "candidate_shadow"
    return "observation_only"


def summary_lines(rows: list[dict[str, Any]]) -> list[str]:
    lines = []
    for item in rows:
        reasons = item.get("required_fixes") or item.get("minimum_fix_path") or []
        lines.append(
            f"- {item.get('ticker')} -> {item.get('status')} / {item.get('action')} / "
            f"promotion_allowed={item.get('promotion_allowed')} / bucket={item.get('summary_bucket')} / "
            f"fixes={'; '.join(reasons[:3]) or '-'}"
        )
    return lines


def compact_ticker_row(item: dict[str, Any]) -> dict[str, Any]:
    debugger = item.get("promotion_debugger") or {}
    portfolio_risk = item.get("portfolio_risk") or {}
    promotion = item.get("promotion") or {}
    snapshots = promotion.get("snapshots") or {}
    field_gate = item.get("promotion_evidence_gate") or snapshots.get("promotion_evidence_gate") or {}
    data_quality_gate = item.get("data_quality_gate") or snapshots.get("data_quality_gate") or {}
    return {
        "ticker": item.get("ticker"),
        "market": item.get("market"),
        "status": item.get("status"),
        "action": item.get("action"),
        "promotion_allowed": item.get("promotion_allowed"),
        "summary_bucket": item.get("summary_bucket"),
        "live_news_evidence": item.get("live_news_evidence"),
        "live_filing_evidence": item.get("live_filing_evidence"),
        "fundamentals_status": item.get("fundamentals_status"),
        "fundamentals_missing_fields": item.get("fundamentals_missing_fields") or [],
        "valuation_usage": item.get("valuation_usage"),
        "proxy_quality": item.get("proxy_quality"),
        "proxy_independent_source_count": item.get("proxy_independent_source_count"),
        "bear_case_strength": item.get("bear_case_strength"),
        "portfolio_risk": {
            "status": portfolio_risk.get("status"),
            "recommended_action": portfolio_risk.get("recommended_action"),
            "recommended_position_pct": portfolio_risk.get("recommended_position_pct"),
            "blocking_factors": portfolio_risk.get("blocking_factors") or [],
        },
        "ledger_written": item.get("ledger_written"),
        "review_queue_visible": item.get("review_queue_visible"),
        "missing_requirements": item.get("missing_requirements") or [],
        "required_fixes": item.get("required_fixes") or [],
        "minimum_fix_path": debugger.get("minimum_fix_path") or item.get("minimum_fix_path") or [],
        "core_blocker_count": len(field_gate.get("core_blockers") or []),
        "non_core_warning_count": len(field_gate.get("supporting_warnings") or []) + len(field_gate.get("optional_warnings") or []),
        "promotion_mode": snapshots.get("promotion_mode") or item.get("promotion_mode"),
        "position_policy": snapshots.get("position_policy") or item.get("position_policy"),
        "data_quality_gate_status": data_quality_gate.get("status") or data_quality_gate.get("after_status"),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 6 Daily Live Summary",
        "",
        f"- generated_at: `{payload.get('generated_at')}`",
        f"- watchlist: `{payload.get('watchlist_id')}`",
        f"- overall_result: `{payload.get('overall_result')}`",
        f"- core_blocker_count: `{payload.get('core_blocker_count') or 0}`",
        f"- non_core_warning_count: `{payload.get('non_core_warning_count') or 0}`",
        f"- reduced_size_pending_candidates: `{', '.join(payload.get('reduced_size_pending_candidates') or []) or '-'}`",
        "",
        "## Status Counts",
        "",
    ]
    for key, value in (payload.get("status_counts") or {}).items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Ticker Reasons", ""])
    for line in payload.get("summary_lines") or []:
        lines.append(line)
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Phase 6 daily live summary")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--watchlist", default="ai_core")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db_path)
    try:
        validation = load_latest_phase6_validation(conn)
        if not validation:
            payload = {
                "generated_at": now_ts(),
                "watchlist_id": args.watchlist,
                "overall_result": "skipped",
                "skip_reason": "no phase6_multi_ticker_live_validation snapshot found",
                "status_counts": {},
                "summary_lines": [],
            }
        else:
            rows = []
            for item in validation.get("tickers") or []:
                row = dict(item)
                row["summary_bucket"] = bucket_for_result(row)
                rows.append(row)
            counts = Counter(row["summary_bucket"] for row in rows)
            compact_rows = [compact_ticker_row(row) for row in rows]
            payload = {
                "generated_at": now_ts(),
                "watchlist_id": validation.get("watchlist_id") or args.watchlist,
                "overall_result": validation.get("summary", {}).get("overall_result") or "partial_pass",
                "watchlist_meta": validation.get("watchlist_meta") or {},
                "status_counts": dict(counts),
                "summary_lines": summary_lines(rows),
                "core_blocker_count": sum(int(row.get("core_blocker_count") or 0) for row in compact_rows),
                "non_core_warning_count": sum(int(row.get("non_core_warning_count") or 0) for row in compact_rows),
                "reduced_size_pending_candidates": [
                    row.get("ticker")
                    for row in compact_rows
                    if row.get("status") == "pending_human_review" and row.get("promotion_mode") == "reduced_size_pending"
                ],
                "still_blocked_by_core_fields": [
                    row.get("ticker")
                    for row in compact_rows
                    if int(row.get("core_blocker_count") or 0) > 0
                ],
                "tickers": compact_rows,
            }
        output_dir = project_path("06_reports", "adhoc", "phase6")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{payload['generated_at'][:10]}_phase6_daily_live_summary.md"
        output_path.write_text(render_markdown(payload), encoding="utf-8")
        register_snapshot(
            conn,
            entity_type="phase6_daily_live_summary",
            entity_id=payload["generated_at"][:10],
            status=str(payload.get("overall_result") or "skipped"),
            source=SCRIPT_NAME,
            payload={**payload, "summary_rel_path": str(output_path)},
        )
        conn.commit()
    finally:
        conn.close()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase6 daily live summary built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
