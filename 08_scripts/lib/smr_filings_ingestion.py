#!/usr/bin/env python3
"""Filings ingestion, freshness, chunking, and primary evidence export."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from datetime import datetime
from typing import Any

from smr_claim_graph import ensure_claim_graph_tables, upsert_evidence
from smr_paths import normalize_project_path, relative_to_project
from smr_wiki import generate_execution_id, loads_json, now_ts, read_markdown

FILING_SOURCE_KINDS = {
    "announcement",
    "cninfo_announcement",
    "hkex_announcement",
    "sec_filing_document",
    "sec_earnings_material",
    "official_ir_material",
    "sec_submissions_json",
    "official_ir_page_discovery",
    "ir_material_pdf",
    "ir_material_page",
}

PRIMARY_SOURCE_KEYS = {
    "cninfo_announcement",
    "hkex_announcement",
    "sec_filing_document",
    "sec_earnings_material",
    "official_ir_material",
}


def ensure_filings_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS filing_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filing_id TEXT UNIQUE NOT NULL,
            ticker TEXT,
            market TEXT,
            company_name TEXT,
            filing_type TEXT,
            title TEXT,
            published_at TEXT,
            ingested_at TEXT NOT NULL,
            source_key TEXT,
            source_url TEXT,
            raw_doc_path TEXT,
            parsed_text_path TEXT,
            parse_status TEXT,
            language TEXT,
            metadata_json TEXT NOT NULL DEFAULT '{}'
        );

        CREATE INDEX IF NOT EXISTS idx_filing_documents_ticker_date
        ON filing_documents(ticker, published_at DESC);

        CREATE INDEX IF NOT EXISTS idx_filing_documents_market_source
        ON filing_documents(market, source_key, published_at DESC);

        CREATE TABLE IF NOT EXISTS document_chunks (
            chunk_id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            document_type TEXT NOT NULL,
            source_key TEXT,
            ticker TEXT,
            market TEXT,
            section_name TEXT,
            chunk_index INTEGER NOT NULL,
            text TEXT NOT NULL,
            evidence_id TEXT,
            created_at TEXT NOT NULL,
            metadata_json TEXT NOT NULL DEFAULT '{}'
        );

        CREATE INDEX IF NOT EXISTS idx_document_chunks_document
        ON document_chunks(document_id, chunk_index);
        """
    )


def relation_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name=?",
        (name,),
    ).fetchone()
    return bool(row)


def table_columns(conn: sqlite3.Connection, name: str) -> set[str]:
    if not relation_exists(conn, name):
        return set()
    return {row[1] for row in conn.execute(f"PRAGMA table_info({name})").fetchall()}


def parse_dt(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    text = text.replace("T", " ")[:19]
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[: len(fmt)], fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def normalize_dt(value: Any) -> str | None:
    dt_value = parse_dt(value)
    if not dt_value:
        return None
    return dt_value.strftime("%Y-%m-%d %H:%M:%S")


def normalize_text(value: Any, limit: int | None = None) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit is not None and len(text) > limit:
        return text[:limit].rstrip()
    return text


def stable_hash(*parts: Any) -> str:
    raw = "|".join(normalize_text(part).lower() for part in parts if part not in (None, ""))
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def infer_market(ticker: str | None, fallback: str | None = None) -> str:
    fallback_text = str(fallback or "").strip().upper()
    if fallback_text in {"A", "CN", "H", "HK", "US"}:
        return {"CN": "A", "HK": "H"}.get(fallback_text, fallback_text)
    text = str(ticker or "").upper()
    if text.endswith((".SZ", ".SH", ".BJ")):
        return "A"
    if text.endswith(".HK"):
        return "H"
    if text:
        return "US"
    return "global"


def infer_filing_type(title: str | None, source_key: str | None = None) -> str:
    text = normalize_text(title).lower()
    source = str(source_key or "")
    if "10-k" in text:
        return "sec_10k"
    if "10-q" in text:
        return "sec_10q"
    if "8-k" in text:
        return "sec_8k"
    if "annual" in text or "年报" in text:
        return "annual_report"
    if "quarter" in text or "季报" in text:
        return "quarterly_report"
    if "interim" in text or "中报" in text or "中期" in text:
        return "interim_report"
    if "earnings" in text or "业绩" in text or "results" in text:
        return "earnings_release"
    if "guidance" in text or "指引" in text:
        return "guidance"
    if "contract" in text or "合同" in text:
        return "material_contract"
    if "buyback" in text or "repurchase" in text or "回购" in text:
        return "share_buyback"
    if "dividend" in text or "分红" in text:
        return "dividend"
    if "risk" in text or "风险" in text:
        return "risk_disclosure"
    if source == "hkex_announcement":
        return "hkex_announcement"
    if source == "cninfo_announcement":
        return "cn_exchange_announcement"
    return "other"


def normalize_filing_document(raw: dict[str, Any]) -> dict[str, Any]:
    title = normalize_text(raw.get("title"), limit=500)
    if not title:
        raise ValueError("filing title is required")
    source_key = normalize_text(raw.get("source_key") or raw.get("source_kind") or "official_filing", limit=120)
    ticker = normalize_text(raw.get("ticker") or raw.get("entity_id"), limit=80)
    published_at = normalize_dt(raw.get("published_at") or raw.get("publish_time") or raw.get("created_at") or raw.get("updated_at"))
    source_url = normalize_text(raw.get("source_url") or raw.get("url"), limit=1200)
    filing_id = raw.get("filing_id") or f"filing_{stable_hash(source_key, ticker, title, published_at or source_url)[:20]}"
    return {
        "filing_id": filing_id,
        "ticker": ticker,
        "market": infer_market(ticker, raw.get("market")),
        "company_name": normalize_text(raw.get("company_name") or raw.get("company"), limit=240),
        "filing_type": raw.get("filing_type") or infer_filing_type(title, source_key),
        "title": title,
        "published_at": published_at,
        "ingested_at": normalize_dt(raw.get("ingested_at")) or now_ts(),
        "source_key": source_key,
        "source_url": source_url,
        "raw_doc_path": normalize_text(raw.get("raw_doc_path"), limit=1200),
        "parsed_text_path": normalize_text(raw.get("parsed_text_path") or raw.get("source_path"), limit=1200),
        "parse_status": raw.get("parse_status") or "parsed",
        "language": raw.get("language") or ("zh" if re.search(r"[\u4e00-\u9fff]", title) else "en"),
        "metadata": raw.get("metadata") or {},
        "body": normalize_text(raw.get("body") or "", limit=20000),
    }


def upsert_filing_document(conn: sqlite3.Connection, item: dict[str, Any]) -> dict[str, Any]:
    ensure_filings_tables(conn)
    normalized = normalize_filing_document(item)
    conn.execute(
        """
        INSERT INTO filing_documents (
            filing_id, ticker, market, company_name, filing_type, title, published_at, ingested_at,
            source_key, source_url, raw_doc_path, parsed_text_path, parse_status, language, metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(filing_id) DO UPDATE SET
            ticker=excluded.ticker,
            market=excluded.market,
            company_name=excluded.company_name,
            filing_type=excluded.filing_type,
            title=excluded.title,
            published_at=excluded.published_at,
            ingested_at=excluded.ingested_at,
            source_key=excluded.source_key,
            source_url=excluded.source_url,
            raw_doc_path=excluded.raw_doc_path,
            parsed_text_path=excluded.parsed_text_path,
            parse_status=excluded.parse_status,
            language=excluded.language,
            metadata_json=excluded.metadata_json
        """,
        (
            normalized["filing_id"],
            normalized["ticker"],
            normalized["market"],
            normalized["company_name"],
            normalized["filing_type"],
            normalized["title"],
            normalized["published_at"],
            normalized["ingested_at"],
            normalized["source_key"],
            normalized["source_url"],
            normalized["raw_doc_path"],
            normalized["parsed_text_path"],
            normalized["parse_status"],
            normalized["language"],
            json.dumps(normalized["metadata"], ensure_ascii=False, sort_keys=True),
        ),
    )
    if normalized.get("body"):
        upsert_document_chunks(conn, normalized, normalized["body"])
    return normalized


def count_live_filings_for_ticker(conn: sqlite3.Connection, ticker: str, since_date: str | None = None) -> int:
    ensure_filings_tables(conn)
    params: list[Any] = [ticker]
    where = "ticker=?"
    if since_date:
        where += " AND substr(COALESCE(published_at, ingested_at), 1, 10) >= ?"
        params.append(since_date)
    row = conn.execute(
        f"""
        SELECT COUNT(*)
        FROM filing_documents
        WHERE {where}
          AND metadata_json LIKE '%"live"%'
        """,
        tuple(params),
    ).fetchone()
    return int(row[0] or 0)


def split_chunks(text: str, max_chars: int = 900, limit: int = 20) -> list[str]:
    clean = normalize_text(text)
    if not clean:
        return []
    chunks = []
    for start in range(0, len(clean), max_chars):
        chunk = clean[start : start + max_chars].strip()
        if len(chunk) >= 40:
            chunks.append(chunk)
        if len(chunks) >= limit:
            break
    return chunks


def upsert_document_chunks(conn: sqlite3.Connection, document: dict[str, Any], body_text: str) -> int:
    ensure_filings_tables(conn)
    chunks = split_chunks(body_text)
    for index, chunk in enumerate(chunks, start=1):
        chunk_id = "chunk_" + stable_hash(document["filing_id"], index, chunk)[:20]
        evidence_id = "ev_" + stable_hash(document["source_key"], document["filing_id"], chunk)[:16]
        conn.execute(
            """
            INSERT OR REPLACE INTO document_chunks (
                chunk_id, document_id, document_type, source_key, ticker, market, section_name,
                chunk_index, text, evidence_id, created_at, metadata_json
            )
            VALUES (?, ?, 'filing', ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                chunk_id,
                document["filing_id"],
                document["source_key"],
                document["ticker"],
                document["market"],
                "body",
                index,
                chunk,
                evidence_id,
                now_ts(),
                json.dumps({"filing_type": document.get("filing_type")}, ensure_ascii=False, sort_keys=True),
            ),
        )
    return len(chunks)


def manifest_row_to_filing(row: sqlite3.Row | tuple[Any, ...], columns: list[str]) -> dict[str, Any] | None:
    data = dict(row) if isinstance(row, sqlite3.Row) else {columns[index]: row[index] for index in range(len(row))}
    metadata = loads_json(data.get("metadata_json"), {})
    source_kind = metadata.get("source_kind") or data.get("source_type")
    provider = str(metadata.get("provider") or "").lower()
    if source_kind == "announcement" and provider == "cninfo":
        source_kind = "cninfo_announcement"
    elif source_kind == "announcement" and provider == "hkexnews":
        source_kind = "hkex_announcement"
    if source_kind not in FILING_SOURCE_KINDS and "announcement" not in str(source_kind) and "filing" not in str(source_kind):
        return None
    source_path = normalize_project_path(data.get("source_path")) if data.get("source_path") else None
    body = read_markdown(source_path) if source_path else ""
    return {
        "filing_id": data.get("source_id"),
        "ticker": data.get("entity_id") if data.get("entity_type") == "stock" else None,
        "market": metadata.get("market"),
        "company_name": metadata.get("company_name"),
        "filing_type": metadata.get("filing_type") or infer_filing_type(data.get("title"), source_kind),
        "title": data.get("title"),
        "published_at": metadata.get("published_at") or metadata.get("notice_date") or data.get("created_at") or data.get("updated_at"),
        "ingested_at": data.get("updated_at") or now_ts(),
        "source_key": source_kind,
        "source_url": metadata.get("source_url"),
        "raw_doc_path": metadata.get("raw_rel_path"),
        "parsed_text_path": relative_to_project(source_path) if source_path else data.get("source_rel_path"),
        "parse_status": "parsed" if body else "metadata_only",
        "body": body,
        "metadata": {
            **metadata,
            "live": bool(metadata.get("live", True)),
            "source_id": data.get("source_id"),
            "source_rel_path": relative_to_project(source_path) if source_path else data.get("source_rel_path"),
        },
    }


def ingest_filings_from_manifest(conn: sqlite3.Connection, limit: int | None = None) -> dict[str, Any]:
    ensure_filings_tables(conn)
    if not relation_exists(conn, "source_manifest"):
        return {"inserted": 0, "skipped": 0, "chunks": 0, "scanned": 0, "reason": "source_manifest_missing"}
    wanted = [
        "source_id",
        "source_type",
        "entity_type",
        "entity_id",
        "title",
        "source_path",
        "source_rel_path",
        "status",
        "created_at",
        "updated_at",
        "metadata_json",
    ]
    available = table_columns(conn, "source_manifest")
    columns = [column for column in wanted if column in available]
    if "metadata_json" not in columns:
        return {"inserted": 0, "skipped": 0, "chunks": 0, "scanned": 0, "reason": "metadata_json_missing"}
    rows = conn.execute(
        f"""
        SELECT {', '.join(columns)}
        FROM source_manifest
        WHERE source_type='external_source_snapshot'
           OR metadata_json LIKE '%announcement%'
           OR metadata_json LIKE '%filing%'
           OR source_id LIKE '%announcement%'
           OR source_id LIKE '%filing%'
        ORDER BY datetime(COALESCE(updated_at, created_at)) DESC, source_id DESC
        LIMIT ?
        """,
        (limit or 500,),
    ).fetchall()
    inserted = 0
    skipped = 0
    chunks = 0
    for row in rows:
        item = manifest_row_to_filing(row, columns)
        if not item:
            skipped += 1
            continue
        try:
            result = upsert_filing_document(conn, item)
        except ValueError:
            skipped += 1
            continue
        inserted += 1
        chunk_count = conn.execute(
            "SELECT COUNT(*) FROM document_chunks WHERE document_id=?",
            (result["filing_id"],),
        ).fetchone()[0]
        chunks += chunk_count
    return {"inserted": inserted, "skipped": skipped, "chunks": chunks, "scanned": len(rows)}


def watchlist_tickers(conn: sqlite3.Connection) -> set[str]:
    candidates = []
    if relation_exists(conn, "stock_pool_current") and "ts_code" in table_columns(conn, "stock_pool_current"):
        candidates.append("SELECT ts_code FROM stock_pool_current")
    elif relation_exists(conn, "stock_pool") and "ts_code" in table_columns(conn, "stock_pool"):
        candidates.append("SELECT ts_code FROM stock_pool WHERE COALESCE(status, 'active')='active'")
    tickers: set[str] = set()
    for query in candidates:
        for row in conn.execute(query).fetchall():
            if row[0]:
                tickers.add(str(row[0]))
    return tickers


def latest_filings_by_scope(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    ensure_filings_tables(conn)
    rows = conn.execute(
        """
        SELECT
            COALESCE(source_key, 'filings') AS source_key,
            COALESCE(market, 'global') AS market,
            COALESCE(ticker, 'all') AS ticker,
            MAX(published_at) AS last_published_at,
            MAX(ingested_at) AS last_ingested_at,
            COUNT(*) AS document_count
        FROM filing_documents
        GROUP BY COALESCE(source_key, 'filings'), COALESCE(market, 'global'), COALESCE(ticker, 'all')
        ORDER BY source_key, market, ticker
        """
    ).fetchall()
    source_rows = [
        {
            "source_key": row[0],
            "market": row[1],
            "ticker": row[2],
            "scope": "ticker" if row[2] != "all" else "market",
            "last_published_at": row[3],
            "last_ingested_at": row[4],
            "document_count": row[5],
        }
        for row in rows
    ]
    if not source_rows:
        legacy_latest = None
        if relation_exists(conn, "market_event"):
            columns = table_columns(conn, "market_event")
            conditions = []
            params: list[Any] = []
            if "event_family" in columns:
                conditions.append("event_family LIKE ?")
                params.append("%company_event%")
            if "source_kind" in columns:
                conditions.append("source_kind IN (?, ?, ?, ?, ?)")
                params.extend(
                    [
                        "announcement",
                        "cninfo_announcement",
                        "sec_filing_document",
                        "sec_earnings_material",
                        "official_ir_material",
                    ]
                )
            if conditions:
                timestamp_expr = "created_at"
                if "publish_time" in columns and "created_at" in columns:
                    timestamp_expr = "COALESCE(publish_time, created_at)"
                elif "publish_time" in columns:
                    timestamp_expr = "publish_time"
                row = conn.execute(
                    f"SELECT MAX({timestamp_expr}) FROM market_event WHERE " + " OR ".join(f"({item})" for item in conditions),
                    tuple(params),
                ).fetchone()
                legacy_latest = row[0] if row else None
        if legacy_latest is None and relation_exists(conn, "source_manifest"):
            columns = table_columns(conn, "source_manifest")
            if {"source_type", "updated_at"}.issubset(columns):
                row = conn.execute(
                    """
                    SELECT MAX(updated_at)
                    FROM source_manifest
                    WHERE source_type IN (?, ?, ?, ?, ?)
                       OR metadata_json LIKE '%announcement%'
                       OR metadata_json LIKE '%filing%'
                    """,
                    ("announcement", "cninfo_announcement", "sec_filing_document", "sec_earnings_material", "official_ir_material"),
                ).fetchone()
                legacy_latest = row[0] if row else None
        if legacy_latest:
            source_rows.append(
                {
                    "source_key": "official_filings",
                    "market": "global",
                    "ticker": "all",
                    "scope": "legacy_market_event",
                    "last_published_at": legacy_latest,
                    "last_ingested_at": legacy_latest,
                    "document_count": 0,
                    "legacy_fallback": True,
                }
            )
    watchlist = watchlist_tickers(conn)
    if watchlist:
        placeholders = ",".join("?" for _ in watchlist)
        watch_row = conn.execute(
            f"""
            SELECT
                MAX(published_at),
                MAX(ingested_at),
                COUNT(*),
                COUNT(DISTINCT ticker)
            FROM filing_documents
            WHERE ticker IN ({placeholders})
            """,
            tuple(sorted(watchlist)),
        ).fetchone()
        source_rows.append(
            {
                "source_key": "watchlist_filings",
                "market": "watchlist",
                "ticker": "watchlist",
                "scope": "watchlist",
                "last_published_at": watch_row[0],
                "last_ingested_at": watch_row[1],
                "document_count": watch_row[2],
                "covered_ticker_count": watch_row[3],
                "watchlist_ticker_count": len(watchlist),
            }
        )
    return source_rows


def build_filings_health_snapshot(
    conn: sqlite3.Connection,
    stale_after_minutes: int = 1440,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now()
    rows = latest_filings_by_scope(conn)
    source_rows = []
    market_counts: dict[str, dict[str, int]] = {}
    for row in rows:
        anchor = parse_dt(row.get("last_published_at")) or parse_dt(row.get("last_ingested_at"))
        if not anchor:
            status = "missing"
            age_minutes = None
        else:
            age_minutes = max(0, int((now - anchor).total_seconds() / 60))
            status = "fresh" if age_minutes <= stale_after_minutes else "stale"
        market = row.get("market") or "global"
        market_counts.setdefault(market, {})
        market_counts[market][status] = market_counts[market].get(status, 0) + 1
        source_rows.append({**row, "freshness_status": status, "age_minutes": age_minutes})
    if not source_rows:
        overall = "missing"
    elif all(row["freshness_status"] == "fresh" for row in source_rows):
        overall = "fresh"
    elif any(row["freshness_status"] == "fresh" for row in source_rows):
        overall = "degraded"
    else:
        overall = "stale"
    return {
        "generated_at": now_ts(),
        "overall_status": overall,
        "stale_after_minutes": stale_after_minutes,
        "source_rows": source_rows,
        "market_counts": market_counts,
        "stale_sources": [row for row in source_rows if row["freshness_status"] != "fresh"],
    }


def update_filings_health_rows(
    conn: sqlite3.Connection,
    stale_after_minutes: int = 1440,
    affected_modules: list[str] | None = None,
) -> dict[str, Any]:
    from smr_data_health import ensure_data_health_tables

    ensure_filings_tables(conn)
    ensure_data_health_tables(conn)
    affected_modules = affected_modules or ["deep_market_scan", "opportunity_radar", "report_generation", "investment_research"]
    snapshot = build_filings_health_snapshot(conn, stale_after_minutes=stale_after_minutes)
    rows = snapshot["source_rows"] or [
        {
            "source_key": "official_filings",
            "market": "global",
            "ticker": "all",
            "scope": "global",
            "last_published_at": None,
            "last_ingested_at": None,
            "freshness_status": "missing",
            "age_minutes": None,
            "document_count": 0,
        }
    ]
    conn.execute("DELETE FROM data_source_health WHERE data_type='filings'")
    timestamp = now_ts()
    for row in rows:
        status = row["freshness_status"]
        blocking = "none" if status == "fresh" else "warn"
        source_key = row.get("source_key") or "official_filings"
        if row.get("scope") == "ticker" and row.get("ticker") not in {None, "", "all"}:
            source_key = f"{source_key}:{row.get('ticker')}"
        reason = ""
        if status != "fresh":
            reason = (
                f"filings[{row.get('source_key')}/{row.get('market')}/{row.get('ticker')}] stale or missing; "
                f"last_published_at={row.get('last_published_at') or '-'}, "
                f"last_ingested_at={row.get('last_ingested_at') or '-'}."
            )
        conn.execute(
            """
            INSERT INTO data_source_health (
                source_key, market, asset_type, data_type, last_success_at, last_data_timestamp,
                expected_update_frequency, freshness_status, stale_after_minutes, blocking_level,
                staleness_reason, affected_modules_json, metadata_json, created_at, updated_at
            )
            VALUES (?, ?, 'stock', 'filings', ?, ?, 'intraday_batch', ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_key, market, asset_type, data_type) DO UPDATE SET
                last_success_at=excluded.last_success_at,
                last_data_timestamp=excluded.last_data_timestamp,
                freshness_status=excluded.freshness_status,
                stale_after_minutes=excluded.stale_after_minutes,
                blocking_level=excluded.blocking_level,
                staleness_reason=excluded.staleness_reason,
                affected_modules_json=excluded.affected_modules_json,
                metadata_json=excluded.metadata_json,
                updated_at=excluded.updated_at
            """,
            (
                source_key,
                row.get("market") or "global",
                row.get("last_ingested_at"),
                row.get("last_published_at") or row.get("last_ingested_at"),
                status,
                stale_after_minutes,
                blocking,
                reason,
                json.dumps(affected_modules, ensure_ascii=False),
                json.dumps({**row, "original_source_key": row.get("source_key")}, ensure_ascii=False, sort_keys=True),
                timestamp,
                timestamp,
            ),
        )
    return snapshot


def export_filings_to_evidence(conn: sqlite3.Connection, limit: int = 80) -> dict[str, Any]:
    ensure_filings_tables(conn)
    ensure_claim_graph_tables(conn)
    rows = conn.execute(
        """
        SELECT
            c.chunk_id,
            c.document_id,
            c.source_key,
            c.ticker,
            c.market,
            c.text,
            c.evidence_id,
            f.published_at,
            f.ingested_at,
            f.source_url,
            f.filing_type,
            f.title,
            f.metadata_json
        FROM document_chunks c
        JOIN filing_documents f ON f.filing_id=c.document_id
        ORDER BY datetime(COALESCE(f.published_at, f.ingested_at)) DESC, c.chunk_index
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    exported = 0
    for row in rows:
        source_key = row[2] or "official_filings"
        source_quality = "primary" if source_key in PRIMARY_SOURCE_KEYS else "secondary"
        upsert_evidence(
            conn,
            {
                "evidence_id": row[6],
                "source_key": source_key,
                "source_type": "filing",
                "source_quality": source_quality,
                "source_status": "active",
                "published_at": row[7],
                "ingested_at": row[8],
                "text_excerpt": row[5],
                "url_or_doc_id": row[9] or row[1],
                "metadata": {
                    **loads_json(row[12], {}),
                    "chunk_id": row[0],
                    "filing_id": row[1],
                    "ticker": row[3],
                    "market": row[4],
                    "filing_type": row[10],
                    "title": row[11],
                    "exporter": "smr_filings_ingestion",
                },
            },
        )
        exported += 1
    return {"exported": exported, "scanned": len(rows)}


def seed_filing_document(
    conn: sqlite3.Connection,
    ticker: str,
    title: str,
    body: str,
    source_key: str = "manual_filing",
    published_at: str | None = None,
    market: str | None = None,
    filing_type: str | None = None,
) -> dict[str, Any]:
    return upsert_filing_document(
        conn,
        {
            "filing_id": generate_execution_id("filing_seed"),
            "ticker": ticker,
            "market": market,
            "title": title,
            "body": body,
            "source_key": source_key,
            "published_at": published_at or now_ts(),
            "filing_type": filing_type,
            "metadata": {"seeded": True},
        },
    )
