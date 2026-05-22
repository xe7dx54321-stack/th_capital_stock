#!/usr/bin/env python3
"""Phase 6 multi-ticker live reliability and portfolio risk validation."""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_bear_case import build_bear_case
from smr_claim_graph import claim_graph_summary, link_claim_evidence, upsert_claim
from smr_data_health import refresh_system_data_health
from smr_decision import ensure_decision_tables
from smr_evidence_quality import update_evidence_quality_scores
from smr_fundamentals import build_fundamentals_snapshot
from smr_news_ingestion import export_news_to_evidence, ingest_yahoo_finance_news, update_news_health_rows
from smr_filings_ingestion import export_filings_to_evidence, update_filings_health_rows
from smr_paper_portfolio import ensure_paper_portfolio_tables
from smr_phase6_watchlists import load_watchlist_config, watchlist_items, watchlist_map
from smr_portfolio_risk import evaluate_portfolio_risk
from smr_promotion_debugger import explain_promotion_result
from smr_proxy_extraction import build_live_consensus_proxy
from smr_recommendation_candidate import build_recommendation_candidate
from smr_recommendation_promotion import evaluate_promotion, promotion_to_dict
from smr_registry import register_snapshot
from smr_valuation import build_valuation_snapshot
from smr_wiki import generate_execution_id, now_ts


SCRIPT_NAME = "validate_phase6_multi_ticker_live.py"


def parse_tickers(raw: str | None) -> list[str]:
    return [item.strip().upper() for item in str(raw or "").split(",") if item.strip()]


def market_for_ticker(ticker: str) -> str:
    if ticker.endswith((".SZ", ".SH", ".BJ")):
        return "A"
    if ticker.endswith(".HK"):
        return "H"
    return "US"


def run_command(command: list[str], timeout: int = 240) -> dict[str, Any]:
    try:
        result = subprocess.run(
            command,
            cwd=Path(__file__).resolve().parents[2],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout or "",
            "stderr": result.stderr or "",
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        return {
            "command": command,
            "returncode": 124,
            "stdout": stdout,
            "stderr": f"timeout_after_{timeout}s",
        }


def parse_json_stdout(run: dict[str, Any]) -> dict[str, Any]:
    stdout = run.get("stdout") or ""
    start = stdout.find("{")
    end = stdout.rfind("}")
    if start < 0 or end <= start:
        return {"parse_error": "json_payload_not_found"}
    try:
        return json.loads(stdout[start : end + 1])
    except json.JSONDecodeError as exc:
        return {"parse_error": str(exc)}


def compact_run(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "command": run.get("command"),
        "returncode": run.get("returncode"),
        "stdout_tail": (run.get("stdout") or "")[-1000:],
        "stderr_tail": (run.get("stderr") or "")[-500:],
    }


def compact_ingestion(ingestion: dict[str, Any]) -> dict[str, Any]:
    return {
        "news_run": compact_run(ingestion.get("news_run") or {}),
        "filings_run": compact_run(ingestion.get("filings_run") or {}),
        "news_payload": ingestion.get("news_payload") or {},
        "filings_payload": ingestion.get("filings_payload") or {},
        "news_quality_metrics": ingestion.get("news_quality_metrics") or {},
    }


def latest_registry_payload(conn: sqlite3.Connection, entity_type: str) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT payload_json
        FROM task_registry_entry
        WHERE entity_type=?
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """,
        (entity_type,),
    ).fetchone()
    if not row:
        return {}
    try:
        return json.loads(row[0] or "{}")
    except json.JSONDecodeError:
        return {}


def live_evidence_rows(conn: sqlite3.Connection, ticker: str, filing_since_date: str, news_since_date: str, limit: int = 8) -> list[dict[str, Any]]:
    columns = {row[1] for row in conn.execute("PRAGMA table_info(evidence_items)").fetchall()}
    quality_expr = "quality_score" if "quality_score" in columns else "NULL AS quality_score"
    usable_expr = "usable_for_promotion" if "usable_for_promotion" in columns else "NULL AS usable_for_promotion"
    rows: list[dict[str, Any]] = []
    seen_evidence_ids: set[str] = set()
    per_type_limit = max(2, limit // 2)
    for source_type, since_date in (("filing", filing_since_date), ("news", news_since_date)):
        matched_for_type = 0
        scanned = conn.execute(
            f"""
            SELECT evidence_id, source_key, source_type, source_quality, source_status,
                   text_excerpt, metadata_json, {quality_expr}, {usable_expr}, published_at, ingested_at
            FROM evidence_items
            WHERE metadata_json LIKE '%"live"%'
              AND source_type=?
              AND substr(COALESCE(published_at, ingested_at), 1, 10) >= ?
            ORDER BY
              CASE source_quality WHEN 'primary' THEN 0 WHEN 'secondary' THEN 1 ELSE 2 END,
              COALESCE(quality_score, 0) DESC,
              id DESC
            LIMIT ?
            """,
            (source_type, since_date, limit * 40),
        ).fetchall()
        for row in scanned:
            if row[0] in seen_evidence_ids:
                continue
            metadata = json.loads(row[6] or "{}")
            ticker_values = set()
            for key in ("ticker", "symbol", "ts_code"):
                if metadata.get(key):
                    ticker_values.add(str(metadata[key]).upper())
            for item in metadata.get("tickers") or []:
                if item:
                    ticker_values.add(str(item).upper())
            if ticker.upper() not in ticker_values:
                continue
            seen_evidence_ids.add(row[0])
            rows.append(
                {
                    "evidence_id": row[0],
                    "source_key": row[1],
                    "source_type": row[2],
                    "source_quality": row[3],
                    "source_status": row[4],
                    "text_excerpt": row[5],
                    "metadata": metadata,
                    "quality_score": row[7],
                    "usable_for_promotion": bool(row[8]) if row[8] is not None else None,
                    "published_at": row[9],
                    "ingested_at": row[10],
                }
            )
            matched_for_type += 1
            if matched_for_type >= per_type_limit:
                break
    rows.sort(
        key=lambda item: (
            0 if item.get("source_quality") == "primary" else 1,
            -(float(item.get("quality_score") or 0.0)),
            str(item.get("source_type") or ""),
        )
    )
    return rows[:limit]


def build_live_claim_graph(conn: sqlite3.Connection, ticker: str, evidence_rows: list[dict[str, Any]], run_id: str) -> dict[str, Any]:
    report_id = f"phase6_live_report__{ticker}"
    recommendation_id = f"phase6_live__{ticker}"
    claim_id = f"claim_phase6_live_core_{ticker.replace('.', '_')}"
    upsert_claim(
        conn,
        {
            "claim_id": claim_id,
            "report_id": report_id,
            "recommendation_id": recommendation_id,
            "ticker": ticker,
            "theme": "phase6_live_e2e",
            "claim_text": f"{ticker} has live external evidence supporting a reviewable research candidate.",
            "claim_type": "thesis",
            "importance": "core",
            "stance": "base",
            "confidence": 0.55,
            "metadata": {"live_e2e_run_id": run_id},
        },
    )
    for evidence in evidence_rows[:4]:
        link_claim_evidence(conn, claim_id, evidence["evidence_id"], "supports", 0.62, "Phase 6 live E2E evidence link")
    return claim_graph_summary(conn, report_id)


def evidence_check_from_rows(evidence_rows: list[dict[str, Any]]) -> dict[str, Any]:
    independent = len({row["source_key"] for row in evidence_rows if row.get("source_key")})
    primary = sum(1 for row in evidence_rows if row.get("source_quality") == "primary")
    usable = sum(1 for row in evidence_rows if row.get("usable_for_promotion"))
    severity = "pass" if len(evidence_rows) >= 2 and primary >= 1 else "degrade"
    return {
        "severity": severity,
        "evidence_summary": {
            "source_path_count": independent,
            "primary_anchor_count": primary,
            "live_evidence_count": len(evidence_rows),
            "usable_for_promotion_count": usable,
        },
        "independent_source_count": independent,
        "primary_evidence_count": primary,
    }


def proxy_from_live_evidence(conn: sqlite3.Connection, ticker: str, evidence_rows: list[dict[str, Any]]) -> dict[str, Any]:
    proxy = build_live_consensus_proxy(conn, ticker, limit=max(len(evidence_rows), 8))
    if proxy.get("proxy_quality") != "invalid" or not evidence_rows:
        return proxy
    proxy["fallback_evidence_ids"] = [row["evidence_id"] for row in evidence_rows[:4]]
    return proxy


def annotate_ledger(conn: sqlite3.Connection, recommendation_id: str, metadata_updates: dict[str, Any]) -> None:
    row = conn.execute(
        "SELECT metadata_json FROM decision_ledger WHERE recommendation_id=? ORDER BY updated_at DESC LIMIT 1",
        (recommendation_id,),
    ).fetchone()
    if not row:
        return
    metadata = json.loads(row[0] or "{}")
    metadata.update(metadata_updates)
    conn.execute(
        "UPDATE decision_ledger SET metadata_json=?, updated_at=? WHERE recommendation_id=?",
        (json.dumps(metadata, ensure_ascii=False, sort_keys=True, default=str), now_ts(), recommendation_id),
    )


def review_queue_visible(conn: sqlite3.Connection, recommendation_id: str) -> bool:
    row = conn.execute(
        "SELECT COUNT(*) FROM decision_ledger WHERE recommendation_id=? AND status='pending_human_review'",
        (recommendation_id,),
    ).fetchone()
    return bool(row and row[0])


def build_ticker_result(
    conn: sqlite3.Connection,
    ticker: str,
    run_id: str,
    filing_since_date: str,
    news_since_date: str,
    watchlist_lookup: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    watchlist_item = watchlist_lookup.get(ticker.upper()) or {}
    update_evidence_quality_scores(conn, ticker=ticker, limit=500)
    evidence_rows = live_evidence_rows(conn, ticker, filing_since_date, news_since_date)
    live_filing_count = sum(1 for row in evidence_rows if row.get("source_type") == "filing")
    live_news_count = sum(1 for row in evidence_rows if row.get("source_type") == "news")
    fundamentals = build_fundamentals_snapshot(conn, ticker, prefer_live=True)
    data_health = refresh_system_data_health(conn)
    update_news_health_rows(conn, stale_after_minutes=1440)
    update_filings_health_rows(conn, stale_after_minutes=1440)
    valuation = build_valuation_snapshot(conn, ticker, data_health_snapshot=data_health)
    claim_graph = build_live_claim_graph(conn, ticker, evidence_rows, run_id) if evidence_rows else {
        "total_core_claims": 1,
        "supported_core_claims": 0,
        "unsupported_core_claims": [{"claim_id": f"claim_phase6_live_core_{ticker}", "claim_text": "no live evidence", "support_count": 0}],
        "low_quality_core_claims": [],
        "counter_evidence_count": 0,
        "recommendation_allowed": False,
    }
    evidence_check = evidence_check_from_rows(evidence_rows)
    proxy = proxy_from_live_evidence(conn, ticker, evidence_rows) if evidence_rows else {
        "ticker": ticker,
        "market": market_for_ticker(ticker),
        "is_official_consensus": False,
        "proxy_quality": "invalid",
        "usable_for_promotion": False,
        "evidence_ids": [],
        "note": "no live evidence available for proxy",
        "independent_source_count": 0,
    }
    dashboard_summary = {
        "action": f"buy {ticker}",
        "ticker": ticker,
        "theme": watchlist_item.get("theme"),
        "sector": watchlist_item.get("sector"),
        "suggested_position_pct": watchlist_item.get("max_position_pct") or 1.0,
        "max_position_pct": watchlist_item.get("max_position_pct") or 1.0,
        "confidence_rationale": "Phase 6 live E2E candidate generated from live external evidence only.",
        "kill_triggers": ["Live primary evidence no longer supports the thesis."],
    }
    bear_case = build_bear_case(
        conn,
        report_id=f"phase6_live_report__{ticker}",
        recommendation_id=f"phase6_live__{ticker}",
        dashboard_summary=dashboard_summary,
        valuation_snapshot=valuation,
        missing_data=fundamentals.get("missing_fields") or valuation.get("missing_data") or [],
        evidence_ids=[row["evidence_id"] for row in evidence_rows[:4]],
    )
    portfolio_risk = evaluate_portfolio_risk(
        conn,
        ticker=ticker,
        watchlist_item=watchlist_item,
        suggested_position_pct=dashboard_summary.get("suggested_position_pct"),
        max_position_pct=dashboard_summary.get("max_position_pct"),
        watchlist_name="ai_core",
        watchlist_items=list(watchlist_lookup.values()),
    )
    promotion = evaluate_promotion(
        conn,
        report_id=f"phase6_live_report__{ticker}",
        recommendation_id=f"phase6_live__{ticker}",
        from_status="observation_only",
        dashboard_summary=dashboard_summary,
        data_health_snapshot=data_health,
        evidence_check_snapshot=evidence_check,
        claim_graph_snapshot=claim_graph,
        valuation_snapshot=valuation,
        fundamentals_snapshot=fundamentals,
        consensus_proxy=proxy,
        bear_case=bear_case,
        risk_snapshot={"status": "pass"},
        lint_result={"max_severity": "info", "issues": []},
        write_ledger=True,
    )
    promotion_debugger = explain_promotion_result(
        ticker,
        promotion_to_dict(promotion),
        proxy=proxy,
        fundamentals=fundamentals,
        valuation=valuation,
        evidence_check=evidence_check,
        claim_graph=claim_graph,
        data_health=data_health,
    )
    candidate = build_recommendation_candidate(
        conn,
        recommendation_id=f"phase6_live__{ticker}",
        ticker=ticker,
        report=dashboard_summary,
        claim_graph=claim_graph,
        evidence_check=evidence_check,
        valuation_snapshot=valuation,
        consensus_proxy=proxy,
        bear_case=bear_case,
        risk_snapshot={"status": "pass"},
        portfolio_risk=portfolio_risk,
        market_signal={"signal": "positive"},
        promotion_result=promotion,
        write_ledger=True,
    )
    annotate_ledger(
        conn,
        f"phase6_live__{ticker}",
        {
            "live_e2e_run_id": run_id,
            "live_evidence_ids": [row["evidence_id"] for row in evidence_rows],
            "live_filing_evidence": live_filing_count,
            "live_news_evidence": live_news_count,
            "fundamentals_snapshot_id": fundamentals.get("snapshot_id"),
            "promotion_debugger": promotion_debugger,
            "portfolio_risk": portfolio_risk,
            "proxy_independent_source_count": proxy.get("independent_source_count"),
        },
    )
    return {
        "ticker": ticker,
        "market": market_for_ticker(ticker),
        "watchlist_item": watchlist_item,
        "status": candidate["status"],
        "action": candidate["action"],
        "promotion_allowed": promotion.allowed,
        "promotion": promotion_to_dict(promotion),
        "live_news_evidence": live_news_count,
        "live_filing_evidence": live_filing_count,
        "live_evidence_ids": [row["evidence_id"] for row in evidence_rows],
        "fundamentals_status": fundamentals.get("freshness_status"),
        "fundamentals_missing_fields": fundamentals.get("missing_fields") or [],
        "valuation_usage": valuation.get("allowed_usage"),
        "proxy_quality": proxy.get("proxy_quality"),
        "proxy_signal_count": proxy.get("proxy_signal_count"),
        "proxy_independent_source_count": proxy.get("independent_source_count"),
        "bear_case_strength": bear_case.get("bear_case_strength"),
        "portfolio_risk": portfolio_risk,
        "ledger_written": bool(conn.execute("SELECT 1 FROM decision_ledger WHERE recommendation_id=?", (f"phase6_live__{ticker}",)).fetchone()),
        "review_queue_visible": review_queue_visible(conn, f"phase6_live__{ticker}"),
        "missing_requirements": promotion.missing_requirements,
        "required_fixes": promotion.required_fixes,
        "promotion_debugger": promotion_debugger,
        "summary_bucket": None,
    }


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    pending = [item for item in results if item.get("status") == "pending_human_review"]
    pending_with_live = [item for item in pending if item.get("live_filing_evidence", 0) >= 1 or item.get("live_news_evidence", 0) >= 1]
    if pending_with_live:
        overall = "partial_pass"
    elif any(item.get("live_filing_evidence") or item.get("live_news_evidence") for item in results):
        overall = "live_data_available_needs_promotion_work"
    else:
        overall = "needs_attention"
    return {
        "overall_result": overall,
        "pending_human_review_count": len(pending),
        "pending_with_live_evidence_count": len(pending_with_live),
        "tickers_seen": len(results),
        "status_counts": {
            status: sum(1 for item in results if item.get("status") == status)
            for status in sorted({item.get("status") for item in results})
        },
    }


def bucket_result(item: dict[str, Any]) -> str:
    if item.get("status") == "pending_human_review":
        return "pending_human_review"
    if item.get("status") == "candidate_shadow":
        return "candidate_shadow"
    if item.get("portfolio_risk", {}).get("status") == "block":
        return "blocked_by_data"
    missing = {str(value) for value in item.get("missing_requirements") or []}
    if any(token in missing for token in {"daily_bar_fresh", "news_health", "relevant_filings_health", "fundamentals_snapshot", "fundamentals_snapshot_fresh_or_explainable"}):
        return "blocked_by_data"
    if any(token.startswith("lint:") or token in {"core_claim_evidence_quality", "two_independent_evidence_sources", "primary_evidence_for_fundamental_claims"} for token in missing):
        return "blocked_by_evidence"
    return "observation_only"


def compact_ticker_result(item: dict[str, Any]) -> dict[str, Any]:
    promotion = item.get("promotion") or {}
    portfolio_risk = item.get("portfolio_risk") or {}
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
        "fundamentals_missing_fields": item.get("fundamentals_missing_fields"),
        "valuation_usage": item.get("valuation_usage"),
        "proxy_quality": item.get("proxy_quality"),
        "proxy_signal_count": item.get("proxy_signal_count"),
        "proxy_independent_source_count": item.get("proxy_independent_source_count"),
        "bear_case_strength": item.get("bear_case_strength"),
        "portfolio_risk": {
            "status": portfolio_risk.get("status"),
            "recommended_action": portfolio_risk.get("recommended_action"),
            "recommended_position_pct": portfolio_risk.get("recommended_position_pct"),
            "recommended_max_position_pct": portfolio_risk.get("recommended_max_position_pct"),
            "blocking_factors": portfolio_risk.get("blocking_factors") or [],
            "minimum_fix_path": portfolio_risk.get("minimum_fix_path") or [],
        },
        "ledger_written": item.get("ledger_written"),
        "review_queue_visible": item.get("review_queue_visible"),
        "missing_requirements": item.get("missing_requirements") or promotion.get("missing_requirements") or [],
        "required_fixes": item.get("required_fixes") or promotion.get("required_fixes") or [],
        "promotion_debugger": {
            "blocking_factors": (item.get("promotion_debugger") or {}).get("blocking_factors") or [],
            "near_pass_items": (item.get("promotion_debugger") or {}).get("near_pass_items") or [],
            "minimum_fix_path": (item.get("promotion_debugger") or {}).get("minimum_fix_path") or [],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 6 multi-ticker live reliability")
    parser.add_argument("--watchlist", default=None)
    parser.add_argument("--tickers", default=None)
    parser.add_argument("--days", type=int, default=180)
    parser.add_argument("--skip-fetch", action="store_true")
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--full-output", action="store_true")
    args = parser.parse_args()

    if args.watchlist and args.tickers:
        raise SystemExit("Use either --watchlist or --tickers, not both")
    if args.watchlist:
        watchlist = load_watchlist_config(args.watchlist)
        tickers = [item["ticker"] for item in watchlist.get("tickers") or []]
        watchlist_name = watchlist.get("watchlist_id") or args.watchlist
    else:
        tickers = parse_tickers(args.tickers or "NVDA,AVGO,09988.HK,300308.SZ")
        watchlist = {
            "watchlist_id": "explicit",
            "name": "explicit",
            "tickers": [
                {"ticker": ticker, "market": market_for_ticker(ticker), "theme": "explicit", "sector": "explicit", "priority": "medium", "max_position_pct": 1.0, "data_requirements": []}
                for ticker in tickers
            ],
        }
        watchlist_name = "explicit"

    run_id = generate_execution_id("phase6_multi_ticker_live")
    filing_since_date = (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")
    news_since_date = (datetime.now() - timedelta(days=min(args.days, 30))).strftime("%Y-%m-%d")
    watchlist_lookup = watchlist_map(args.watchlist or "ai_core") if args.watchlist else {item["ticker"]: item for item in watchlist.get("tickers") or []}
    ingestion = {}
    if not args.skip_fetch:
        ticker_arg = ",".join(tickers)
        news_cmd = [
            sys.executable,
            str(Path(__file__).with_name("validate_live_news_ingestion.py")),
            "--tickers",
            ticker_arg,
            "--days",
            str(min(args.days, 30)),
            "--limit",
            "50",
            "--timeout",
            str(args.timeout),
        ]
        filings_cmd = [
            sys.executable,
            str(Path(__file__).with_name("validate_live_filings_ingestion.py")),
            "--tickers",
            ticker_arg,
            "--days",
            str(args.days),
            "--limit",
            "6",
            "--timeout",
            str(args.timeout),
        ]
        news_run = run_command(news_cmd, timeout=args.timeout)
        filings_run = run_command(filings_cmd, timeout=args.timeout)
        ingestion = {
            "news_run": news_run,
            "filings_run": filings_run,
            "news_payload": parse_json_stdout(news_run),
            "filings_payload": parse_json_stdout(filings_run),
        }
    conn = sqlite3.connect(args.db_path)
    conn.row_factory = sqlite3.Row
    try:
        ensure_decision_tables(conn)
        ensure_paper_portfolio_tables(conn)
        refresh_system_data_health(conn)
        update_news_health_rows(conn, stale_after_minutes=1440)
        update_filings_health_rows(conn, stale_after_minutes=max(args.days * 24 * 60, 1440))
        if not args.skip_fetch:
            ingestion["news_quality_metrics"] = update_evidence_quality_scores(conn, limit=500)
        results = [build_ticker_result(conn, ticker, run_id, filing_since_date, news_since_date, watchlist_lookup) for ticker in tickers]
        for item in results:
            item["summary_bucket"] = bucket_result(item)
        summary = summarize(results)
        payload = {
            "run_id": run_id,
            "generated_at": now_ts(),
            "mode": "phase6_multi_ticker_live",
            "watchlist_id": watchlist_name,
            "watchlist_meta": watchlist,
            "ingestion": compact_ingestion(ingestion),
            "summary": summary,
            "tickers": results,
        }
        register_snapshot(
            conn,
            entity_type="phase6_multi_ticker_live_validation",
            entity_id="latest",
            status=summary["overall_result"],
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    output = payload if args.full_output else {
        **payload,
        "tickers": [compact_ticker_result(item) for item in payload.get("tickers") or []],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2, default=str))
    return 0 if summary["overall_result"] in {"partial_pass", "live_data_available_needs_promotion_work"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
