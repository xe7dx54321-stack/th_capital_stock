#!/usr/bin/env python3
"""Build Phase 16 parser recovery daily summary."""

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

from validate_phase16_parser_thesis_recovery import DEFAULT_TICKERS, build_payload
from smr_agents import DB_PATH
from smr_registry import register_snapshot
from smr_runlog import log_run


SCRIPT_NAME = "build_phase16_parser_recovery_summary.py"


def build_summary_payload(conn: sqlite3.Connection) -> dict:
    recovery = build_payload(conn, DEFAULT_TICKERS)
    hkex = []
    cninfo = []
    unknown = []
    for target in recovery.get("targets") or []:
        if target.get("target_type") == "hkex_balance_sheet_recovery":
            repair = (target.get("field_repair") or {}).get("shareholders_equity") or {}
            hkex.append(
                {
                    "ticker": target.get("ticker"),
                    "field": "shareholders_equity",
                    "before": "missing",
                    "status": repair.get("status"),
                    "after": repair.get("status"),
                    "missing_reason": repair.get("missing_reason"),
                    "confidence": repair.get("confidence"),
                    "remaining": target.get("remaining_blockers") or [],
                }
            )
        elif target.get("target_type") == "cninfo_income_statement_recovery":
            cninfo.append(
                {
                    "ticker": target.get("ticker"),
                    "fields_repaired": target.get("fields_repaired") or [],
                    "fields_refined": target.get("fields_refined") or [],
                    "remaining": target.get("remaining_blockers") or [],
                    "suggested_fix": ", ".join(
                        sorted(
                            {
                                str(status.get("suggested_fix"))
                                for status in (target.get("field_repair") or {}).values()
                                if status.get("suggested_fix")
                            }
                        )
                    ),
                }
            )
        elif target.get("target_type") == "unknown_thesis_recovery":
            unknown.append(
                {
                    "ticker": target.get("ticker"),
                    "status": "improved" if target.get("after_thesis") not in {None, "unknown"} else "still_unknown",
                    "before": target.get("before_thesis"),
                    "candidate_thesis": target.get("after_thesis"),
                    "confidence": target.get("confidence_after"),
                    "still_blocked": not bool(target.get("allow_pending")),
                }
            )
    return {
        "generated_at": recovery.get("generated_at"),
        "summary": {
            "hkex_targets": [item["ticker"] for item in hkex],
            "cninfo_targets": [item["ticker"] for item in cninfo],
            "unknown_thesis_targets": [item["ticker"] for item in unknown],
            **(recovery.get("summary") or {}),
        },
        "hkex_recovery": hkex,
        "cninfo_recovery": cninfo,
        "unknown_thesis": unknown,
    }


def markdown(payload: dict) -> str:
    lines = ["# Phase 16 Parser Recovery Summary", "", "## HKEX Recovery"]
    lines.append("| Ticker | Field | Before | After | Confidence | Remaining |")
    lines.append("|---|---|---|---|---:|---|")
    for item in payload.get("hkex_recovery") or []:
        lines.append(f"| {item.get('ticker')} | {item.get('field')} | {item.get('before')} | {item.get('after')}:{item.get('missing_reason') or '-'} | {item.get('confidence')} | {', '.join(item.get('remaining') or []) or '-'} |")
    lines.extend(["", "## CNINFO Recovery", "| Ticker | Fields Repaired | Remaining Blockers | Suggested Fix |", "|---|---|---|---|"])
    for item in payload.get("cninfo_recovery") or []:
        repaired = ", ".join((item.get("fields_repaired") or []) + [f"refined:{field}" for field in item.get("fields_refined") or []])
        lines.append(f"| {item.get('ticker')} | {repaired or '-'} | {', '.join(item.get('remaining') or []) or '-'} | {item.get('suggested_fix') or '-'} |")
    lines.extend(["", "## Unknown Thesis", "| Ticker | Before | After | Confidence | Still Blocked? |", "|---|---|---|---:|---|"])
    for item in payload.get("unknown_thesis") or []:
        lines.append(f"| {item.get('ticker')} | {item.get('before')} | {item.get('candidate_thesis')} | {item.get('confidence')} | {item.get('still_blocked')} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 16 parser recovery summary")
    parser.add_argument("--db-path", default=str(DB_PATH))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--json", action="store_true")
    mode.add_argument("--markdown", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_summary_payload(conn)
        register_snapshot(
            conn,
            entity_type="phase16_parser_recovery_summary",
            entity_id="latest",
            status="built",
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    print(markdown(payload) if args.markdown else json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase16 parser recovery summary built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
