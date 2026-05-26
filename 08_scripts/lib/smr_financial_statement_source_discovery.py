#!/usr/bin/env python3
"""Discover primary financial statement sources for Phase 17 recovery."""

from __future__ import annotations

import json
import re
import sqlite3
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from smr_paths import normalize_project_path, project_path, relative_to_project
from smr_wiki import loads_json, now_ts
from smr_cninfo_source_identity import cninfo_query_hint, resolve_cninfo_source_identity


MANIFEST_PATH = project_path("00_control", "financial_statement_sources.json")
HKEX_FILE_PREFIX = "https://www1.hkexnews.hk"
CNINFO_STATIC_PREFIX = "https://static.cninfo.com.cn/"

EXPECTED_SECTIONS = ["income_statement", "balance_sheet", "cash_flow_statement"]
TARGET_NAMES = {
    "300308.SZ": "中际旭创",
    "688041.SH": "海光信息",
    "00700.HK": "TENCENT",
}

def market_for_ticker(ticker: str) -> str:
    value = ticker.upper()
    if value.endswith(".HK"):
        return "HK"
    if value.endswith((".SZ", ".SH", ".BJ")):
        return "CN"
    return "US"


def stable_source_id(provider: str, ticker: str, title: str, published_at: str | None) -> str:
    raw = re.sub(r"[^A-Za-z0-9]+", "_", f"{provider}_{ticker}_{published_at or ''}_{title}".lower()).strip("_")
    return raw[:120] or f"{provider}_{ticker.lower().replace('.', '_')}"


def load_financial_statement_manifest(path: Path | None = None) -> dict[str, Any]:
    manifest_path = path or MANIFEST_PATH
    if not manifest_path.exists():
        return {"version": 1, "updated_at": None, "sources": {}}
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def validate_financial_statement_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    sources = manifest.get("sources") or {}
    if not isinstance(sources, dict):
        errors.append("sources_must_be_object")
        sources = {}
    for ticker, items in sources.items():
        if not isinstance(items, list):
            errors.append(f"{ticker}:sources_must_be_list")
            continue
        for index, source in enumerate(items):
            for key in ("source_id", "source_type", "published_at", "expected_sections", "status"):
                if source.get(key) in (None, "", []):
                    errors.append(f"{ticker}:{index}:missing_{key}")
            if not source.get("source_url"):
                errors.append(f"{ticker}:{index}:source_url_missing")
    return {"valid": not errors, "errors": errors}


def manifest_sources_for_ticker(ticker: str, manifest: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    manifest = manifest or load_financial_statement_manifest()
    results = []
    for source in (manifest.get("sources") or {}).get(ticker.upper(), []):
        if str(source.get("status") or "active").lower() != "active":
            continue
        results.append(_normalize_source(ticker.upper(), source, provider_hint="manifest"))
    return results


def _parse_dt(value: Any) -> datetime | None:
    text = str(value or "").strip().replace("T", " ")[:19]
    if not text:
        return None
    for fmt, width in (("%Y-%m-%d %H:%M:%S", 19), ("%Y-%m-%d %H:%M", 16), ("%Y-%m-%d", 10)):
        try:
            return datetime.strptime(text[:width], fmt)
        except ValueError:
            continue
    return None


def _source_priority(source_type: str) -> int:
    value = str(source_type or "").lower()
    if value == "annual_report":
        return 5
    if value in {"interim_report", "semi_annual_report"}:
        return 4
    if value in {"quarterly_report", "third_quarter_report"}:
        return 3
    if value in {"results_announcement", "earnings_report", "performance_report"}:
        return 2
    return 1


def rank_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def key(source: dict[str, Any]) -> tuple[int, datetime, float]:
        return (
            _source_priority(str(source.get("source_type") or "")),
            _parse_dt(source.get("published_at")) or datetime.min,
            float(source.get("confidence") or 0.0),
        )

    return sorted(sources, key=key, reverse=True)


def choose_best_source(sources: list[dict[str, Any]]) -> dict[str, Any] | None:
    ranked = rank_sources([item for item in sources if item.get("has_financial_tables")])
    if not ranked:
        return None
    best = ranked[0]
    return {
        **best,
        "reason": f"latest {best.get('source_type')} with expected financial statement sections",
    }


def _infer_source_type(title: str, category: str = "") -> str:
    text = f"{title} {category}".lower()
    if "annual report" in text or "年度报告" in text:
        return "annual_report"
    if "interim" in text or "half-year" in text or "semi-annual" in text or "半年度报告" in text:
        return "semi_annual_report"
    if "third quarterly" in text or "三季度报告" in text:
        return "third_quarter_report"
    if "quarter" in text or "季度报告" in text or "一季度报告" in text:
        return "quarterly_report"
    if "results" in text or "业绩" in text:
        return "results_announcement"
    return "financial_statement_source"


def _normalize_source(ticker: str, source: dict[str, Any], *, provider_hint: str | None = None) -> dict[str, Any]:
    title = str(source.get("title") or source.get("announcementTitle") or "").strip()
    published_at = str(source.get("published_at") or source.get("notice_date") or "")[:10] or None
    source_type = source.get("source_type") or _infer_source_type(title, str(source.get("category") or ""))
    source_url = source.get("source_url") or source.get("url")
    source_id = source.get("source_id") or stable_source_id(provider_hint or "source", ticker, title, published_at)
    expected_sections = source.get("expected_sections") or list(EXPECTED_SECTIONS)
    return {
        "source_id": source_id,
        "ticker": ticker,
        "market": market_for_ticker(ticker),
        "source_type": source_type,
        "source_url": source_url,
        "published_at": published_at,
        "title": title,
        "document_format": source.get("document_format") or ("pdf_or_html" if source_url else "unknown"),
        "has_financial_tables": bool(source.get("has_financial_tables", True)),
        "expected_sections": expected_sections,
        "confidence": float(source.get("confidence") or 0.7),
        "provider": source.get("provider") or provider_hint,
        "raw_doc_path": source.get("raw_doc_path"),
        "parsed_text_path": source.get("parsed_text_path"),
        "source_rel_path": source.get("source_rel_path"),
    }


def _fetch_json(url: str, *, data: bytes | None = None, referer: str = "https://www.cninfo.com.cn") -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/plain, */*",
            "Referer": referer,
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def discover_cninfo_sources_live(ticker: str, *, days_back: int = 900) -> list[dict[str, Any]]:
    ticker = ticker.upper()
    hint = cninfo_query_hint(ticker)
    if not hint:
        return []
    code = ticker.split(".")[0]
    categories = [
        ("category_ndbg_szsh", "annual_report"),
        ("category_bndbg_szsh", "semi_annual_report"),
        ("category_yjdbg_szsh", "quarterly_report"),
        ("category_sjdbg_szsh", "third_quarter_report"),
    ]
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    results: list[dict[str, Any]] = []
    for category, default_type in categories:
        form = {
            "stock": f"{code},{hint['org_id']}",
            "tabName": "fulltext",
            "pageSize": "8",
            "pageNum": "1",
            "column": hint["column"],
            "category": category,
            "plate": hint["plate"],
            "seDate": f"{start_date}~{end_date}",
            "searchkey": "",
            "secid": "",
            "sortName": "",
            "sortType": "",
            "isHLtitle": "true",
        }
        payload = _fetch_json(
            "https://www.cninfo.com.cn/new/hisAnnouncement/query",
            data=urllib.parse.urlencode(form).encode("utf-8"),
        )
        for item in payload.get("announcements") or []:
            if str(item.get("secCode") or "") != code or not item.get("adjunctUrl"):
                continue
            published_at = datetime.fromtimestamp((item.get("announcementTime") or 0) / 1000).strftime("%Y-%m-%d")
            title = re.sub(r"<[^>]+>", "", str(item.get("announcementTitle") or "")).strip()
            source_url = urllib.parse.urljoin(CNINFO_STATIC_PREFIX, item["adjunctUrl"])
            is_summary = "摘要" in title or "summary" in title.lower()
            results.append(
                _normalize_source(
                    ticker,
                    {
                        "source_id": f"cninfo_{ticker.lower().replace('.', '_')}_{item.get('announcementId')}",
                        "source_type": f"{default_type}_summary" if is_summary else default_type,
                        "source_url": source_url,
                        "published_at": published_at,
                        "title": title,
                        "document_format": "pdf",
                        "confidence": 0.65 if is_summary else (0.88 if default_type in {"annual_report", "quarterly_report"} else 0.8),
                    },
                    provider_hint="cninfo",
                )
            )
    return rank_sources(results)


def _load_hkex_helpers():
    import sys

    wiki_dir = project_path("08_scripts", "wiki")
    lib_dir = project_path("08_scripts", "lib")
    for path in (wiki_dir, lib_dir):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    import fetch_hkex_announcements as hkex  # type: ignore

    return hkex


def discover_hkex_sources_live(ticker: str, *, days_back: int = 900) -> list[dict[str, Any]]:
    ticker = ticker.upper()
    hkex = _load_hkex_helpers()
    code = ticker.split(".")[0]
    target = {"ts_code": ticker, "code": code, "name": TARGET_NAMES.get(ticker, code), "sector": None, "pool_type": "ai_core"}
    identity = hkex.resolve_stock_identity(target)
    start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d")
    end_date = datetime.now().strftime("%Y%m%d")
    _payload, announcements = hkex.title_search(identity["stock_id"], start_date, end_date, 200)
    results: list[dict[str, Any]] = []
    for item in announcements:
        title = hkex.strip_html(item.get("TITLE"))
        category = hkex.strip_html(item.get("LONG_TEXT"))
        text = f"{title} {category}".lower()
        if not any(token in text for token in ("annual report", "interim report", "quarterly results", "final results", "results")):
            continue
        if "environmental" in text or "notice of annual general meeting" in text or "poll results" in text:
            continue
        notice_date, _notice_ts = hkex.parse_notice_date(item["DATE_TIME"])
        source_url = urllib.parse.urljoin(HKEX_FILE_PREFIX, item.get("FILE_LINK") or "")
        results.append(
            _normalize_source(
                ticker,
                {
                    "source_id": f"hkex_{ticker.lower().replace('.', '_')}_{item.get('NEWS_ID')}",
                    "source_type": _infer_source_type(title, category),
                    "source_url": source_url,
                    "published_at": notice_date,
                    "title": title,
                    "document_format": "pdf",
                    "confidence": 0.9 if "annual report" in text else 0.82,
                },
                provider_hint="hkex",
            )
        )
    return rank_sources(results)


def discover_sources_from_db(conn: sqlite3.Connection, ticker: str) -> list[dict[str, Any]]:
    ticker = ticker.upper()
    sources: list[dict[str, Any]] = []
    if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='source_manifest'").fetchone():
        rows = conn.execute(
            """
            SELECT source_id, title, source_path, source_rel_path, source_type, created_at, updated_at, metadata_json
            FROM source_manifest
            WHERE entity_id=?
            ORDER BY COALESCE(updated_at, created_at) DESC
            LIMIT 120
            """,
            (ticker,),
        ).fetchall()
        for row in rows:
            metadata = loads_json(row[7], {})
            title = str(row[1] or metadata.get("title") or "")
            source_type = _infer_source_type(title, str(metadata.get("announcement_type_name") or ""))
            lower = title.lower()
            if source_type == "financial_statement_source" and not any(token in lower for token in ("annual", "interim", "quarter", "results", "年度报告", "季度报告", "半年度报告")):
                continue
            sources.append(
                _normalize_source(
                    ticker,
                    {
                        "source_id": row[0],
                        "source_type": source_type,
                        "source_url": metadata.get("source_url"),
                        "published_at": metadata.get("published_at") or metadata.get("notice_date") or row[5] or row[6],
                        "title": title,
                        "document_format": "pdf_or_html",
                        "confidence": 0.72,
                        "raw_doc_path": metadata.get("raw_rel_path"),
                        "parsed_text_path": row[2] or row[3],
                        "source_rel_path": row[3],
                    },
                    provider_hint=str(metadata.get("provider") or row[4] or "db"),
                )
            )
    if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='filing_documents'").fetchone():
        rows = conn.execute(
            """
            SELECT filing_id, filing_type, title, published_at, source_url, raw_doc_path, parsed_text_path, source_key
            FROM filing_documents
            WHERE ticker=?
            ORDER BY COALESCE(published_at, ingested_at) DESC
            LIMIT 80
            """,
            (ticker,),
        ).fetchall()
        for row in rows:
            source_type = row[1] if row[1] in {"annual_report", "interim_report", "quarterly_report"} else _infer_source_type(row[2] or "")
            if source_type == "financial_statement_source":
                continue
            sources.append(
                _normalize_source(
                    ticker,
                    {
                        "source_id": row[0],
                        "source_type": source_type,
                        "source_url": row[4],
                        "published_at": row[3],
                        "title": row[2],
                        "document_format": "pdf_or_html",
                        "confidence": 0.7,
                        "raw_doc_path": row[5],
                        "parsed_text_path": row[6],
                    },
                    provider_hint=row[7],
                )
            )
    deduped: dict[str, dict[str, Any]] = {}
    for source in sources:
        key = source.get("source_url") or source.get("source_id")
        if key and key not in deduped:
            deduped[str(key)] = source
    return rank_sources(list(deduped.values()))


def discover_financial_statement_sources(
    conn: sqlite3.Connection | None,
    ticker: str,
    *,
    live: bool = True,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ticker = ticker.upper()
    sources = manifest_sources_for_ticker(ticker, manifest)
    if conn is not None:
        sources.extend(discover_sources_from_db(conn, ticker))
    if live:
        try:
            if market_for_ticker(ticker) == "HK":
                sources.extend(discover_hkex_sources_live(ticker))
            elif market_for_ticker(ticker) == "CN":
                sources.extend(discover_cninfo_sources_live(ticker))
        except Exception as exc:
            sources.append(
                {
                    "ticker": ticker,
                    "source_id": f"{ticker.lower()}_live_discovery_error",
                    "source_type": "discovery_error",
                    "title": "live discovery error",
                    "published_at": None,
                    "source_url": None,
                    "document_format": "unknown",
                    "has_financial_tables": False,
                    "expected_sections": [],
                    "confidence": 0.0,
                    "error": str(exc),
                }
            )
    ranked = rank_sources([source for source in sources if source.get("source_type") != "discovery_error"])
    best = choose_best_source(ranked)
    if not ranked:
        source_identity = resolve_cninfo_source_identity(ticker) if market_for_ticker(ticker) == "CN" else None
        identity_reason = (source_identity or {}).get("missing_reason")
        return {
            "ticker": ticker,
            "market": market_for_ticker(ticker),
            "sources_found": [],
            "best_source": None,
            "source_identity": source_identity,
            "missing_reason": identity_reason or "financial_statement_source_not_found",
            "suggested_fix": f"refresh {'HKEX' if ticker.endswith('.HK') else 'CNINFO'} filings ingestion for annual/interim/quarterly reports",
        }
    return {
        "ticker": ticker,
        "market": market_for_ticker(ticker),
        "sources_found": ranked,
        "best_source": best,
        "source_identity": resolve_cninfo_source_identity(ticker) if market_for_ticker(ticker) == "CN" else None,
        "missing_reason": None if best else "financial_statement_source_not_found",
    }


def manifest_entry_from_source(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": source.get("source_id"),
        "source_type": source.get("source_type"),
        "source_url": source.get("source_url"),
        "published_at": source.get("published_at"),
        "title": source.get("title"),
        "document_format": source.get("document_format"),
        "expected_sections": source.get("expected_sections") or list(EXPECTED_SECTIONS),
        "status": "active",
    }


def write_manifest_suggestion(tickers: list[str], payloads: list[dict[str, Any]], path: Path | None = None) -> dict[str, Any]:
    manifest = {"version": 1, "updated_at": now_ts(), "sources": {}}
    for ticker, payload in zip(tickers, payloads):
        manifest["sources"][ticker] = [
            manifest_entry_from_source(source)
            for source in payload.get("sources_found", [])
            if source.get("source_url")
        ][:5]
    target = path or MANIFEST_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"path": str(target), "ticker_count": len(tickers), "valid": validate_financial_statement_manifest(manifest)["valid"]}
