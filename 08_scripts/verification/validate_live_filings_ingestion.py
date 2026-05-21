#!/usr/bin/env python3
"""Validate live filings ingestion into filing_documents/evidence_items."""

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
from smr_filings_ingestion import export_filings_to_evidence, update_filings_health_rows
from smr_paths import project_path
from smr_registry import register_snapshot
from smr_wiki import now_ts

SCRIPT_NAME = "validate_live_filings_ingestion.py"


def parse_tickers(raw: str | None) -> list[str]:
    return [item.strip() for item in str(raw or "").split(",") if item.strip()]


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
            cwd=project_path(),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "command": command,
            "returncode": result.returncode,
            "stdout": (result.stdout or "")[-3000:],
            "stderr": (result.stderr or "")[-3000:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "returncode": 124,
            "stdout": (exc.stdout or "")[-3000:] if isinstance(exc.stdout, str) else "",
            "stderr": f"timeout_after_{timeout}s",
        }


def run_existing_connectors(tickers: list[str], days: int, limit: int, timeout: int) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for ticker in tickers:
        market = market_for_ticker(ticker)
        if market == "US":
            results.append(
                run_command(
                    [
                        sys.executable,
                        str(project_path("08_scripts", "wiki", "fetch_sec_official_materials.py")),
                        "--symbol",
                        ticker,
                        "--days-back",
                        str(days),
                        "--max-filings",
                        str(max(1, min(limit, 6))),
                        "--max-materials",
                        "2",
                    ],
                    timeout=timeout,
                )
            )
        elif market == "H":
            results.append(
                run_command(
                    [
                        sys.executable,
                        str(project_path("08_scripts", "wiki", "fetch_hkex_announcements.py")),
                        "--ts-code",
                        ticker,
                        "--days-back",
                        str(days),
                        "--per-symbol-limit",
                        str(max(1, min(limit, 5))),
                    ],
                    timeout=timeout,
                )
            )
        else:
            results.append(
                run_command(
                    [
                        sys.executable,
                        str(project_path("08_scripts", "wiki", "fetch_cninfo_announcements.py")),
                        "--ts-code",
                        ticker,
                        "--days-back",
                        str(days),
                        "--per-symbol-limit",
                        str(max(1, min(limit, 5))),
                    ],
                    timeout=timeout,
                )
            )
    results.append(run_command([sys.executable, str(project_path("08_scripts", "wiki", "build_source_manifest.py"))], timeout=timeout))
    results.append(
        run_command(
            [
                sys.executable,
                str(project_path("08_scripts", "events", "normalize_market_events.py")),
                "--family",
                "announcement",
                "--days-back",
                str(days),
            ],
            timeout=timeout,
        )
    )
    results.append(
        run_command(
            [
                sys.executable,
                str(project_path("08_scripts", "jobs", "ingest_filings.py")),
                "--from-manifest",
                "--export-evidence",
                "--limit",
                str(max(limit * 20, 100)),
            ],
            timeout=timeout,
        )
    )
    return results


def claim_links_for_ticker(conn: sqlite3.Connection, ticker: str, evidence_ids: list[str]) -> int:
    claim_id = f"claim_live_filing_{ticker.replace('.', '_')}"
    upsert_claim(
        conn,
        {
            "claim_id": claim_id,
            "report_id": "live_filings_validation",
            "recommendation_id": f"live_filings__{ticker}",
            "ticker": ticker,
            "theme": "live_filings_validation",
            "claim_text": f"{ticker} has live filing evidence available for fundamental research.",
            "claim_type": "filing",
            "importance": "core",
            "stance": "base",
            "confidence": 0.55,
            "metadata": {"validator": SCRIPT_NAME},
        },
    )
    linked = 0
    for evidence_id in evidence_ids[:6]:
        link_claim_evidence(conn, claim_id, evidence_id, "supports", 0.62, "live filing validation link")
        linked += 1
    return linked


def summarize_ticker(conn: sqlite3.Connection, ticker: str, since_date: str) -> dict[str, Any]:
    filing_rows = conn.execute(
        """
        SELECT filing_id, source_key, filing_type, title, published_at, ingested_at,
               source_url, parse_status, metadata_json
        FROM filing_documents
        WHERE ticker=?
          AND metadata_json LIKE '%"live"%'
          AND substr(COALESCE(published_at, ingested_at), 1, 10) >= ?
        ORDER BY datetime(COALESCE(published_at, ingested_at)) DESC, id DESC
        """,
        (ticker, since_date),
    ).fetchall()
    filing_ids = [row[0] for row in filing_rows]
    evidence_rows = conn.execute(
        """
        SELECT evidence_id, source_key
        FROM evidence_items
        WHERE source_type='filing'
          AND metadata_json LIKE ?
          AND metadata_json LIKE '%"live"%'
        ORDER BY id DESC
        """,
        (f"%{ticker}%",),
    ).fetchall()
    evidence_ids = [row[0] for row in evidence_rows]
    chunk_count = 0
    if filing_ids:
        placeholders = ",".join("?" for _ in filing_ids)
        row = conn.execute(
            f"SELECT COUNT(*) FROM document_chunks WHERE document_id IN ({placeholders})",
            tuple(filing_ids),
        ).fetchone()
        chunk_count = int(row[0] or 0)
    linked = claim_links_for_ticker(conn, ticker, evidence_ids) if evidence_ids else 0
    source_breakdown = Counter(row[1] for row in filing_rows)
    filing_types = sorted({row[2] for row in filing_rows if row[2]})
    parsed_success = sum(1 for row in filing_rows if row[7] in {"parsed", "metadata_only"})
    has_real_url = any(row[6] and str(row[6]).startswith("http") for row in filing_rows)
    return {
        "ticker": ticker,
        "market": market_for_ticker(ticker),
        "filings_found": len(filing_rows),
        "filing_types": filing_types,
        "parsed_success": parsed_success,
        "chunks_created": chunk_count,
        "evidence_items_created": len(evidence_ids),
        "primary_claim_links": linked,
        "source_breakdown": dict(source_breakdown),
        "has_real_url": has_real_url,
        "freshness": "fresh" if filing_rows else "missing",
        "errors": [] if filing_rows else ["no_live_filings_found"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate live filings ingestion")
    parser.add_argument("--tickers", default="NVDA,09988.HK,000001.SZ")
    parser.add_argument("--days", type=int, default=180)
    parser.add_argument("--limit", type=int, default=6)
    parser.add_argument("--skip-fetch", action="store_true")
    parser.add_argument("--timeout", type=int, default=240)
    args = parser.parse_args()

    tickers = parse_tickers(args.tickers)
    since_date = (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")
    connector_runs = [] if args.skip_fetch else run_existing_connectors(tickers, args.days, args.limit, args.timeout)
    conn = sqlite3.connect(DB_PATH)
    try:
        evidence_metrics = export_filings_to_evidence(conn, limit=max(args.limit * 20, 100))
        quality_metrics = update_evidence_quality_scores(conn, limit=max(args.limit * 40, 200))
        health = update_filings_health_rows(conn, stale_after_minutes=max(args.days * 24 * 60, 1440))
        results = [summarize_ticker(conn, ticker, since_date) for ticker in tickers]
        payload = {
            "generated_at": now_ts(),
            "since_date": since_date,
            "connector_runs": connector_runs,
            "evidence_metrics": evidence_metrics,
            "quality_metrics": quality_metrics,
            "health": health,
            "results": results,
        }
        register_snapshot(
            conn,
            entity_type="live_filings_ingestion_validation",
            entity_id="latest",
            status="partial_pass" if any(item["filings_found"] for item in results) else "needs_attention",
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    print(
        json.dumps(
            {
                "generated_at": payload["generated_at"],
                "since_date": payload["since_date"],
                "status": "partial_pass" if any(item["filings_found"] for item in results) else "needs_attention",
                "results": results,
                "connector_returncodes": [item.get("returncode") for item in connector_runs],
                "evidence_metrics": evidence_metrics,
                "quality_metrics": quality_metrics,
                "health_overall_status": health.get("overall_status"),
            },
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
