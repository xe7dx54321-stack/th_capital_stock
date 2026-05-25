#!/usr/bin/env python3
"""Dry-run or apply Phase 16 watchlist metadata patches."""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parents[1] / "reporting"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
if str(REPORTING_DIR) not in sys.path:
    sys.path.insert(0, str(REPORTING_DIR))

from build_phase15_unknown_thesis_diagnostics import build_ticker_payload
from smr_agents import DB_PATH
from smr_paths import project_path
from smr_wiki import now_ts


WATCHLIST_PATH = project_path("00_control", "phase6_ai_core_watchlist.json")


def apply_patch_to_payload(payload: dict, ticker: str, patch: dict) -> tuple[dict, bool]:
    changed = False
    ticker = ticker.upper()
    output = json.loads(json.dumps(payload, ensure_ascii=False))
    for item in output.get("tickers") or []:
        if str(item.get("ticker") or "").upper() != ticker:
            continue
        for key, value in patch.items():
            if key == "candidate_thesis_types":
                continue
            if item.get(key) != value:
                item[key] = value
                changed = True
        break
    return output, changed


def build_patch_result(ticker: str, *, execute: bool = False, db_path: str = str(DB_PATH)) -> dict:
    conn = sqlite3.connect(db_path)
    try:
        diagnostics = build_ticker_payload(conn, ticker)
    finally:
        conn.close()
    patch = diagnostics.get("suggested_metadata_patch") or {}
    original = json.loads(WATCHLIST_PATH.read_text(encoding="utf-8"))
    patched, changed = apply_patch_to_payload(original, ticker, patch)
    result = {
        "generated_at": now_ts(),
        "ticker": ticker.upper(),
        "mode": "execute" if execute else "dry_run",
        "watchlist_path": str(WATCHLIST_PATH),
        "suggested_metadata_patch": patch,
        "after_patch_simulation": diagnostics.get("after_patch_simulation"),
        "would_change_file": changed,
        "changed": False,
        "backup_path": None,
        "allow_pending": False,
        "reason": "metadata patch does not bypass thesis-aware evidence gate",
    }
    if execute and changed:
        backup = WATCHLIST_PATH.with_suffix(WATCHLIST_PATH.suffix + f".phase16_backup_{now_ts().replace(':', '').replace(' ', '_')}")
        shutil.copy2(WATCHLIST_PATH, backup)
        WATCHLIST_PATH.write_text(json.dumps(patched, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        result["changed"] = True
        result["backup_path"] = str(backup)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply Phase 16 watchlist metadata patch")
    parser.add_argument("--ticker", default="002230.SZ")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    result = build_patch_result(args.ticker, execute=args.execute)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
