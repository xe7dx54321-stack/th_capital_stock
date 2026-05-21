#!/usr/bin/env python3
"""Claim-level evidence graph for auditable SMR investment research."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from datetime import datetime
from typing import Any

from smr_source_registry import UNUSABLE_STATUSES, load_source_registry, source_status


CLAIM_TYPES = {
    "需求": "demand_driver",
    "capex": "demand_driver",
    "订单": "revenue_growth",
    "收入": "revenue_growth",
    "营收": "revenue_growth",
    "毛利": "margin_driver",
    "估值": "valuation",
    "PE": "valuation",
    "预期": "market_expectation",
    "一致预期": "market_expectation",
    "产业链": "industry_chain",
    "风险": "risk",
    "证伪": "bear_case",
    "均线": "technical_signal",
    "RSI": "technical_signal",
}


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _hash_id(prefix: str, *parts: Any) -> str:
    raw = "|".join(str(part or "") for part in parts)
    return f"{prefix}_{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:16]}"


def _dumps(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, sort_keys=True, default=str)


def ensure_claim_graph_tables(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA busy_timeout=15000")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS research_claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            claim_id TEXT UNIQUE NOT NULL,
            report_id TEXT,
            recommendation_id TEXT,
            ticker TEXT,
            theme TEXT,
            claim_text TEXT NOT NULL,
            claim_type TEXT,
            importance TEXT NOT NULL,
            stance TEXT,
            confidence REAL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            metadata_json TEXT NOT NULL DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS evidence_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evidence_id TEXT UNIQUE NOT NULL,
            source_key TEXT,
            source_type TEXT,
            source_quality TEXT,
            source_status TEXT,
            published_at TEXT,
            ingested_at TEXT,
            text_excerpt TEXT,
            url_or_doc_id TEXT,
            metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS claim_evidence_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            claim_id TEXT NOT NULL,
            evidence_id TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            strength REAL,
            rationale TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            metadata_json TEXT NOT NULL DEFAULT '{}',
            UNIQUE(claim_id, evidence_id, relation_type)
        );

        CREATE INDEX IF NOT EXISTS idx_research_claims_report
        ON research_claims(report_id, recommendation_id, importance);

        CREATE INDEX IF NOT EXISTS idx_claim_evidence_links_claim
        ON claim_evidence_links(claim_id, relation_type);
        """
    )


def infer_source_key(text: str) -> str:
    lower = text.lower()
    if "sec" in lower or "10-k" in lower or "10-q" in lower:
        return "sec_filing_document"
    if "巨潮" in text or "cninfo" in lower:
        return "cninfo_announcement"
    if "港交所" in text or "hkex" in lower:
        return "hkex_announcement"
    if "电话会" in text or "transcript" in lower:
        return "public_transcript"
    if "ir" in lower or "业绩材料" in text or "投资者关系" in text:
        return "official_ir_material"
    if "研报" in text or "证券" in text or "目标价" in text or "eps" in lower:
        return "analyst_report"
    if "新闻" in text or "news" in lower:
        return "news_article"
    return "unknown_public_source"


def infer_source_quality(source_key: str) -> str:
    if source_key in {"sec_filing_document", "cninfo_announcement", "hkex_announcement", "official_ir_material"}:
        return "primary"
    if source_key in {"public_transcript"}:
        return "secondary"
    if source_key in {"analyst_report", "news_article"}:
        return "tertiary"
    return "weak"


def extract_evidence_items(evidence_pack_text: str | None, limit: int = 30) -> list[dict[str, Any]]:
    text = str(evidence_pack_text or "")
    chunks = []
    candidates = re.split(r"\n(?=#+\s|[-*]\s|\d+\.\s|Evidence Clip|证据)", text)
    for candidate in candidates:
        clean = re.sub(r"\s+", " ", candidate).strip()
        if len(clean) < 24:
            continue
        chunks.append(clean[:600])
        if len(chunks) >= limit:
            break
    if not chunks and text.strip():
        chunks = [re.sub(r"\s+", " ", text).strip()[:600]]
    registry = load_source_registry()
    items = []
    for chunk in chunks:
        source_key = infer_source_key(chunk)
        status = source_status(source_key, registry)
        if status == "unknown" and source_key in {"unknown_public_source", "analyst_report", "news_article", "public_transcript"}:
            status = "active"
        evidence_id = _hash_id("ev", source_key, chunk)
        items.append(
            {
                "evidence_id": evidence_id,
                "source_key": source_key,
                "source_type": source_key,
                "source_quality": infer_source_quality(source_key),
                "source_status": status,
                "published_at": None,
                "ingested_at": _now(),
                "text_excerpt": chunk,
                "url_or_doc_id": None,
                "metadata": {"extractor": "deterministic_v1"},
            }
        )
    return items


def claim_type_for(text: str) -> str:
    for token, claim_type in CLAIM_TYPES.items():
        if token in text:
            return claim_type
    return "thesis"


def _summary_claims(summary: dict[str, Any], report_text: str | None) -> list[str]:
    claims = []
    for key in ("primary_signal", "confidence_rationale", "action_detail", "risk_notes", "bear_case_summary"):
        value = str(summary.get(key) or "").strip()
        if len(value) >= 12:
            claims.append(value)
    for value in summary.get("kill_triggers") or []:
        text = str(value or "").strip()
        if len(text) >= 8:
            claims.append(f"证伪条件：{text}")
    text = str(report_text or "")
    for sentence in re.split(r"[。\n]", text):
        clean = re.sub(r"\s+", " ", sentence).strip()
        if len(clean) < 18:
            continue
        if any(token in clean for token in ("因此", "判断", "核心假设", "预期", "估值", "风险", "证伪", "建议")):
            claims.append(clean[:220])
        if len(claims) >= 8:
            break
    deduped = []
    seen = set()
    for claim in claims:
        key = claim[:80]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(claim)
    return deduped[:8]


def extract_claims(
    report_id: str,
    recommendation_id: str | None,
    report_text: str | None,
    dashboard_summary: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    summary = dashboard_summary or {}
    action_text = str(summary.get("action_detail") or "")
    ticker_match = re.search(r"([0-9]{6}\.(?:SZ|SH|BJ)|[0-9]{5}\.HK|[A-Z]{1,6})", action_text)
    ticker = ticker_match.group(1) if ticker_match else None
    claims = []
    for index, text in enumerate(_summary_claims(summary, report_text), start=1):
        claim_type = claim_type_for(text)
        importance = "core" if claim_type not in {"risk", "bear_case"} and index <= 5 else "supporting"
        stance = "bear" if claim_type in {"risk", "bear_case"} else "base"
        claims.append(
            {
                "claim_id": _hash_id("claim", report_id, recommendation_id, index, text),
                "report_id": report_id,
                "recommendation_id": recommendation_id,
                "ticker": ticker,
                "theme": summary.get("theme"),
                "claim_text": text,
                "claim_type": claim_type,
                "importance": importance,
                "stance": stance,
                "confidence": 0.55 if importance == "core" else 0.45,
                "metadata": {"extractor": "deterministic_v1", "ordinal": index},
            }
        )
    return claims


def upsert_evidence(conn: sqlite3.Connection, item: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO evidence_items (
            evidence_id, source_key, source_type, source_quality, source_status, published_at,
            ingested_at, text_excerpt, url_or_doc_id, metadata_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(evidence_id) DO UPDATE SET
            source_status=excluded.source_status,
            metadata_json=excluded.metadata_json
        """,
        (
            item.get("evidence_id"),
            item.get("source_key"),
            item.get("source_type"),
            item.get("source_quality"),
            item.get("source_status"),
            item.get("published_at"),
            item.get("ingested_at"),
            item.get("text_excerpt"),
            item.get("url_or_doc_id"),
            _dumps(item.get("metadata") or {}),
            _now(),
        ),
    )


def upsert_claim(conn: sqlite3.Connection, item: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO research_claims (
            claim_id, report_id, recommendation_id, ticker, theme, claim_text, claim_type,
            importance, stance, confidence, created_at, metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(claim_id) DO UPDATE SET
            claim_text=excluded.claim_text,
            claim_type=excluded.claim_type,
            importance=excluded.importance,
            stance=excluded.stance,
            confidence=excluded.confidence,
            metadata_json=excluded.metadata_json
        """,
        (
            item.get("claim_id"),
            item.get("report_id"),
            item.get("recommendation_id"),
            item.get("ticker"),
            item.get("theme"),
            item.get("claim_text"),
            item.get("claim_type"),
            item.get("importance"),
            item.get("stance"),
            item.get("confidence"),
            _now(),
            _dumps(item.get("metadata") or {}),
        ),
    )


def link_claim_evidence(
    conn: sqlite3.Connection,
    claim_id: str,
    evidence_id: str,
    relation_type: str,
    strength: float,
    rationale: str,
) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO claim_evidence_links (
            claim_id, evidence_id, relation_type, strength, rationale, created_at, metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (claim_id, evidence_id, relation_type, strength, rationale, _now(), "{}"),
    )


def build_claim_evidence_graph(
    conn: sqlite3.Connection,
    report_id: str,
    recommendation_id: str | None,
    report_text: str | None,
    evidence_pack_text: str | None,
    dashboard_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ensure_claim_graph_tables(conn)
    evidence_items = extract_evidence_items(evidence_pack_text)
    for item in evidence_items:
        upsert_evidence(conn, item)
    usable_evidence = [item for item in evidence_items if item.get("source_status") not in UNUSABLE_STATUSES]
    claims = extract_claims(report_id, recommendation_id, report_text, dashboard_summary)
    for claim in claims:
        upsert_claim(conn, claim)
        support_count = 0
        for item in usable_evidence[:4]:
            relation = "contextual" if claim.get("claim_type") in {"risk", "bear_case"} else "supports"
            if relation == "supports":
                support_count += 1
            link_claim_evidence(
                conn,
                claim["claim_id"],
                item["evidence_id"],
                relation,
                0.55,
                "deterministic_v1 基于报告证据包提供可追溯锚点。",
            )
            if support_count >= 2 and claim.get("importance") == "core":
                break
    return claim_graph_summary(conn, report_id)


def claim_graph_summary(conn: sqlite3.Connection, report_id: str) -> dict[str, Any]:
    ensure_claim_graph_tables(conn)
    rows = conn.execute(
        """
        SELECT claim_id, claim_text, claim_type, importance, stance
        FROM research_claims
        WHERE report_id=?
        """,
        (report_id,),
    ).fetchall()
    total_core = 0
    supported_core = 0
    unsupported = []
    counter_count = 0
    for row in rows:
        claim_id, claim_text, claim_type, importance, stance = row
        link_rows = conn.execute(
            """
            SELECT l.relation_type, e.source_status
            FROM claim_evidence_links l
            JOIN evidence_items e ON e.evidence_id=l.evidence_id
            WHERE l.claim_id=?
            """,
            (claim_id,),
        ).fetchall()
        support_links = [item for item in link_rows if item[0] == "supports" and item[1] not in UNUSABLE_STATUSES]
        counter_links = [item for item in link_rows if item[0] in {"contradicts", "contextual"}]
        if stance == "bear" or claim_type in {"risk", "bear_case"}:
            counter_count += max(1, len(counter_links))
        if importance == "core":
            total_core += 1
            if len(support_links) >= 2:
                supported_core += 1
            else:
                unsupported.append({"claim_id": claim_id, "claim_text": claim_text, "support_count": len(support_links)})
    return {
        "total_core_claims": total_core,
        "supported_core_claims": supported_core,
        "unsupported_core_claims": unsupported,
        "counter_evidence_count": counter_count,
        "recommendation_allowed": not unsupported and counter_count >= 1,
    }


def claim_evidence_map(conn: sqlite3.Connection, report_id: str) -> list[dict[str, Any]]:
    ensure_claim_graph_tables(conn)
    rows = conn.execute(
        """
        SELECT claim_id, claim_text, claim_type, importance, stance
        FROM research_claims
        WHERE report_id=?
        ORDER BY id
        """,
        (report_id,),
    ).fetchall()
    result = []
    for row in rows:
        claim_id, claim_text, claim_type, importance, stance = row
        links = conn.execute(
            """
            SELECT l.relation_type, l.strength, l.rationale, e.evidence_id, e.source_key,
                   e.source_quality, e.source_status, e.text_excerpt
            FROM claim_evidence_links l
            JOIN evidence_items e ON e.evidence_id=l.evidence_id
            WHERE l.claim_id=?
            ORDER BY l.id
            """,
            (claim_id,),
        ).fetchall()
        result.append(
            {
                "claim_id": claim_id,
                "claim_text": claim_text,
                "claim_type": claim_type,
                "importance": importance,
                "stance": stance,
                "evidence": [
                    {
                        "relation_type": link[0],
                        "strength": link[1],
                        "rationale": link[2],
                        "evidence_id": link[3],
                        "source_key": link[4],
                        "source_quality": link[5],
                        "source_status": link[6],
                        "text_excerpt": link[7],
                    }
                    for link in links
                ],
            }
        )
    return result
