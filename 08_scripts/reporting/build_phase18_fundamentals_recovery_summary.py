#!/usr/bin/env python3
"""Build Phase 18 fundamentals recovery summary."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
VERIFICATION_DIR = Path(__file__).resolve().parents[1] / "verification"
for path in (LIB_DIR, VERIFICATION_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from validate_phase18_fundamentals_recovery_revalidation import build_payload
from smr_agents import DB_PATH
from smr_runlog import log_run

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def compact_summary(payload: dict) -> dict:
    recovered_fields = []
    remaining_core_blockers = {}
    remaining_source_gaps = []
    next_actions = []
    update_results = ((payload.get("fundamentals_update") or {}).get("results") or [])
    update_by_ticker = {item.get("ticker"): item for item in update_results}
    for row in payload.get("ticker_results") or []:
        ticker = row.get("ticker")
        update = (update_by_ticker.get(ticker) or {}).get("fundamentals_snapshot_update") or {}
        for field in update.get("fields_updated") or []:
            recovered_fields.append(
                {
                    "ticker": ticker,
                    "field": field.get("field"),
                    "status": field.get("status"),
                    "source_evidence_id": field.get("source_evidence_id"),
                    "input_evidence_ids": field.get("input_evidence_ids") or [],
                    "allowed_usage": field.get("allowed_usage"),
                }
            )
        if row.get("core_blockers_after"):
            remaining_core_blockers[ticker] = row.get("core_blockers_after")
        if row.get("source_status") == "source_missing":
            remaining_source_gaps.append(ticker)
            next_actions.append({"ticker": ticker, "action": "resolve_cninfo_source_identity_or_add_manifest_entry"})
    summary = payload.get("summary") or {}
    return {
        "generated_at": payload.get("generated_at"),
        "summary": {
            "source_gaps_closed": summary.get("source_gaps_closed"),
            "fields_recovered": summary.get("fields_recovered"),
            "snapshots_updated": summary.get("fundamentals_snapshots_updated"),
            "core_blockers_reduced": summary.get("core_blockers_reduced"),
            "remaining_source_gaps": remaining_source_gaps,
            "remaining_core_blockers": remaining_core_blockers,
            "new_pending_created": summary.get("new_pending_created"),
        },
        "recovered_fields": recovered_fields,
        "ticker_results": payload.get("ticker_results") or [],
        "next_actions": next_actions,
    }


def to_markdown(payload: dict) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 18 Fundamentals Recovery Summary",
        "",
        "## Overall",
        f"- Source gaps closed: {summary.get('source_gaps_closed')}",
        f"- Fields recovered: {summary.get('fields_recovered')}",
        f"- Fundamentals snapshots updated: {summary.get('snapshots_updated')}",
        f"- Core blockers reduced: {summary.get('core_blockers_reduced')}",
        "",
        "## Recovered Fields",
        "| Ticker | Field | Status | Evidence | Usage |",
        "|---|---|---|---|---|",
    ]
    for field in payload.get("recovered_fields") or []:
        evidence = field.get("source_evidence_id") or ",".join(field.get("input_evidence_ids") or []) or "-"
        lines.append(f"| {field.get('ticker')} | {field.get('field')} | {field.get('status')} | {evidence} | {field.get('allowed_usage')} |")
    lines.extend(["", "## Remaining Gaps", "| Ticker | Gap | Suggested Fix |", "|---|---|---|"])
    for ticker in summary.get("remaining_source_gaps") or []:
        lines.append(f"| {ticker} | source_identity_or_manifest | resolve CNINFO identity/source manifest |")
    for ticker, blockers in (summary.get("remaining_core_blockers") or {}).items():
        lines.append(f"| {ticker} | {', '.join(blockers)} | recover field evidence or keep blocked |")
    lines.extend(["", "## Promotion Impact", "| Ticker | Before | After | Remaining Reason |", "|---|---|---|---|"])
    for row in payload.get("ticker_results") or []:
        lines.append(
            f"| {row.get('ticker')} | {', '.join(row.get('core_blockers_before') or []) or '-'} | "
            f"{', '.join(row.get('core_blockers_after') or []) or '-'} | {row.get('remaining_reason')} |"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 18 fundamentals recovery summary")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    parser.add_argument("--no-live", action="store_true")
    args = parser.parse_args()
    payload = compact_summary(build_payload(args.db_path, ["00700.HK", "300308.SZ", "688041.SH"], live=not args.no_live))
    if args.markdown:
        print(to_markdown(payload))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run("build_phase18_fundamentals_recovery_summary.py", "success", "phase18 fundamentals recovery summary built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
