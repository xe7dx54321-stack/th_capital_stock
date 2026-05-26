#!/usr/bin/env python3
"""Validate Phase 20 promotion impact after gate strengthening diagnostics."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parents[1] / "reporting"
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase20_002230_thesis_evidence_pack import build_payload as build_002230_pack
from smr_agents import DB_PATH
from smr_bear_case_mitigation import bear_case_mitigation_improved, build_ticker_bear_case_mitigation
from smr_phase6_watchlists import load_watchlist_config
from smr_promotion_block_reason import build_ticker_block_diagnostics
from smr_proxy_signal_gate import build_proxy_signal_gate, proxy_gate_improved
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_valuation_gate import diagnose_valuation_gate, valuation_gate_improved
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "validate_phase20_promotion_revalidation.py"


def parse_tickers(raw: str | None, watchlist: str | None = None) -> list[str]:
    if raw:
        return [item.strip().upper() for item in raw.split(",") if item.strip()]
    if watchlist:
        return [str(item.get("ticker") or "").upper() for item in load_watchlist_config(watchlist).get("tickers") or [] if item.get("ticker")]
    return []


def _why_no_pending(ticker: str, bear: dict, valuation: dict, proxy: dict, thesis_pack: dict | None) -> list[str]:
    reasons = []
    bear_gate = bear.get("bear_case_mitigation") or {}
    val_gate = valuation.get("valuation_gate") or {}
    proxy_gate = proxy.get("proxy_signal_gate") or {}
    if bear_gate.get("blocks_pending"):
        reasons.append(f"bear case remains blocking for {ticker}")
    if val_gate.get("after_status") in {"blocked", "insufficient", "context_only"}:
        reasons.append(f"valuation gate remains {val_gate.get('after_status')} for {ticker}")
    if proxy_gate.get("status") in {"weak", "missing", "invalid", "conflicted"}:
        reasons.append(f"proxy signal remains {proxy_gate.get('status')} for {ticker}")
    if thesis_pack and not (thesis_pack.get("after") or {}).get("allow_pending"):
        reasons.append("002230.SZ thesis evidence is still insufficient for pending")
    return reasons or ["promotion remains conservative because full gate stack did not pass"]


def ticker_result(conn: sqlite3.Connection, ticker: str, *, watchlist: str) -> dict:
    before = build_ticker_block_diagnostics(conn, ticker, watchlist_id=watchlist)
    bear = build_ticker_bear_case_mitigation(conn, ticker, watchlist_id=watchlist)
    valuation = diagnose_valuation_gate(conn, ticker, phase19_diag=before)
    proxy = build_proxy_signal_gate(conn, ticker, watchlist_id=watchlist)
    thesis_pack = build_002230_pack(conn) if ticker.upper() == "002230.SZ" else None
    why_changed = []
    if bear_case_mitigation_improved(bear):
        why_changed.append("bear_case_gate improved for at least one claim with linked evidence")
    if valuation_gate_improved(valuation):
        why_changed.append("valuation gate moved to stronger supporting status")
    if proxy_gate_improved(proxy):
        why_changed.append("proxy gate has usable internal supporting signal")
    if thesis_pack and (thesis_pack.get("after") or {}).get("thesis_status") == "evidence_backed_candidate":
        why_changed.append("thesis evidence moved beyond metadata-only candidate")
    after_status = before.get("status")
    before_bear_gate = before.get("bear_case_gate") or {}
    existing_reduced_size_pending = bool(
        after_status == "pending_human_review"
        and before_bear_gate.get("action_effect") in {"reduce_position_size", "reduced_size_candidate_allowed"}
    )
    promotion_mode = "reduced_size_pending" if existing_reduced_size_pending else None
    new_pending = False
    paper_order_allowed = False
    return {
        "ticker": ticker,
        "before_status": before.get("status"),
        "after_status": after_status,
        "promotion_mode": promotion_mode,
        "primary_gate_before": before.get("primary_blocking_gate"),
        "bear_case_status_after": (bear.get("bear_case_mitigation") or {}).get("overall_status"),
        "valuation_status_after": (valuation.get("valuation_gate") or {}).get("after_status"),
        "proxy_status_after": (proxy.get("proxy_signal_gate") or {}).get("status"),
        "thesis_status_after": (thesis_pack.get("after") or {}).get("thesis_status") if thesis_pack else before.get("primary_thesis_type"),
        "why_changed": why_changed,
        "why_no_pending": _why_no_pending(ticker, bear, valuation, proxy, thesis_pack),
        "remaining_warnings": list(
            dict.fromkeys(
                ((bear.get("bear_case_mitigation") or {}).get("responses") or [{}])[-1].get("missing_evidence", [])
                + ((valuation.get("valuation_gate") or {}).get("remaining_valuation_blockers") or [])
                + ((proxy.get("proxy_signal_gate") or {}).get("missing_requirements") or [])
            )
        )[:8],
        "new_pending_created": new_pending,
        "existing_reduced_size_pending": existing_reduced_size_pending,
        "requires_human_review": bool(new_pending or after_status == "pending_human_review"),
        "paper_order_allowed": paper_order_allowed,
    }


def build_payload(conn: sqlite3.Connection, tickers: list[str], *, watchlist: str = "ai_core") -> dict:
    rows = [ticker_result(conn, ticker, watchlist=watchlist) for ticker in tickers]
    summary = {
        "tickers_checked": len(rows),
        "bear_case_gate_improved": sum(1 for row in rows if any("bear_case_gate" in item for item in row.get("why_changed") or [])),
        "valuation_gate_improved": sum(1 for row in rows if any("valuation gate" in item for item in row.get("why_changed") or [])),
        "proxy_gate_improved": sum(1 for row in rows if any("proxy gate" in item for item in row.get("why_changed") or [])),
        "thesis_evidence_improved": sum(1 for row in rows if any("thesis evidence" in item for item in row.get("why_changed") or [])),
        "new_reduced_size_pending": sum(1 for row in rows if row.get("new_pending_created") and row.get("promotion_mode") == "reduced_size_pending"),
        "new_pending_created": sum(1 for row in rows if row.get("new_pending_created")),
        "full_size_pending_created": 0,
        "gate_improvements": sum(1 for row in rows if row.get("why_changed")),
    }
    why_no_pending = [reason for row in rows for reason in row.get("why_no_pending") or [] if not row.get("new_pending_created")]
    return {
        "generated_at": now_ts(),
        "overall_status": "partial_pass" if summary["gate_improvements"] else "pass",
        "summary": summary,
        "ticker_results": rows,
        "why_no_pending": why_no_pending[:12],
        "safety": {
            "promotion_rules_relaxed": False,
            "paper_order_allowed": False,
            "unknown_or_metadata_only_pending_allowed": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 20 promotion revalidation")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--watchlist", default="ai_core")
    parser.add_argument("--tickers")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, parse_tickers(args.tickers, args.watchlist if not args.tickers else None), watchlist=args.watchlist)
        register_snapshot(
            conn,
            entity_type="phase20_promotion_revalidation",
            entity_id=args.watchlist if not args.tickers else args.tickers,
            status=payload["overall_status"],
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase20 promotion revalidation complete", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
