#!/usr/bin/env python3
"""Validate live news ingestion into news_items/evidence_items."""

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
from smr_claim_graph import link_claim_evidence, upsert_claim
from smr_evidence_quality import update_evidence_quality_scores
from smr_news_ingestion import export_news_to_evidence, ingest_yahoo_finance_news, update_news_health_rows, upsert_news_item
from smr_paths import project_path
from smr_registry import register_snapshot
from smr_wiki import now_ts

SCRIPT_NAME = "validate_live_news_ingestion.py"
LIVE_NEWS_SOURCE_KEYS = {
    "eastmoney_news_article",
    "eastmoney_news_search",
    "news_article",
    "news_search",
    "public_analyst_signal_marketscreener",
    "yahoo_finance_rss",
}


def parse_tickers(raw: str | None) -> list[str]:
    return [item.strip() for item in str(raw or "").split(",") if item.strip()]


def market_for_ticker(ticker: str) -> str:
    if ticker.endswith((".SZ", ".SH", ".BJ")):
        return "A"
    if ticker.endswith(".HK"):
        return "H"
    return "US"


def run_command(command: list[str], timeout: int = 180) -> dict[str, Any]:
    result = subprocess.run(command, cwd=project_path(), capture_output=True, text=True, timeout=timeout, check=False)
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": (result.stdout or "")[-3000:],
        "stderr": (result.stderr or "")[-3000:],
    }


def run_existing_connectors(tickers: list[str], limit: int, timeout: int) -> list[dict[str, Any]]:
    results = []
    a_tickers = [ticker for ticker in tickers if market_for_ticker(ticker) == "A"]
    for ticker in a_tickers:
        results.append(
            run_command(
                [
                    sys.executable,
                    str(project_path("08_scripts", "wiki", "fetch_eastmoney_news_search.py")),
                    "--ts-code",
                    ticker,
                    "--per-symbol-limit",
                    str(limit),
                    "--limit",
                    "1",
                ],
                timeout=timeout,
            )
        )
        results.append(
            run_command(
                [
                    sys.executable,
                    str(project_path("08_scripts", "wiki", "fetch_eastmoney_news_articles.py")),
                    "--ts-code",
                    ticker,
                    "--article-limit",
                    str(min(limit, 3)),
                    "--limit",
                    "1",
                ],
                timeout=timeout,
            )
        )
    if a_tickers:
        for script in ("build_source_manifest.py",):
            results.append(run_command([sys.executable, str(project_path("08_scripts", "wiki", script))], timeout=timeout))
        results.append(
            run_command(
                [
                    sys.executable,
                    str(project_path("08_scripts", "events", "normalize_market_events.py")),
                    "--family",
                    "news",
                    "--days-back",
                    "30",
                ],
                timeout=timeout,
            )
        )
    return results


def ingest_live_news_from_manifest(conn: sqlite3.Connection, tickers: list[str], since_date: str, limit: int) -> dict[str, Any]:
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='source_manifest'").fetchone():
        return {"inserted": 0, "deduped": 0, "scanned": 0, "errors": ["source_manifest_missing"]}
    rows = conn.execute(
        """
        SELECT source_id, entity_id, title, metadata_json, updated_at, created_at
        FROM source_manifest
        WHERE source_type='external_source_snapshot'
          AND (metadata_json LIKE '%news%' OR source_id LIKE '%news%')
        ORDER BY datetime(COALESCE(updated_at, created_at)) DESC
        LIMIT ?
        """,
        (limit * 20,),
    ).fetchall()
    inserted = 0
    deduped = 0
    scanned = 0
    errors: list[str] = []
    wanted = set(tickers)
    for row in rows:
        metadata = json.loads(row[3] or "{}")
        ticker = row[1]
        if wanted and ticker not in wanted:
            continue
        scanned += 1
        published_at = metadata.get("published_at") or metadata.get("notice_date") or metadata.get("fetched_at") or row[4] or row[5]
        if since_date and str(published_at or "")[:10] < since_date:
            continue
        try:
            result = upsert_news_item(
                conn,
                {
                    "news_id": row[0],
                    "source_key": metadata.get("source_kind") or "live_news",
                    "source_name": metadata.get("provider") or metadata.get("source_domain"),
                    "title": row[2],
                    "body": row[2],
                    "url": metadata.get("source_url"),
                    "published_at": published_at,
                    "tickers": [ticker],
                    "market": market_for_ticker(ticker),
                    "credibility": "medium",
                    "metadata": {**metadata, "live": True, "source_manifest_id": row[0]},
                },
            )
            if result.get("deduped"):
                deduped += 1
            else:
                inserted += 1
        except Exception as exc:
            errors.append(f"{row[0]}: {exc}")
    return {"inserted": inserted, "deduped": deduped, "scanned": scanned, "errors": errors}


def claim_links_for_ticker(conn: sqlite3.Connection, ticker: str, evidence_ids: list[str]) -> int:
    claim_id = f"claim_live_news_{ticker.replace('.', '_')}"
    upsert_claim(
        conn,
        {
            "claim_id": claim_id,
            "report_id": "live_news_validation",
            "recommendation_id": f"live_news__{ticker}",
            "ticker": ticker,
            "theme": "live_news_validation",
            "claim_text": f"{ticker} has live news evidence available for opportunity radar.",
            "claim_type": "news",
            "importance": "supporting",
            "stance": "base",
            "confidence": 0.4,
            "metadata": {"validator": SCRIPT_NAME},
        },
    )
    linked = 0
    for evidence_id in evidence_ids[:5]:
        link_claim_evidence(conn, claim_id, evidence_id, "contextual", 0.45, "live news validation link")
        linked += 1
    return linked


def _loads_json(raw: str | None, fallback: Any) -> Any:
    if raw in (None, ""):
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def _ticker_matches(ticker: str, metadata: dict[str, Any], tickers: list[Any] | None = None) -> bool:
    values = {str(item).upper() for item in (tickers or []) if item}
    for key in ("ticker", "symbol", "ts_code"):
        if metadata.get(key):
            values.add(str(metadata[key]).upper())
    for item in metadata.get("tickers") or []:
        if item:
            values.add(str(item).upper())
    return ticker.upper() in values


def _is_live_metadata(metadata: dict[str, Any]) -> bool:
    return metadata.get("live") is True


def summarize_ticker(conn: sqlite3.Connection, ticker: str, since_date: str) -> dict[str, Any]:
    raw_rows = conn.execute(
        """
        SELECT news_id, source_key, title, url, published_at, ingested_at, metadata_json, tickers_json
        FROM news_items
        WHERE source_key IN ({})
          AND metadata_json LIKE '%"live"%'
          AND substr(COALESCE(published_at, ingested_at), 1, 10) >= ?
        ORDER BY datetime(COALESCE(published_at, ingested_at)) DESC
        """.format(",".join("?" for _ in LIVE_NEWS_SOURCE_KEYS)),
        (*sorted(LIVE_NEWS_SOURCE_KEYS), since_date),
    ).fetchall()
    rows = []
    news_ids = set()
    for row in raw_rows:
        metadata = _loads_json(row[6], {})
        tickers = _loads_json(row[7], [])
        if not _is_live_metadata(metadata) or not _ticker_matches(ticker, metadata, tickers):
            continue
        rows.append(row)
        news_ids.add(row[0])

    raw_evidence_rows = conn.execute(
        """
        SELECT evidence_id, source_key, published_at, ingested_at, metadata_json
        FROM evidence_items
        WHERE source_type='news'
          AND source_key IN ({})
          AND metadata_json LIKE '%"live"%'
          AND substr(COALESCE(published_at, ingested_at), 1, 10) >= ?
        ORDER BY id DESC
        """.format(",".join("?" for _ in LIVE_NEWS_SOURCE_KEYS)),
        (*sorted(LIVE_NEWS_SOURCE_KEYS), since_date),
    ).fetchall()
    evidence_rows = []
    for row in raw_evidence_rows:
        metadata = _loads_json(row[4], {})
        if not _is_live_metadata(metadata):
            continue
        if metadata.get("news_id") not in news_ids:
            continue
        if not _ticker_matches(ticker, metadata, metadata.get("tickers") or []):
            continue
        evidence_rows.append(row)
    evidence_ids = [row[0] for row in evidence_rows]
    linked = claim_links_for_ticker(conn, ticker, evidence_ids) if evidence_ids else 0
    source_breakdown = Counter(row[1] for row in rows)
    unique_urls = {row[3] for row in rows if row[3]}
    has_real_url = any(row[3] and str(row[3]).startswith("http") for row in rows)
    has_published = any(row[4] for row in rows)
    return {
        "ticker": ticker,
        "market": market_for_ticker(ticker),
        "news_items_found": len(rows),
        "deduped_items": len(unique_urls) or len(news_ids),
        "freshness": "fresh" if rows else "missing",
        "evidence_items_created": len(evidence_ids),
        "claim_links_created": linked,
        "source_breakdown": dict(source_breakdown),
        "has_real_url": has_real_url,
        "has_published_at": has_published,
        "errors": [] if rows else ["no_live_news_items_found"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate live news ingestion")
    parser.add_argument("--tickers", default="NVDA,09988.HK,000001.SZ")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--skip-fetch", action="store_true")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()

    tickers = parse_tickers(args.tickers)
    since_date = (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")
    connector_runs = [] if args.skip_fetch else run_existing_connectors(tickers, args.limit, args.timeout)
    conn = sqlite3.connect(DB_PATH)
    try:
        manifest_metrics = ingest_live_news_from_manifest(conn, tickers, since_date, args.limit)
        yahoo_metrics = ingest_yahoo_finance_news(conn, tickers, limit=args.limit, timeout=min(args.timeout, 60))
        ingest_metrics = {"manifest": manifest_metrics, "yahoo_finance_rss": yahoo_metrics}
        evidence_metrics = export_news_to_evidence(conn, limit=args.limit, source_keys=LIVE_NEWS_SOURCE_KEYS)
        quality_metrics = update_evidence_quality_scores(conn, limit=args.limit * 4)
        health = update_news_health_rows(conn, stale_after_minutes=1440, source_keys=LIVE_NEWS_SOURCE_KEYS)
        results = [summarize_ticker(conn, ticker, since_date) for ticker in tickers]
        payload = {
            "generated_at": now_ts(),
            "since_date": since_date,
            "status": "partial_pass" if any(item["news_items_found"] for item in results) else "needs_attention",
            "connector_runs": connector_runs,
            "ingest_metrics": ingest_metrics,
            "evidence_metrics": evidence_metrics,
            "quality_metrics": quality_metrics,
            "health": health,
            "results": results,
        }
        register_snapshot(
            conn,
            entity_type="live_news_ingestion_validation",
            entity_id="latest",
            status=payload["status"],
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
