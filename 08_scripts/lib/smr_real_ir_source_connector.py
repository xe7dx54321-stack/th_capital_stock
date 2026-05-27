#!/usr/bin/env python3
"""Phase 28 real IR source connector.

This connector normalizes already-available real source metadata from local SMR
tables. It deliberately does not fetch or store raw HTML/PDF content.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from smr_phase25_utils import unique_list
from smr_supplier_exposure_model import get_supplier_exposure_profile, normalize_ticker
from smr_wiki import now_ts


REAL_IR_SOURCE_TYPES = {
    "investor_relations_record",
    "investor_interaction",
    "earnings_briefing",
    "annual_report",
    "semiannual_report",
    "quarterly_report",
    "company_announcement",
    "company_ir_webpage",
    "news_with_company_quote",
    "industry_public_commentary",
    "unknown",
}


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return bool(conn.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name=?", (name,)).fetchone())


def _columns(conn: sqlite3.Connection, name: str) -> set[str]:
    if not _table_exists(conn, name):
        return set()
    return {row[1] for row in conn.execute(f"PRAGMA table_info({name})").fetchall()}


def _loads(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    try:
        value = json.loads(raw or "{}")
        return value if isinstance(value, dict) else {}
    except (TypeError, json.JSONDecodeError):
        return {}


def _is_metadata_only_text(text: str) -> bool:
    labels = ("证券代码", "证券简称", "公告标题", "公告日期", "公告类型", "披露板块", "原始文件")
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    return bool(lines) and len(text) < 600 and all(any(line.startswith(label) for label in labels) for line in lines)


def stable_real_ir_source_id(ticker: str, source_url: str | None, title: str | None = None) -> str:
    ticker = normalize_ticker(ticker)
    digest = hashlib.sha1(f"{ticker}|{source_url or title or ''}".encode("utf-8")).hexdigest()[:12]
    return f"real_ir_{ticker.replace('.', '_').lower()}_{digest}"


def classify_real_ir_source_type(title: str | None, source_kind: str | None = None, filing_type: str | None = None) -> str:
    text = f"{title or ''} {source_kind or ''} {filing_type or ''}".lower()
    if "投资者关系" in text or "调研" in text:
        return "investor_relations_record"
    if "互动易" in text or "问答" in text:
        return "investor_interaction"
    if "业绩说明会" in text or "earnings" in text:
        return "earnings_briefing"
    if "年度报告" in text or "annual_report" in text:
        return "annual_report"
    if "半年度" in text or "semiannual" in text:
        return "semiannual_report"
    if "季度" in text or "quarterly" in text:
        return "quarterly_report"
    if "ir_landing" in text or "ir_material" in text:
        return "company_ir_webpage"
    if "news" in text:
        return "news_with_company_quote"
    if "announcement" in text or "公告" in text or "cn_exchange_announcement" in text:
        return "company_announcement"
    return "unknown"


def ensure_real_ir_source_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS real_ir_sources (
            source_id TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            company_name TEXT,
            source_type TEXT NOT NULL,
            title TEXT,
            published_at TEXT,
            source_url TEXT,
            source_quality TEXT,
            allowed_usage TEXT,
            freshness_status TEXT,
            text_snippet TEXT,
            metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_real_ir_sources_url ON real_ir_sources(source_url) WHERE source_url IS NOT NULL")


def normalize_real_ir_source(
    *,
    ticker: str,
    company_name: str | None,
    source_type: str,
    title: str | None,
    published_at: str | None,
    source_url: str | None,
    source_quality: str = "company_primary",
    text_snippet: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_type = source_type if source_type in REAL_IR_SOURCE_TYPES else "unknown"
    allowed_usage = "semantic_extraction_candidate" if source_url else "context_only"
    return {
        "source_id": stable_real_ir_source_id(ticker, source_url, title),
        "ticker": normalize_ticker(ticker),
        "company_name": company_name,
        "source_type": source_type,
        "title": title,
        "published_at": published_at,
        "source_url": source_url,
        "source_quality": source_quality,
        "allowed_usage": allowed_usage,
        "freshness_status": "freshness_unknown" if not published_at else "dated",
        "raw_content_saved": False,
        "text_snippet": (text_snippet or "")[:4000],
        "metadata": metadata or {},
        "real_source": True,
    }


def _read_text_snippet(path_value: str | None, *, limit: int = 4000) -> str:
    if not path_value:
        return ""
    path = Path(path_value)
    if not path.is_absolute():
        path = Path.cwd() / path
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    marker = "## Extracted Text"
    if marker in text:
        text = text.split(marker, 1)[1]
    elif text.lstrip().startswith("---") and "raw_rel_path:" in text[:2000]:
        return ""
    text = text.strip()
    if _is_metadata_only_text(text):
        return ""
    return text[:limit]


def _sources_from_real_ir_table(conn: sqlite3.Connection, ticker: str) -> list[dict[str, Any]]:
    if not _table_exists(conn, "real_ir_sources"):
        return []
    rows = []
    for row in conn.execute(
        """
        SELECT source_id, ticker, company_name, source_type, title, published_at,
               source_url, source_quality, allowed_usage, freshness_status,
               text_snippet, metadata_json
        FROM real_ir_sources
        WHERE ticker=?
        ORDER BY COALESCE(published_at, updated_at) DESC
        """,
        (normalize_ticker(ticker),),
    ).fetchall():
        payload = {
            "source_id": row[0],
            "ticker": row[1],
            "company_name": row[2],
            "source_type": row[3],
            "title": row[4],
            "published_at": row[5],
            "source_url": row[6],
            "source_quality": row[7],
            "allowed_usage": row[8],
            "freshness_status": row[9],
            "raw_content_saved": False,
            "text_snippet": row[10] or "",
            "metadata": _loads(row[11]),
            "real_source": True,
        }
        rows.append(payload)
    return rows


def _sources_from_filing_documents(conn: sqlite3.Connection, ticker: str, company_name: str | None) -> list[dict[str, Any]]:
    if not _table_exists(conn, "filing_documents"):
        return []
    cols = _columns(conn, "filing_documents")
    required = {"ticker", "title", "filing_type", "published_at", "source_key", "source_url", "parsed_text_path", "metadata_json"}
    if not required.issubset(cols):
        return []
    rows = []
    for row in conn.execute(
        """
        SELECT title, filing_type, published_at, source_key, source_url, parsed_text_path, metadata_json
        FROM filing_documents
        WHERE ticker=? AND source_url IS NOT NULL
        ORDER BY COALESCE(published_at, ingested_at) DESC
        LIMIT 12
        """,
        (normalize_ticker(ticker),),
    ).fetchall():
        title, filing_type, published_at, source_key, source_url, parsed_path, metadata_json = row
        source_type = classify_real_ir_source_type(title, source_key, filing_type)
        if source_type not in {
            "investor_relations_record",
            "investor_interaction",
            "earnings_briefing",
            "annual_report",
            "semiannual_report",
            "quarterly_report",
            "company_announcement",
        }:
            continue
        rows.append(
            normalize_real_ir_source(
                ticker=ticker,
                company_name=company_name,
                source_type=source_type,
                title=title,
                published_at=published_at,
                source_url=source_url,
                source_quality="company_primary",
                text_snippet=_read_text_snippet(parsed_path),
                metadata={"source_table": "filing_documents", "source_key": source_key, "parsed_text_path": parsed_path, **_loads(metadata_json)},
            )
        )
    return rows


def _sources_from_source_manifest(conn: sqlite3.Connection, ticker: str, company_name: str | None) -> list[dict[str, Any]]:
    if not _table_exists(conn, "source_manifest"):
        return []
    rows = []
    for row in conn.execute(
        """
        SELECT source_id, source_type, title, source_rel_path, status, tags, metadata_json
        FROM source_manifest
        WHERE entity_id=? AND status='active'
        ORDER BY updated_at DESC
        LIMIT 12
        """,
        (normalize_ticker(ticker),),
    ).fetchall():
        manifest_source_id, source_kind, title, source_rel_path, status, tags, metadata_json = row
        metadata = _loads(metadata_json)
        source_url = metadata.get("source_url")
        if not source_url:
            continue
        source_type = classify_real_ir_source_type(title, source_kind)
        rows.append(
            normalize_real_ir_source(
                ticker=ticker,
                company_name=company_name,
                source_type=source_type,
                title=title,
                published_at=metadata.get("published_at") or metadata.get("notice_date") or metadata.get("fetched_at"),
                source_url=source_url,
                source_quality="company_primary",
                text_snippet=_read_text_snippet(source_rel_path),
                metadata={
                    "source_table": "source_manifest",
                    "manifest_source_id": manifest_source_id,
                    "source_rel_path": source_rel_path,
                    "tags": tags,
                    **metadata,
                },
            )
        )
    return rows


def _sources_from_news(conn: sqlite3.Connection, ticker: str, company_name: str | None) -> list[dict[str, Any]]:
    if not _table_exists(conn, "news_items"):
        return []
    rows = []
    for row in conn.execute(
        """
        SELECT news_id, source_key, title, body, url, published_at, metadata_json
        FROM news_items
        WHERE url IS NOT NULL AND (tickers_json LIKE ? OR title LIKE ? OR body LIKE ?)
        ORDER BY published_at DESC
        LIMIT 4
        """,
        (f"%{normalize_ticker(ticker)}%", f"%{company_name or ticker}%", f"%{company_name or ticker}%"),
    ).fetchall():
        news_id, source_key, title, body, url, published_at, metadata_json = row
        rows.append(
            normalize_real_ir_source(
                ticker=ticker,
                company_name=company_name,
                source_type="news_with_company_quote",
                title=title,
                published_at=published_at,
                source_url=url,
                source_quality="public_news",
                text_snippet=body,
                metadata={"source_table": "news_items", "news_id": news_id, "source_key": source_key, **_loads(metadata_json)},
            )
        )
    return rows


def discover_real_ir_sources(conn: sqlite3.Connection, ticker: str, *, limit: int = 8) -> list[dict[str, Any]]:
    ticker = normalize_ticker(ticker)
    profile = get_supplier_exposure_profile(ticker)
    company_name = profile.get("company_name")
    candidates = (
        _sources_from_real_ir_table(conn, ticker)
        + _sources_from_filing_documents(conn, ticker, company_name)
        + _sources_from_source_manifest(conn, ticker, company_name)
        + _sources_from_news(conn, ticker, company_name)
    )
    by_url: dict[str, dict[str, Any]] = {}
    for source in candidates:
        key = source.get("source_url") or source.get("source_id")
        if not key or key in by_url:
            continue
        by_url[key] = source
    return list(by_url.values())[:limit]


def write_real_ir_sources(conn: sqlite3.Connection, sources: list[dict[str, Any]]) -> int:
    ensure_real_ir_source_table(conn)
    written = 0
    now = now_ts()
    for source in sources:
        if not source.get("source_url"):
            continue
        conn.execute(
            """
            INSERT INTO real_ir_sources (
                source_id, ticker, company_name, source_type, title, published_at,
                source_url, source_quality, allowed_usage, freshness_status,
                text_snippet, metadata_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_id) DO UPDATE SET
                title=excluded.title,
                published_at=excluded.published_at,
                source_quality=excluded.source_quality,
                allowed_usage=excluded.allowed_usage,
                freshness_status=excluded.freshness_status,
                text_snippet=excluded.text_snippet,
                metadata_json=excluded.metadata_json,
                updated_at=excluded.updated_at
            """,
            (
                source.get("source_id"),
                source.get("ticker"),
                source.get("company_name"),
                source.get("source_type"),
                source.get("title"),
                source.get("published_at"),
                source.get("source_url"),
                source.get("source_quality"),
                source.get("allowed_usage"),
                source.get("freshness_status"),
                source.get("text_snippet"),
                json.dumps(source.get("metadata") or {}, ensure_ascii=False),
                now,
                now,
            ),
        )
        written += 1
    return written


def build_real_ir_source_payload(
    conn: sqlite3.Connection,
    ticker: str,
    *,
    mode: str = "dry_run",
    limit: int = 8,
) -> dict[str, Any]:
    profile = get_supplier_exposure_profile(ticker)
    sources = discover_real_ir_sources(conn, ticker, limit=limit)
    sources_written = write_real_ir_sources(conn, sources) if mode == "execute" else 0
    return {
        "ticker": normalize_ticker(ticker),
        "company_name": profile.get("company_name"),
        "mode": mode,
        "sources_found": len(sources),
        "normalized_sources": sources,
        "sources_written": sources_written,
        "source_missing": len(sources) == 0,
        "safety": {
            "raw_content_saved": False,
            "dry_run_wrote_db": False if mode == "dry_run" else None,
            "source_url_deduped": len(sources) == len(unique_list([source.get("source_url") for source in sources])),
        },
    }
