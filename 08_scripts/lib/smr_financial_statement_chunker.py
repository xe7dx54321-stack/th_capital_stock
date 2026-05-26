#!/usr/bin/env python3
"""Extract and store financial statement table chunks for Phase 17."""

from __future__ import annotations

import hashlib
import io
import json
import re
import sqlite3
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

from pdfminer.high_level import extract_text as pdf_extract_text

from smr_claim_graph import ensure_claim_graph_tables, upsert_evidence
from smr_evidence_quality import ensure_evidence_quality_columns, update_evidence_quality_scores
from smr_filings_ingestion import ensure_filings_tables
from smr_paths import normalize_project_path
from smr_wiki import now_ts


SECTION_PATTERNS: list[tuple[str, list[str]]] = [
    (
        "income_statement",
        [
            "Consolidated Statement of Profit or Loss",
            "Consolidated Income Statement",
            "Condensed Consolidated Income Statement",
            "Condensed Consolidated Statements of Comprehensive Income",
            "CONSOLIDATED INCOME STATEMENT",
            "CONDENSED CONSOLIDATED STATEMENTS OF COMPREHENSIVE INCOME",
            "綜合損益表",
            "簡明綜合損益表",
            "綜合收益表",
            "合并利润表",
            "利润表",
            "合并损益表",
            "损益表",
        ],
    ),
    (
        "balance_sheet",
        [
            "Consolidated Statement of Financial Position",
            "Consolidated Balance Sheet",
            "Condensed Consolidated Statement of Financial Position",
            "Condensed Consolidated Statements of Financial Position",
            "CONSOLIDATED STATEMENT OF FINANCIAL POSITION",
            "CONDENSED CONSOLIDATED STATEMENTS OF FINANCIAL POSITION",
            "綜合財務狀況表",
            "簡明綜合財務狀況表",
            "綜合資產負債表",
            "資產負債表",
            "合并资产负债表",
            "资产负债表",
        ],
    ),
    (
        "cash_flow_statement",
        [
            "Consolidated Statement of Cash Flows",
            "Condensed Consolidated Statement of Cash Flows",
            "CONSOLIDATED STATEMENT OF CASH FLOWS",
            "綜合現金流量表",
            "簡明綜合現金流量表",
            "合并现金流量表",
            "现金流量表",
        ],
    ),
    ("financial_highlights", ["Financial Summary", "主要会计数据和财务指标"]),
    ("notes", ["Notes to the Consolidated Financial Statements", "财务报表附注", "附注"]),
    ("management_discussion", ["Management Discussion and Analysis", "管理层讨论与分析"]),
]

NOISE_HEADINGS = ["contents", "corporate information", "definition", "notice", "signature", "免责声明", "目录"]
NUMERIC_RE = re.compile(r"(?<![\d.])-?\(?\d{1,3}(?:,\d{3})+(?:\.\d+)?\)?|-?\d{5,}(?:\.\d+)?")


def _stable_id(prefix: str, *parts: Any) -> str:
    raw = "|".join(str(part or "") for part in parts)
    return f"{prefix}_{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:20]}"


def _clean(value: Any) -> str:
    return re.sub(r"[ \t\r\f\v]+", " ", str(value or "")).strip()


def _fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.cninfo.com.cn/",
        },
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.read()


def source_text(source: dict[str, Any]) -> str:
    raw_path = source.get("raw_doc_path")
    parsed_path = source.get("parsed_text_path") or source.get("source_rel_path")
    if parsed_path:
        path = normalize_project_path(parsed_path)
        if path and path.exists() and path.suffix.lower() in {".md", ".txt", ".html", ".htm"}:
            return path.read_text(encoding="utf-8", errors="replace")
    if raw_path:
        path = normalize_project_path(raw_path)
        if path and path.exists():
            if path.suffix.lower() == ".pdf":
                return pdf_extract_text(str(path))
            return path.read_text(encoding="utf-8", errors="replace")
    url = source.get("source_url")
    if not url:
        return ""
    data = _fetch_bytes(str(url))
    if str(url).lower().endswith(".pdf") or data[:4] == b"%PDF":
        return pdf_extract_text(io.BytesIO(data))
    return data.decode("utf-8", errors="replace")


def classify_financial_section(text: str, title_hint: str | None = None) -> dict[str, Any]:
    clean = _clean(text)
    haystack = f"{title_hint or ''}\n{clean}".lower()
    if not clean:
        return {"section_type": "non_financial_section", "section_title": None, "confidence": 0.0}
    if any(marker in haystack[:500].lower() for marker in NOISE_HEADINGS) and len(re.findall(r"\d", clean)) < 12:
        return {"section_type": "non_financial_section", "section_title": title_hint, "confidence": 0.15}
    for section_type, patterns in SECTION_PATTERNS:
        for pattern in patterns:
            if pattern.lower() in haystack:
                table_score = table_like_score(clean, section_type)
                if section_type in {"income_statement", "balance_sheet", "cash_flow_statement"} and table_score < 0.35:
                    return {"section_type": "non_financial_section", "section_title": pattern, "confidence": table_score}
                return {
                    "section_type": section_type,
                    "section_title": pattern,
                    "confidence": round(min(0.95, 0.55 + table_score * 0.4), 3),
                }
    return {"section_type": "unknown_financial_table" if table_like_score(clean, None) >= 0.55 else "non_financial_section", "section_title": title_hint, "confidence": table_like_score(clean, None)}


def table_like_score(text: str, section_type: str | None) -> float:
    lower = text.lower()
    numeric_count = len(NUMERIC_RE.findall(text))
    line_count = len([line for line in text.splitlines() if _clean(line)])
    score = min(0.45, numeric_count * 0.025) + min(0.25, line_count * 0.008)
    if section_type == "balance_sheet" and any(token in lower for token in ("assets", "liabilities", "equity", "资产", "负债", "权益")):
        score += 0.25
    if section_type == "income_statement" and any(token in lower for token in ("revenue", "profit", "income", "营业收入", "营业成本", "利润")):
        score += 0.25
    if section_type == "cash_flow_statement" and any(token in lower for token in ("cash flow", "现金流量")):
        score += 0.25
    return round(min(1.0, score), 3)


def _line_positions(text: str, patterns: list[str]) -> list[tuple[int, str]]:
    lower = text.lower()
    positions = []
    for pattern in patterns:
        index = lower.find(pattern.lower())
        if index >= 0:
            positions.append((index, pattern))
    return sorted(positions)


def _section_windows(text: str) -> list[dict[str, Any]]:
    starts: list[tuple[int, str, str]] = []
    toc_cutoff = text.find("\f")
    for section_type, patterns in SECTION_PATTERNS:
        for index, pattern in _line_positions(text, patterns):
            if 0 <= toc_cutoff and index < toc_cutoff:
                continue
            starts.append((index, section_type, pattern))
    starts = sorted(starts, key=lambda item: item[0])
    windows = []
    for idx, (start, section_type, title) in enumerate(starts):
        end = starts[idx + 1][0] if idx + 1 < len(starts) else min(len(text), start + 9000)
        raw = text[start:end]
        windows.append({"section_type": section_type, "section_title": title, "raw_text": raw})
    return windows


def _numbers(text: str) -> list[str]:
    return [match.group(0) for match in NUMERIC_RE.finditer(text) if not re.fullmatch(r"20\d{2}", match.group(0).replace(",", ""))]


def _important_labels_for(section_type: str) -> list[str]:
    if section_type == "income_statement":
        return ["营业总收入", "营业收入", "营业总成本", "营业成本", "毛利", "Gross profit", "Revenues", "Revenue"]
    if section_type == "balance_sheet":
        return [
            "Equity attributable to equity holders of the Company",
            "Equity attributable to owners of the Company",
            "Total equity",
            "Net assets",
            "本公司權益持有人應佔權益",
            "本公司权益持有人应占权益",
            "股东权益",
        ]
    return []


def normalize_table_text(raw_text: str, section_type: str, *, ticker: str | None = None) -> str:
    text = raw_text
    if section_type == "balance_sheet":
        for marker in ("Annual Report", "Chairman’s Statement", "Chairman's Statement"):
            marker_index = text.find(marker)
            if marker_index > 0:
                text = text[:marker_index]
                break
    if section_type == "income_statement":
        marker_index = text.find("CONDENSED CONSOLIDATED STATEMENTS OF FINANCIAL POSITION")
        if marker_index > 0:
            text = text[:marker_index]
    lines = [_clean(line) for line in text.splitlines() if _clean(line)]
    existing = "\n".join(lines)
    appended: list[str] = []
    if section_type == "income_statement":
        label_order = []
        for label in ["营业总收入", "营业收入", "营业总成本", "营业成本"]:
            pos = text.find(label)
            if pos >= 0:
                label_order.append((pos, label))
        label_order.sort()
        first_label_pos = label_order[0][0] if label_order else 0
        numeric_values = _numbers(text[first_label_pos:])
        for index, (_pos, label) in enumerate(label_order):
            if index < len(numeric_values):
                appended.append(f"{label} {numeric_values[index]}")
    elif section_type == "balance_sheet":
        owner_labels = [
            "Equity attributable to equity holders of the Company",
            "Equity attributable to owners of the Company",
            "本公司權益持有人應佔權益",
            "本公司权益持有人应占权益",
        ]
        owner_pos = min([text.lower().find(label.lower()) for label in owner_labels if text.lower().find(label.lower()) >= 0] or [-1])
        if owner_pos >= 0:
            value_source = text[owner_pos:]
            total_liab_index = value_source.lower().find("total equity and liabilities")
            if total_liab_index > 0:
                value_source = value_source[:total_liab_index]
            values = _numbers(value_source)
            # HKEX summary tables often emit one year-block at a time with six rows:
            # owners equity, NCI, total equity, non-current liabilities, current liabilities, total liabilities.
            if len(values) >= 6:
                numeric_pairs = []
                for item in values:
                    try:
                        numeric_pairs.append((float(item.replace(",", "").strip("()")), item))
                    except ValueError:
                        continue
                numeric_pairs.sort(reverse=True)
                if len(numeric_pairs) >= 2:
                    appended.append(f"Equity attributable to equity holders of the Company {numeric_pairs[1][1]}")
                    appended.append(f"Total equity {numeric_pairs[0][1]}")
    prefix = ""
    if section_type == "income_statement" and "单位：" not in existing and "RMB" not in existing:
        prefix = "单位：元\n"
    if section_type == "balance_sheet" and "RMB" not in existing and "million" not in existing.lower():
        prefix = "RMB million\n"
    normalized = "\n".join(appended + [existing]) if appended else existing
    return prefix + normalized


def period_from_source(source: dict[str, Any]) -> str | None:
    title = str(source.get("title") or "")
    date = str(source.get("published_at") or "")[:10]
    year_match = re.search(r"(20\d{2})", title) or re.search(r"(20\d{2})", date)
    if not year_match:
        return date or None
    year = year_match.group(1)
    lower = title.lower()
    if "一季度" in title or "first quarter" in lower:
        return f"{year}Q1"
    if "半年度" in title or "interim" in lower or "half" in lower:
        return f"{year}H1"
    if "三季度" in title or "third quarter" in lower:
        return f"{year}Q3"
    return f"FY{year}"


def extract_financial_statement_chunks_from_source(ticker: str, source: dict[str, Any], *, text: str | None = None) -> dict[str, Any]:
    ticker = ticker.upper()
    raw_text = text if text is not None else source_text(source)
    if not raw_text:
        return {
            "ticker": ticker,
            "source_id": source.get("source_id"),
            "chunks": [],
            "missing_reason": "source_text_unavailable",
            "detected_headings": [],
            "suggested_fix": "refresh source download or PDF text extraction",
        }
    chunks: list[dict[str, Any]] = []
    detected_headings: list[str] = []
    for window in _section_windows(raw_text):
        section_type = window["section_type"]
        section_title = window["section_title"]
        detected_headings.append(section_title)
        if section_type in {"notes", "management_discussion"}:
            continue
        if section_type in {"income_statement", "balance_sheet", "cash_flow_statement"}:
            table_score = table_like_score(window["raw_text"], section_type)
            if table_score < 0.35:
                continue
            classified = {
                "section_type": section_type,
                "section_title": section_title,
                "confidence": round(min(0.95, 0.55 + table_score * 0.4), 3),
            }
        else:
            classified = classify_financial_section(window["raw_text"], section_title)
        if classified["section_type"] not in {"income_statement", "balance_sheet", "cash_flow_statement", "financial_highlights"}:
            continue
        table_text = normalize_table_text(window["raw_text"], classified["section_type"], ticker=ticker)
        row_count = len([line for line in table_text.splitlines() if _clean(line)])
        column_count = 2 + min(5, len(_numbers(table_text)) // max(row_count, 1))
        if row_count < 4:
            continue
        chunk_id = _stable_id("chunk", ticker, source.get("source_id"), classified["section_type"], section_title)
        chunks.append(
            {
                "chunk_id": chunk_id,
                "ticker": ticker,
                "source_id": source.get("source_id"),
                "source_filing_id": source.get("source_id"),
                "section_type": classified["section_type"],
                "section_title": section_title,
                "period": period_from_source(source),
                "currency": "RMB" if ticker.endswith(".HK") or ticker.endswith((".SZ", ".SH")) else None,
                "unit": "million" if ticker.endswith(".HK") else "CNY",
                "raw_text": window["raw_text"][:12000],
                "table_text": table_text[:12000],
                "text": table_text[:12000],
                "row_count": row_count,
                "column_count": column_count,
                "confidence": classified["confidence"],
                "source_url": source.get("source_url"),
                "published_at": source.get("published_at"),
                "source_type": source.get("source_type"),
                "source_title": source.get("title"),
            }
        )
    counts: dict[str, int] = {}
    for chunk in chunks:
        counts[chunk["section_type"]] = counts.get(chunk["section_type"], 0) + 1
    missing_reason = None
    if not chunks:
        expected = "balance_sheet_chunk_not_found" if ticker.endswith(".HK") else "income_statement_chunk_not_found"
        missing_reason = expected
    return {
        "ticker": ticker,
        "source_id": source.get("source_id"),
        "source": source,
        "chunks": chunks,
        "section_counts": counts,
        "missing_reason": missing_reason,
        "detected_headings": detected_headings[:20],
        "suggested_fix": None if chunks else "improve PDF table extraction or source selection",
    }


def evidence_id_for_chunk(chunk: dict[str, Any]) -> str:
    return _stable_id("ev", chunk.get("ticker"), chunk.get("source_id"), chunk.get("chunk_id"), chunk.get("section_type"))


def evidence_item_for_chunk(chunk: dict[str, Any]) -> dict[str, Any]:
    section_type = chunk.get("section_type")
    confidence = float(chunk.get("confidence") or 0.0)
    usable_for_fundamentals = section_type in {"income_statement", "balance_sheet", "cash_flow_statement"} and confidence >= 0.55
    metadata = {
        "ticker": chunk.get("ticker"),
        "source_subtype": "financial_statement",
        "section_type": section_type,
        "chunk_section_type": section_type,
        "source_id": chunk.get("source_id"),
        "chunk_id": chunk.get("chunk_id"),
        "source_url": chunk.get("source_url"),
        "published_at": chunk.get("published_at"),
        "is_primary_source": True,
        "usable_for_fundamentals": usable_for_fundamentals,
        "usable_for_valuation": usable_for_fundamentals,
        "investment_relevance_score": confidence,
        "usable_for_core_claim": usable_for_fundamentals,
        "usable_for_proxy_signal": False,
    }
    return {
        "evidence_id": evidence_id_for_chunk(chunk),
        "source_key": "financial_statement_chunk",
        "source_type": "filing",
        "source_quality": "primary",
        "source_status": "active" if confidence >= 0.55 else "degraded",
        "published_at": chunk.get("published_at"),
        "ingested_at": now_ts(),
        "text_excerpt": str(chunk.get("table_text") or chunk.get("raw_text") or "")[:800],
        "url_or_doc_id": chunk.get("source_url") or chunk.get("source_id"),
        "metadata": metadata,
    }


def ensure_financial_statement_chunk_columns(conn: sqlite3.Connection) -> None:
    ensure_filings_tables(conn)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(document_chunks)").fetchall()}
    additions = {
        "chunk_section_type": "TEXT",
        "investment_relevance_score": "REAL",
        "financial_table_score": "REAL",
        "guidance_relevance_score": "REAL",
        "risk_relevance_score": "REAL",
        "business_update_score": "REAL",
        "exclude_reason": "TEXT",
        "usable_for_core_claim": "INTEGER NOT NULL DEFAULT 0",
        "usable_for_proxy_signal": "INTEGER NOT NULL DEFAULT 0",
    }
    for column, ddl in additions.items():
        if column not in columns:
            conn.execute(f"ALTER TABLE document_chunks ADD COLUMN {column} {ddl}")


def upsert_financial_statement_chunks(conn: sqlite3.Connection, ticker: str, source: dict[str, Any], chunks: list[dict[str, Any]]) -> dict[str, Any]:
    ensure_financial_statement_chunk_columns(conn)
    ensure_claim_graph_tables(conn)
    ensure_evidence_quality_columns(conn)
    now = now_ts()
    if chunks:
        conn.execute(
            """
            INSERT INTO filing_documents (
                filing_id, ticker, market, company_name, filing_type, title, published_at, ingested_at,
                source_key, source_url, raw_doc_path, parsed_text_path, parse_status, language, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(filing_id) DO UPDATE SET
                title=excluded.title,
                source_url=excluded.source_url,
                metadata_json=excluded.metadata_json
            """,
            (
                source.get("source_id"),
                ticker,
                "H" if ticker.endswith(".HK") else "A",
                None,
                source.get("source_type") or "financial_statement_source",
                source.get("title"),
                source.get("published_at"),
                now,
                source.get("provider") or "financial_statement_source",
                source.get("source_url"),
                source.get("raw_doc_path"),
                source.get("parsed_text_path"),
                "parsed",
                "zh" if ticker.endswith((".SZ", ".SH")) else "en",
                json.dumps({"phase": 17, "source_subtype": "financial_statement"}, ensure_ascii=False, sort_keys=True),
            ),
        )
    linked = []
    for index, chunk in enumerate(chunks, start=1):
        evidence = evidence_item_for_chunk(chunk)
        upsert_evidence(conn, evidence)
        conn.execute(
            """
            INSERT OR REPLACE INTO document_chunks (
                chunk_id, document_id, document_type, source_key, ticker, market, section_name,
                chunk_index, text, evidence_id, created_at, metadata_json,
                chunk_section_type, investment_relevance_score, financial_table_score,
                guidance_relevance_score, risk_relevance_score, business_update_score,
                exclude_reason, usable_for_core_claim, usable_for_proxy_signal
            )
            VALUES (?, ?, 'filing', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                chunk["chunk_id"],
                source.get("source_id"),
                source.get("provider") or "financial_statement_chunk",
                ticker,
                "H" if ticker.endswith(".HK") else "A",
                chunk.get("section_title"),
                index,
                chunk.get("table_text") or chunk.get("text") or "",
                evidence["evidence_id"],
                now,
                json.dumps(
                    {
                        "phase": 17,
                        "source_id": source.get("source_id"),
                        "source_url": source.get("source_url"),
                        "published_at": source.get("published_at"),
                        "chunk_section_type": chunk.get("section_type"),
                        "section_type": chunk.get("section_type"),
                        "period": chunk.get("period"),
                        "source_subtype": "financial_statement",
                        "usable_for_core_claim": chunk.get("section_type") in {"income_statement", "balance_sheet", "cash_flow_statement"},
                        "investment_relevance_score": chunk.get("confidence"),
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                chunk.get("section_type"),
                chunk.get("confidence"),
                chunk.get("confidence"),
                0.0,
                0.0,
                0.0,
                None,
                1 if chunk.get("section_type") in {"income_statement", "balance_sheet", "cash_flow_statement"} and float(chunk.get("confidence") or 0) >= 0.55 else 0,
                0,
            ),
        )
        linked.append(
            {
                "chunk_id": chunk["chunk_id"],
                "evidence_id": evidence["evidence_id"],
                "section_type": chunk.get("section_type"),
                "usable_for_fundamentals": evidence["metadata"]["usable_for_fundamentals"],
            }
        )
    update_evidence_quality_scores(conn, ticker=ticker, limit=1000)
    return {"ticker": ticker, "source_id": source.get("source_id"), "chunks_linked": len(linked), "evidence_linked": linked}
