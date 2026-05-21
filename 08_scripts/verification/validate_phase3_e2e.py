#!/usr/bin/env python3
"""Controlled Phase 3 end-to-end validation.

This is a deterministic validation harness, not a live market-data claim. It
uses real ticker identifiers across A/H/US and controlled seed evidence to prove
the Phase 3 gates can produce:

1. one pending_human_review candidate,
2. one observation_only candidate with explicit missing requirements,
3. one proxy-only candidate_shadow that remains distinct from official consensus.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_claim_graph import ensure_claim_graph_tables
from smr_consensus_proxy import build_consensus_revision_proxy, ensure_consensus_proxy_table
from smr_data_health import ensure_data_health_tables
from smr_decision import ensure_decision_tables
from smr_filings_ingestion import export_filings_to_evidence, seed_filing_document, update_filings_health_rows
from smr_news_ingestion import export_news_to_evidence, seed_news_item, update_news_health_rows
from smr_recommendation_candidate import build_recommendation_candidate
from smr_recommendation_promotion import evaluate_promotion, promotion_to_dict
from smr_registry import register_snapshot
from smr_valuation import ensure_valuation_table
from smr_wiki import now_ts

SCRIPT_NAME = "validate_phase3_e2e.py"


CASES = [
    {
        "case_id": "phase3_e2e_us_pending",
        "ticker": "NVDA",
        "market": "US",
        "action": "buy NVDA",
        "news_title": "NVDA raises AI guidance",
        "news_body": "NVDA management raised AI revenue outlook for data center demand.",
        "filing_title": "NVDA 10-Q earnings release",
        "filing_body": "NVDA revenue increased materially. Risk factors include supply constraints and customer concentration.",
        "filing_source_key": "sec_filing_document",
        "proxy_text": "NVDA 2026E EPS 1.20 -> 1.45 guidance raise beat higher",
        "proxy_method": "guidance_change",
        "proxy_evidence_limit": 2,
        "valuation_allowed_usage": "promotion_eligible",
        "expected_status": "pending_human_review",
    },
    {
        "case_id": "phase3_e2e_h_observation",
        "ticker": "09988.HK",
        "market": "H",
        "action": "buy 09988.HK",
        "news_title": "09988.HK cloud demand watch",
        "news_body": "09988.HK cloud demand commentary is positive, but the signal is still secondary news only.",
        "filing_title": "09988.HK exchange announcement",
        "filing_body": "09988.HK disclosed operating updates and risk factors. No forward EPS support is available.",
        "filing_source_key": "hkex_announcement",
        "proxy_text": "09988.HK commentary beat",
        "proxy_method": "news_language_proxy",
        "proxy_evidence_limit": 0,
        "valuation_allowed_usage": "context_only",
        "expected_status": "observation_only",
    },
    {
        "case_id": "phase3_e2e_a_proxy_shadow",
        "ticker": "000001.SZ",
        "market": "A",
        "action": "buy 000001.SZ",
        "news_title": "000001.SZ earnings expectation proxy improves",
        "news_body": "000001.SZ showed a possible expectation-gap signal from secondary reporting.",
        "filing_title": "000001.SZ CN exchange announcement",
        "filing_body": "000001.SZ primary filing evidence exists, but proxy strength remains below pending-review threshold.",
        "filing_source_key": "cninfo_announcement",
        "proxy_text": "000001.SZ EPS 1.00 -> 1.08 beat higher",
        "proxy_method": "broker_report_extraction",
        "proxy_evidence_limit": 1,
        "valuation_allowed_usage": "supporting_evidence",
        "expected_status": "candidate_shadow",
    },
]


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def ensure_validation_tables(conn: sqlite3.Connection) -> None:
    ensure_data_health_tables(conn)
    ensure_claim_graph_tables(conn)
    ensure_decision_tables(conn)
    ensure_consensus_proxy_table(conn)
    ensure_valuation_table(conn)


def evidence_ids_for(conn: sqlite3.Connection, ticker: str, limit: int = 4) -> list[str]:
    if limit <= 0:
        return []
    rows = conn.execute(
        """
        SELECT evidence_id, source_key
        FROM evidence_items
        WHERE text_excerpt LIKE ?
           OR metadata_json LIKE ?
        ORDER BY id DESC
        LIMIT 50
        """,
        (f"%{ticker}%", f"%{ticker}%"),
    ).fetchall()
    evidence_ids = []
    seen_sources = set()
    for row in rows:
        source_key = row[1] or row[0]
        if source_key in seen_sources:
            continue
        seen_sources.add(source_key)
        evidence_ids.append(row[0])
        if len(evidence_ids) >= limit:
            break
    return evidence_ids


def controlled_health_snapshot(ticker: str, market: str) -> dict[str, Any]:
    rows = [
        {"source_key": "daily_bar", "market": "A", "asset_type": "stock", "data_type": "daily_bar", "freshness_status": "fresh", "blocking_level": "none"},
        {"source_key": "daily_bar", "market": "H", "asset_type": "stock", "data_type": "daily_bar", "freshness_status": "fresh", "blocking_level": "none"},
        {"source_key": "daily_bar", "market": "US", "asset_type": "stock", "data_type": "daily_bar", "freshness_status": "fresh", "blocking_level": "none"},
        {"source_key": "manual_news", "market": market, "asset_type": "stock", "data_type": "news", "freshness_status": "fresh", "blocking_level": "none"},
        {
            "source_key": f"watchlist_filings:{ticker}",
            "market": market,
            "asset_type": "stock",
            "data_type": "filings",
            "freshness_status": "fresh",
            "blocking_level": "none",
            "metadata": {"scope": "watchlist", "ticker": ticker},
        },
    ]
    return {
        "generated_at": now_ts(),
        "overall_status": "fresh",
        "mode": "controlled_seed_validation",
        "items": rows,
        "capability_status": {},
    }


def seed_case(conn: sqlite3.Connection, case: dict[str, Any]) -> list[str]:
    ticker = case["ticker"]
    seed_news_item(
        conn,
        title=case["news_title"],
        body=case["news_body"],
        source_key="manual_news",
        ticker=ticker,
        market=case["market"],
    )
    seed_filing_document(
        conn,
        ticker=ticker,
        title=case["filing_title"],
        body=case["filing_body"],
        source_key=case["filing_source_key"],
        market=case["market"],
    )
    export_news_to_evidence(conn, limit=200)
    export_filings_to_evidence(conn, limit=200)
    update_news_health_rows(conn)
    update_filings_health_rows(conn)
    return evidence_ids_for(conn, ticker, limit=case["proxy_evidence_limit"])


def evaluate_case(conn: sqlite3.Connection, case: dict[str, Any]) -> dict[str, Any]:
    ticker = case["ticker"]
    evidence_ids = seed_case(conn, case)
    proxy = build_consensus_revision_proxy(
        conn,
        case["proxy_text"],
        evidence_ids=evidence_ids,
        ticker=ticker,
        method=case["proxy_method"],
    )
    dashboard_summary = {
        "action": case["action"],
        "ticker": ticker,
        "suggested_position_pct": 2.0,
        "max_position_pct": 5.0,
        "confidence_rationale": "controlled Phase 3 validation sample",
        "kill_triggers": ["Primary evidence breaks thesis"],
    }
    valuation = {
        "ticker": ticker,
        "market": case["market"],
        "allowed_usage": case["valuation_allowed_usage"],
        "valuation_status": case["valuation_allowed_usage"],
        "missing_data": [] if case["valuation_allowed_usage"] != "context_only" else ["forward_eps", "historical_percentile", "peer_set"],
    }
    evidence_check = {
        "severity": "pass",
        "evidence_summary": {
            "source_path_count": 2,
            "primary_anchor_count": 1,
        },
        "independent_source_count": 2,
        "primary_evidence_count": 1,
    }
    claim_graph = {
        "total_core_claims": 2,
        "supported_core_claims": 2,
        "unsupported_core_claims": [],
        "counter_evidence_count": 1,
        "recommendation_allowed": True,
    }
    bear_case = {
        "bear_case_claims": [{"claim_text": "Opposite case: signal may be explained by timing or cycle noise."}],
        "deal_breakers": ["Primary evidence breaks thesis"],
        "bear_case_strength": "medium",
        "deal_breaker_count": 1,
        "data_quality_risk": "medium",
    }
    promotion = evaluate_promotion(
        conn,
        report_id=f"report__{case['case_id']}",
        recommendation_id=case["case_id"],
        from_status="observation_only",
        dashboard_summary=dashboard_summary,
        data_health_snapshot=controlled_health_snapshot(ticker, case["market"]),
        evidence_check_snapshot=evidence_check,
        claim_graph_snapshot=claim_graph,
        valuation_snapshot=valuation,
        consensus_proxy=proxy,
        bear_case=bear_case,
        risk_snapshot={"status": "pass"},
        lint_result={"max_severity": "info", "issues": []},
        write_ledger=True,
    )
    candidate = build_recommendation_candidate(
        conn,
        recommendation_id=case["case_id"],
        ticker=ticker,
        report=dashboard_summary,
        claim_graph=claim_graph,
        evidence_check=evidence_check,
        valuation_snapshot=valuation,
        consensus_proxy=proxy,
        bear_case=bear_case,
        risk_snapshot={"status": "pass"},
        market_signal={"signal": "positive"},
        promotion_result=promotion,
        write_ledger=True,
    )
    result = {
        "case_id": case["case_id"],
        "ticker": ticker,
        "market": case["market"],
        "expected_status": case["expected_status"],
        "actual_status": candidate["status"],
        "action": candidate["action"],
        "promotion": promotion_to_dict(promotion),
        "candidate": candidate,
        "consensus_proxy": proxy,
        "evidence_ids": evidence_ids,
        "passed": candidate["status"] == case["expected_status"],
    }
    register_snapshot(
        conn,
        entity_type="phase3_e2e_validation_case",
        entity_id=case["case_id"],
        status=candidate["status"],
        source=SCRIPT_NAME,
        payload=result,
    )
    return result


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    for result in results:
        status = result["actual_status"]
        status_counts[status] = status_counts.get(status, 0) + 1
    has_pending = status_counts.get("pending_human_review", 0) >= 1
    has_observation = status_counts.get("observation_only", 0) >= 1
    has_proxy_shadow = any(
        result["consensus_proxy"].get("is_official_consensus") is False
        and result["consensus_proxy"].get("proxy_quality") == "medium"
        and result["actual_status"] == "candidate_shadow"
        for result in results
    )
    all_expected = all(result["passed"] for result in results)
    return {
        "overall_status": "partial_pass" if has_pending and has_observation and has_proxy_shadow and all_expected else "needs_attention",
        "status_counts": status_counts,
        "has_pending_human_review": has_pending,
        "has_observation_only": has_observation,
        "has_proxy_candidate_shadow": has_proxy_shadow,
        "all_cases_matched_expected_status": all_expected,
        "mode": "controlled_seed_validation",
        "note": "Uses real ticker identifiers with controlled seed evidence; run live ingestion separately for real-source validation.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 3 promotion/candidate E2E with controlled A/H/US samples")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--dry-run", action="store_true", help="Run validation and roll back DB writes")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db_path)
    conn.row_factory = sqlite3.Row
    try:
        ensure_validation_tables(conn)
        results = [evaluate_case(conn, case) for case in CASES]
        summary = summarize(results)
        payload = {"summary": summary, "results": results}
        register_snapshot(
            conn,
            entity_type="phase3_e2e_validation",
            entity_id="latest",
            status=summary["overall_status"],
            source=SCRIPT_NAME,
            payload=payload,
        )
        if args.dry_run:
            conn.rollback()
            payload["summary"]["dry_run"] = True
        else:
            conn.commit()
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        return 0 if summary["overall_status"] == "partial_pass" else 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
