#!/usr/bin/env python3
"""Phase 11 peer valuation data builder."""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
DATA_DIR = Path(__file__).resolve().parents[1] / "data_harvester"
for path in (LIB_DIR, DATA_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from ah_daily_bar import fetch_us_stock_history, insert_us_daily_bars
from smr_agents import DB_PATH
from smr_fundamentals import build_fundamentals_snapshot
from smr_paths import project_path
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_valuation import build_peer_set_snapshot, latest_factor, load_peer_set_config, market_for_ticker, peer_set_definition
from smr_wiki import now_ts


SCRIPT_NAME = "build_peer_valuation_data.py"
PEER_REASON_TO_BLOCKER = {
    "peer_set_config_missing": "PEER_SET_CONFIG_MISSING",
    "peer_price_missing": "PEER_PRICE_MISSING",
    "peer_fundamentals_missing": "PEER_FUNDAMENTALS_MISSING",
    "peer_multiples_missing": "PEER_MULTIPLES_MISSING",
    "peer_count_insufficient": "PEER_COUNT_INSUFFICIENT",
    "peer_data_missing": "PEER_DATA_MISSING",
}


def _run(command: list[str], timeout: int = 180) -> dict[str, Any]:
    try:
        result = subprocess.run(
            command,
            cwd=project_path(),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "command": command,
            "returncode": result.returncode,
            "stdout_tail": (result.stdout or "")[-800:],
            "stderr_tail": (result.stderr or "")[-800:],
        }
    except subprocess.TimeoutExpired:
        return {"command": command, "returncode": 124, "stderr_tail": f"timeout_after_{timeout}s", "stdout_tail": ""}


def refresh_peer_inputs(conn: sqlite3.Connection, ticker: str, *, timeout: int = 180) -> list[dict[str, Any]]:
    market = market_for_ticker(ticker)
    actions: list[dict[str, Any]] = []
    if market == "US":
        try:
            rows = fetch_us_stock_history(ticker, days=10)
            inserted = insert_us_daily_bars(conn, rows)
            actions.append({"ticker": ticker, "action": "refresh_us_price", "status": "success" if inserted else "empty", "rows": inserted})
        except Exception as exc:
            actions.append({"ticker": ticker, "action": "refresh_us_price", "status": "failed", "reason": str(exc)})
        try:
            snapshot = build_fundamentals_snapshot(conn, ticker, timeout=60, prefer_live=True)
            actions.append(
                {
                    "ticker": ticker,
                    "action": "refresh_us_fundamentals",
                    "status": snapshot.get("freshness_status") or "unknown",
                    "snapshot_id": snapshot.get("snapshot_id"),
                }
            )
        except Exception as exc:
            actions.append({"ticker": ticker, "action": "refresh_us_fundamentals", "status": "failed", "reason": str(exc)})
        return actions

    if market in {"H", "A"}:
        price_run = _run(
            [sys.executable, str(project_path("08_scripts", "data_harvester", "ah_daily_bar.py")), "--days", "10", "--ts-code", ticker],
            timeout=timeout,
        )
        actions.append({"ticker": ticker, "action": "refresh_ah_price", "status": "success" if price_run["returncode"] == 0 else "failed", **price_run})
        factor_run = _run(
            [sys.executable, str(project_path("08_scripts", "factor_engine", "fundamental.py")), "--code", ticker],
            timeout=timeout,
        )
        actions.append({"ticker": ticker, "action": "refresh_ah_factors", "status": "success" if factor_run["returncode"] == 0 else "failed", **factor_run})
    return actions


def _target_for_peer_set(peer_set_id: str) -> str:
    config = load_peer_set_config()
    peer_set = (config.get("peer_sets") or {}).get(peer_set_id) or {}
    return str(peer_set.get("primary_ticker") or (peer_set.get("tickers") or [""])[0])


def peer_blockers(snapshot: dict[str, Any]) -> list[str]:
    available = int(snapshot.get("peer_count_available") or 0)
    required = int(snapshot.get("peer_count_required") or 0)
    if snapshot.get("peer_set_status") == "available" and available >= required:
        return []
    codes = []
    for reason in snapshot.get("peer_missing_reasons") or []:
        codes.append(PEER_REASON_TO_BLOCKER.get(str(reason), "PEER_DATA_MISSING"))
    return sorted(set(codes))


def peer_missing_detail(snapshot: dict[str, Any]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for peer in snapshot.get("peer_multiples") or []:
        reasons = list(peer.get("missing_reasons") or [])
        reasons.extend(f"{metric}:{reason}" for metric, reason in (peer.get("missing_reasons_by_metric") or {}).items())
        result[peer["ticker"]] = sorted(set(reasons))
    return result


def build_peer_valuation_payload(
    conn: sqlite3.Connection,
    *,
    ticker: str | None = None,
    peer_set_id: str | None = None,
    execute: bool = False,
    timeout: int = 180,
) -> dict[str, Any]:
    ticker = (ticker or _target_for_peer_set(peer_set_id or "") or "09988.HK").upper()
    resolved_peer_set_id, peer_set = peer_set_definition(ticker)
    if peer_set_id:
        resolved_peer_set_id = peer_set_id
        config = load_peer_set_config()
        peer_set = dict((config.get("peer_sets") or {}).get(peer_set_id) or peer_set)
        ticker = str(peer_set.get("primary_ticker") or ticker).upper()
    peers = [str(item).upper() for item in peer_set.get("tickers") or []]
    actions: list[dict[str, Any]] = []
    if execute:
        for symbol in peers:
            actions.extend(refresh_peer_inputs(conn, symbol, timeout=timeout))
    snapshot = build_peer_set_snapshot(conn, ticker, latest_factor(conn, ticker))
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "peer_set_id": snapshot.get("peer_set_id") or resolved_peer_set_id,
        "peer_set_status": snapshot.get("peer_set_status"),
        "required_min_peers": snapshot.get("peer_count_required"),
        "peer_count_available": snapshot.get("peer_count_available"),
        "peer_count_required": snapshot.get("peer_count_required"),
        "peer_comparison_status": snapshot.get("peer_comparison_status"),
        "metrics": snapshot.get("metrics") or {},
        "peers": snapshot.get("peer_multiples") or [],
        "remaining_peer_blockers": peer_blockers(snapshot),
        "peer_missing_detail": peer_missing_detail(snapshot),
        "actions": actions,
        "mode": "execute" if execute else "read_only",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 11 peer valuation data")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker")
    parser.add_argument("--peer-set")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db_path)
    conn.row_factory = sqlite3.Row
    try:
        payload = build_peer_valuation_payload(
            conn,
            ticker=args.ticker,
            peer_set_id=args.peer_set,
            execute=args.execute,
            timeout=args.timeout,
        )
        register_snapshot(
            conn,
            entity_type="phase11_peer_valuation_data",
            entity_id=payload["ticker"],
            status=payload.get("peer_set_status") or "unknown",
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase11 peer valuation data built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
