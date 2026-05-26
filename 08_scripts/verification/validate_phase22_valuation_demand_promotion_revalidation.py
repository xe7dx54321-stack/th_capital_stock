#!/usr/bin/env python3
"""Validate Phase 22 promotion impact after valuation/demand/proxy upgrades."""

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

from build_phase22_confirmed_demand_evidence import build_ticker_confirmed_demand
from build_phase22_proxy_strengthening import build_ticker_proxy_strengthening, proxy_strengthened
from smr_agents import DB_PATH
from smr_bear_case_mitigation import build_ticker_bear_case_mitigation
from smr_demand_valuation_linkage import build_demand_valuation_linkage, demand_valuation_linkage_improved
from smr_phase6_watchlists import load_watchlist_config
from smr_promotion_block_reason import build_ticker_block_diagnostics
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_valuation_gate_v2 import diagnose_valuation_gate_v2, valuation_gate_v2_improved
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "validate_phase22_valuation_demand_promotion_revalidation.py"


def parse_tickers(raw: str | None, watchlist: str | None = None) -> list[str]:
    if raw:
        return [item.strip().upper() for item in raw.split(",") if item.strip()]
    if watchlist:
        return [str(item.get("ticker") or "").upper() for item in load_watchlist_config(watchlist).get("tickers") or [] if item.get("ticker")]
    return []


def _can_reduced_size_pending(bear_gate: dict, val_gate: dict, proxy_after: dict) -> bool:
    if bear_gate.get("blocks_pending"):
        return False
    if str(bear_gate.get("overall_residual_risk_level") or "").lower() in {"high", "critical"}:
        return False
    if val_gate.get("after_status") in {"blocked", "insufficient", "context_only"}:
        return False
    if proxy_after.get("status") in {"weak", "missing", "invalid", "conflicted"}:
        return False
    return bool(val_gate.get("allows_reduced_size_pending") and proxy_after.get("usable_for_reduced_size_pending"))


def _why_no_pending(ticker: str, bear_gate: dict, val_gate: dict, proxy_after: dict, confirmed: dict) -> list[str]:
    reasons = []
    if bear_gate.get("blocks_pending"):
        reasons.append(f"bear case remains blocking for {ticker}")
    if val_gate.get("after_status") in {"blocked", "insufficient", "context_only"}:
        reasons.append(f"valuation remains {val_gate.get('after_status')}")
    elif val_gate.get("after_status") == "supporting_evidence":
        reasons.append("valuation remains supporting only")
    if proxy_after.get("status") in {"weak", "missing", "invalid", "conflicted"}:
        reasons.append(f"proxy remains {proxy_after.get('status')}")
    if (confirmed.get("confirmed_order_count") or 0) == 0:
        reasons.append(confirmed.get("no_confirmed_order_reason") or "no confirmed demand evidence")
    return list(dict.fromkeys(reasons)) or ["promotion remains conservative because full gate stack did not pass"]


def ticker_result(conn: sqlite3.Connection, ticker: str, *, watchlist: str) -> dict:
    before = build_ticker_block_diagnostics(conn, ticker, watchlist_id=watchlist)
    linkage = build_demand_valuation_linkage(conn, ticker, thesis_type=before.get("primary_thesis_type"), persist=True)
    valuation = diagnose_valuation_gate_v2(conn, ticker, watchlist_id=watchlist, phase19_diag=before, demand_linkage=linkage)
    confirmed = build_ticker_confirmed_demand(conn, ticker)
    confirmed_summary = confirmed.get("confirmed_demand_evidence") or {}
    proxy = build_ticker_proxy_strengthening(conn, ticker, watchlist=watchlist)
    bear = build_ticker_bear_case_mitigation(conn, ticker, watchlist_id=watchlist, include_direct_demand=True)
    bear_gate = bear.get("bear_case_mitigation") or {}
    val_gate = valuation.get("valuation_gate_v2") or {}
    proxy_gate = proxy.get("proxy_strengthening") or {}
    proxy_after = proxy_gate.get("after") or {}
    can_pending = _can_reduced_size_pending(bear_gate, val_gate, proxy_after)
    # Phase 22 is a revalidation layer; it reports eligibility but does not write
    # pending review rows or create paper orders.
    new_pending = False
    why_changed = []
    if valuation_gate_v2_improved(valuation):
        why_changed.append("valuation gate upgraded from supporting/context to stronger diagnostic status")
    if demand_valuation_linkage_improved(linkage):
        why_changed.append("direct demand evidence supports revenue growth assumption")
    if proxy_strengthened(proxy):
        why_changed.append("proxy signal strengthened with independent demand evidence")
    if can_pending:
        why_changed.append("gate stack is eligible for reduced-size human review, but no automatic pending was created")
    warnings = _why_no_pending(ticker, bear_gate, val_gate, proxy_after, confirmed_summary)
    warnings.extend(val_gate.get("remaining_blockers") or [])
    warnings.extend((proxy_gate.get("remaining_requirements") or [])[:4])
    return {
        "ticker": ticker,
        "before_status": before.get("status"),
        "after_status": before.get("status") if not new_pending else "pending_human_review",
        "promotion_mode": "reduced_size_pending" if new_pending else None,
        "primary_gate_before": before.get("primary_blocking_gate"),
        "valuation_before": val_gate.get("before_status"),
        "valuation_after": val_gate.get("after_status"),
        "demand_valuation_linkage": (linkage.get("demand_valuation_linkage") or {}).get("status"),
        "confirmed_order_count": confirmed_summary.get("confirmed_order_count"),
        "tender_or_procurement_count": confirmed_summary.get("tender_or_procurement_count"),
        "customer_capex_count": confirmed_summary.get("customer_capex_count"),
        "proxy_before": (proxy_gate.get("before") or {}).get("status"),
        "proxy_after": proxy_after.get("status"),
        "bear_case_status_after": bear_gate.get("overall_status"),
        "reduced_size_pending_eligible": can_pending,
        "why_changed": why_changed,
        "why_no_pending": _why_no_pending(ticker, bear_gate, val_gate, proxy_after, confirmed_summary),
        "remaining_warnings": list(dict.fromkeys(warnings))[:12],
        "new_pending_created": new_pending,
        "requires_human_review": bool(new_pending),
        "paper_order_allowed": False,
    }


def build_payload(conn: sqlite3.Connection, tickers: list[str], *, watchlist: str = "ai_core") -> dict:
    rows = [ticker_result(conn, ticker, watchlist=watchlist) for ticker in tickers]
    summary = {
        "tickers_checked": len(rows),
        "valuation_gate_improved": sum(1 for row in rows if any("valuation gate" in item for item in row.get("why_changed") or [])),
        "demand_valuation_linkage_improved": sum(1 for row in rows if any("revenue growth assumption" in item for item in row.get("why_changed") or [])),
        "proxy_strengthened": sum(1 for row in rows if any("proxy signal strengthened" in item for item in row.get("why_changed") or [])),
        "reduced_size_pending_eligible": sum(1 for row in rows if row.get("reduced_size_pending_eligible")),
        "new_reduced_size_pending": 0,
        "new_pending_created": 0,
        "full_size_pending_created": 0,
        "gate_improvements": sum(1 for row in rows if row.get("why_changed")),
    }
    return {
        "generated_at": now_ts(),
        "overall_status": "partial_pass" if summary["gate_improvements"] else "pass",
        "summary": summary,
        "ticker_results": rows,
        "why_no_pending": [reason for row in rows for reason in row.get("why_no_pending") or []][:16],
        "safety": {
            "promotion_rules_relaxed": False,
            "paper_order_allowed": False,
            "full_size_pending_created": False,
            "valuation_context_only_pending_allowed": False,
            "weak_proxy_pending_allowed": False,
            "high_unresolved_core_bear_case_pending_allowed": False,
            "indication_treated_as_confirmed_order": False,
            "proxy_eps_official_consensus": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 22 valuation/demand promotion impact")
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
            entity_type="phase22_valuation_demand_promotion_revalidation",
            entity_id=args.tickers or args.watchlist,
            status=payload["overall_status"],
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase22 valuation/demand promotion revalidation complete", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
