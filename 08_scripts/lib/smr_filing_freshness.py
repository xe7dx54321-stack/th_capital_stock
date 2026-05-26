#!/usr/bin/env python3
"""Filing and evidence freshness diagnostics for Phase 19."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from smr_evidence_quality import parse_dt
from smr_paths import project_path


FRESHNESS_STATUSES = {"fresh", "usable_with_warning", "stale", "missing", "unknown"}
FINANCIAL_SECTIONS = {"income_statement", "balance_sheet", "cash_flow_statement", "financial_highlights"}


def loads_json(raw: str | None, fallback: Any) -> Any:
    if raw in (None, ""):
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def relation_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name=?", (name,)).fetchone()
    return bool(row)


def table_columns(conn: sqlite3.Connection, name: str) -> set[str]:
    if not relation_exists(conn, name):
        return set()
    return {row[1] for row in conn.execute(f"PRAGMA table_info({name})").fetchall()}


def normalize_ticker(ticker: str) -> str:
    return str(ticker or "").strip().upper()


def ticker_aliases(ticker: str) -> list[str]:
    ticker = normalize_ticker(ticker)
    aliases = [ticker]
    if "." in ticker:
        aliases.append(ticker.split(".", 1)[0])
    return list(dict.fromkeys(alias for alias in aliases if alias))


def freshness_status_for_date(value: Any, *, now: datetime | None = None) -> tuple[str, int | None]:
    now = now or datetime.now()
    anchor = parse_dt(value)
    if not anchor:
        return "missing", None
    stale_days = max(0, int((now - anchor).total_seconds() // 86400))
    if stale_days <= 180:
        return "fresh", stale_days
    if stale_days <= 365:
        return "usable_with_warning", stale_days
    return "stale", stale_days


def expected_latest_period(now: datetime | None = None) -> str:
    now = now or datetime.now()
    if now.month >= 11:
        return f"{now.year}Q3"
    if now.month >= 8:
        return f"{now.year}H1"
    if now.month >= 5:
        return f"{now.year}Q1"
    return f"FY{now.year - 1}"


def _evidence_ticker_predicate(ticker: str) -> tuple[str, list[Any]]:
    clauses = []
    params: list[Any] = []
    for alias in ticker_aliases(ticker):
        clauses.append("(metadata_json LIKE ? OR text_excerpt LIKE ? OR source_key LIKE ?)")
        params.extend([f"%{alias}%", f"%{alias}%", f"%{alias}%"])
    return " OR ".join(clauses or ["1=0"]), params


def latest_evidence_by_type(conn: sqlite3.Connection, ticker: str, source_type: str) -> dict[str, Any]:
    if not relation_exists(conn, "evidence_items"):
        return {}
    predicate, params = _evidence_ticker_predicate(ticker)
    row = conn.execute(
        f"""
        SELECT evidence_id, source_key, source_type, source_quality, source_status,
               published_at, ingested_at, created_at, text_excerpt, metadata_json
        FROM evidence_items
        WHERE source_type=? AND ({predicate})
        ORDER BY datetime(COALESCE(published_at, ingested_at, created_at)) DESC, id DESC
        LIMIT 1
        """,
        (source_type, *params),
    ).fetchone()
    if not row:
        return {}
    keys = [
        "evidence_id",
        "source_key",
        "source_type",
        "source_quality",
        "source_status",
        "published_at",
        "ingested_at",
        "created_at",
        "text_excerpt",
        "metadata_json",
    ]
    data = dict(zip(keys, row))
    data["metadata"] = loads_json(data.pop("metadata_json"), {})
    return data


def latest_financial_statement_evidence(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    if relation_exists(conn, "document_chunks"):
        rows = conn.execute(
            """
            SELECT chunk_id, evidence_id, chunk_section_type, created_at, metadata_json
            FROM document_chunks
            WHERE ticker=?
              AND evidence_id IS NOT NULL
              AND COALESCE(chunk_section_type, '') IN ('income_statement', 'balance_sheet', 'cash_flow_statement', 'financial_highlights')
            ORDER BY datetime(created_at) DESC, chunk_index ASC
            LIMIT 16
            """,
            (ticker,),
        ).fetchall()
        candidates = []
        for chunk_id, evidence_id, section_type, created_at, metadata_json in rows:
            metadata = loads_json(metadata_json, {})
            date_value = metadata.get("published_at") or metadata.get("filing_date") or created_at
            candidates.append(
                {
                    "chunk_id": chunk_id,
                    "evidence_id": evidence_id,
                    "source_type": "filing",
                    "source_quality": "primary",
                    "source_status": "active",
                    "published_at": date_value,
                    "ingested_at": created_at,
                    "created_at": created_at,
                    "section_type": section_type,
                    "metadata": metadata,
                }
            )
        if candidates:
            candidates.sort(key=lambda item: str(item.get("published_at") or item.get("created_at") or ""), reverse=True)
            return candidates[0]
    return latest_evidence_by_type(conn, ticker, "filing")


def latest_manifest_source(ticker: str) -> dict[str, Any]:
    path = project_path("00_control", "financial_statement_sources.json")
    if not Path(path).exists():
        return {}
    data = loads_json(Path(path).read_text(encoding="utf-8"), {})
    sources = ((data.get("sources") or {}).get(normalize_ticker(ticker)) or [])
    active = [item for item in sources if item.get("status", "active") == "active"]
    if not active:
        return {}
    active.sort(key=lambda item: str(item.get("published_at") or ""), reverse=True)
    return dict(active[0])


def build_filing_freshness(conn: sqlite3.Connection, ticker: str, *, now: datetime | None = None) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    now = now or datetime.now()
    latest = latest_financial_statement_evidence(conn, ticker)
    manifest = latest_manifest_source(ticker)
    if not latest and manifest:
        latest = {
            "evidence_id": None,
            "source_type": manifest.get("source_type"),
            "source_quality": "primary",
            "source_status": manifest.get("status") or "active",
            "published_at": manifest.get("published_at"),
            "metadata": manifest,
        }
    date_value = latest.get("published_at") or latest.get("ingested_at") or latest.get("created_at")
    status, stale_days = freshness_status_for_date(date_value, now=now)
    latest_type = latest.get("source_type") or (manifest.get("source_type") if manifest else None)
    source_quality = str(latest.get("source_quality") or "unknown")
    usable = status == "fresh" and source_quality in {"primary", "secondary"}
    if status == "usable_with_warning":
        usable = False
    filing = {
        "status": status,
        "latest_filing_type": latest_type,
        "latest_filing_date": date_value,
        "expected_latest_period": expected_latest_period(now),
        "actual_latest_period": (latest.get("metadata") or {}).get("period") or (latest.get("metadata") or {}).get("fiscal_period"),
        "stale_days": stale_days,
        "usable_for_promotion": bool(usable),
        "source_evidence_id": latest.get("evidence_id"),
        "source_quality": source_quality,
    }
    evidence_freshness = {
        "financial_statement_evidence": status,
        "news_evidence": freshness_status_for_date((latest_evidence_by_type(conn, ticker, "news") or {}).get("published_at"), now=now)[0],
        "proxy_evidence": freshness_status_for_date((latest_evidence_by_type(conn, ticker, "proxy") or {}).get("published_at"), now=now)[0]
        if latest_evidence_by_type(conn, ticker, "proxy")
        else "unknown",
    }
    if status in {"stale", "missing", "unknown"}:
        blocking_effect = "block_pending_review"
        next_fix = "refresh primary filing evidence or financial statement source manifest"
    elif status == "usable_with_warning":
        blocking_effect = "warning_supporting_only"
        next_fix = "refresh latest quarterly or annual filing before promotion"
    else:
        blocking_effect = "none"
        next_fix = None
    return {
        "ticker": ticker,
        "filing_freshness": filing,
        "evidence_freshness": evidence_freshness,
        "blocking_effect": blocking_effect,
        "next_fix": next_fix,
    }


def build_watchlist_freshness(conn: sqlite3.Connection, tickers: list[str], *, now: datetime | None = None) -> dict[str, Any]:
    rows = [build_filing_freshness(conn, ticker, now=now) for ticker in tickers]
    return {
        "summary": {
            "tickers_checked": len(rows),
            "fresh": sum(1 for row in rows if (row.get("filing_freshness") or {}).get("status") == "fresh"),
            "usable_with_warning": sum(1 for row in rows if (row.get("filing_freshness") or {}).get("status") == "usable_with_warning"),
            "stale": sum(1 for row in rows if (row.get("filing_freshness") or {}).get("status") == "stale"),
            "missing": sum(1 for row in rows if (row.get("filing_freshness") or {}).get("status") == "missing"),
            "blocking": sum(1 for row in rows if row.get("blocking_effect") == "block_pending_review"),
        },
        "ticker_results": rows,
    }
