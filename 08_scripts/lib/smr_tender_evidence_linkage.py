#!/usr/bin/env python3
"""Link Phase 24 tender/procurement items to evidence graph candidates."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from smr_claim_graph import ensure_claim_graph_tables, upsert_evidence
from smr_cn_tender_procurement import stable_tender_key, now_ts


def ensure_tender_evidence_candidate_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tender_procurement_evidence_candidates (
            evidence_id TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            evidence_type TEXT NOT NULL,
            evidence_strength TEXT NOT NULL,
            source_url TEXT NOT NULL,
            title TEXT,
            published_at TEXT,
            independent_source_key TEXT NOT NULL,
            allowed_usage TEXT NOT NULL,
            usable_for_bear_case_mitigation INTEGER NOT NULL DEFAULT 0,
            usable_for_proxy_signal INTEGER NOT NULL DEFAULT 0,
            usable_for_promotion INTEGER NOT NULL DEFAULT 0,
            payload_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tender_candidates_ticker ON tender_procurement_evidence_candidates(ticker)")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_tender_candidates_url ON tender_procurement_evidence_candidates(source_url)")


def tender_item_to_evidence_candidate(item: dict[str, Any]) -> dict[str, Any]:
    source_url = str(item.get("source_url") or "").strip()
    evidence_type = str(item.get("evidence_type") or "unknown")
    strength = str(item.get("evidence_strength") or "blocked")
    allowed_usage = str(item.get("allowed_usage") or "blocked")
    evidence_id = stable_tender_key(item.get("ticker"), source_url, item.get("title"), prefix="ev_tender")
    limitations = list(item.get("limitations") or [])
    if not source_url and "missing source_url; cannot enter evidence graph" not in limitations:
        limitations.append("missing source_url; cannot enter evidence graph")
    is_confirmed = strength == "confirmed_award" and evidence_type in {"signed_contract", "winning_bid", "procurement_award", "tender_award"}
    is_notice = evidence_type in {"tender_notice", "procurement_notice", "purchase_intention"}
    usable_for_bear = bool(source_url and allowed_usage == "supporting_evidence" and strength in {"confirmed_award", "near_confirmed", "strong_indication"})
    usable_for_proxy = bool(source_url and allowed_usage in {"supporting_evidence", "context_only"} and strength != "blocked")
    return {
        "evidence_id": evidence_id,
        "ticker": item.get("ticker"),
        "source_type": "tender_procurement",
        "source_subtype": evidence_type,
        "source_url": source_url,
        "published_at": item.get("published_at"),
        "title": item.get("title"),
        "evidence_category": "direct_demand",
        "evidence_strength": strength,
        "is_primary_source": False,
        "is_confirmed_order": is_confirmed,
        "is_tender_award": evidence_type in {"tender_award", "winning_bid", "procurement_award"},
        "is_tender_notice_only": is_notice,
        "usable_for_bear_case_mitigation": usable_for_bear,
        "usable_for_proxy_signal": usable_for_proxy,
        "usable_for_promotion": False,
        "independent_source_key": item.get("independent_source_key"),
        "allowed_usage": allowed_usage,
        "limitations": list(dict.fromkeys(limitations)),
        "metadata": {
            "connector_id": "cn_tender_procurement",
            "company_name": item.get("company_name"),
            "project_name": item.get("project_name"),
            "customer_name": item.get("customer_name"),
            "amount": item.get("amount"),
            "currency": item.get("currency"),
            "is_company_named": item.get("is_company_named"),
            "is_customer_named": item.get("is_customer_named"),
            "is_award_result": item.get("is_award_result"),
            "allowed_usage": allowed_usage,
            "limitations": list(dict.fromkeys(limitations)),
        },
        "text_excerpt": " ".join(part for part in [str(item.get("title") or ""), str(item.get("snippet") or "")] if part).strip()[:900],
    }


def upsert_tender_evidence_candidate(conn: sqlite3.Connection, candidate: dict[str, Any]) -> bool:
    source_url = str(candidate.get("source_url") or "").strip()
    if not source_url:
        return False
    ensure_tender_evidence_candidate_table(conn)
    now = now_ts()
    conn.execute(
        """
        INSERT INTO tender_procurement_evidence_candidates (
            evidence_id, ticker, evidence_type, evidence_strength, source_url, title,
            published_at, independent_source_key, allowed_usage,
            usable_for_bear_case_mitigation, usable_for_proxy_signal, usable_for_promotion,
            payload_json, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(evidence_id) DO UPDATE SET
            evidence_strength=excluded.evidence_strength,
            allowed_usage=excluded.allowed_usage,
            usable_for_bear_case_mitigation=excluded.usable_for_bear_case_mitigation,
            usable_for_proxy_signal=excluded.usable_for_proxy_signal,
            usable_for_promotion=excluded.usable_for_promotion,
            payload_json=excluded.payload_json,
            updated_at=excluded.updated_at
        """,
        (
            candidate.get("evidence_id"),
            candidate.get("ticker"),
            candidate.get("source_subtype"),
            candidate.get("evidence_strength"),
            source_url,
            candidate.get("title"),
            candidate.get("published_at"),
            candidate.get("independent_source_key"),
            candidate.get("allowed_usage"),
            1 if candidate.get("usable_for_bear_case_mitigation") else 0,
            1 if candidate.get("usable_for_proxy_signal") else 0,
            1 if candidate.get("usable_for_promotion") else 0,
            json.dumps(candidate, ensure_ascii=False, sort_keys=True, default=str),
            now,
            now,
        ),
    )
    if candidate.get("allowed_usage") != "blocked":
        ensure_claim_graph_tables(conn)
        upsert_evidence(
            conn,
            {
                "evidence_id": candidate.get("evidence_id"),
                "source_key": candidate.get("independent_source_key"),
                "source_type": "tender_procurement",
                "source_quality": "secondary",
                "source_status": "active",
                "published_at": candidate.get("published_at"),
                "ingested_at": now,
                "text_excerpt": candidate.get("text_excerpt"),
                "url_or_doc_id": source_url,
                "metadata": candidate.get("metadata") or {},
            },
        )
    return True


def load_tender_evidence_candidates(conn: sqlite3.Connection, ticker: str, *, limit: int = 80) -> list[dict[str, Any]]:
    ensure_tender_evidence_candidate_table(conn)
    rows = conn.execute(
        """
        SELECT payload_json
        FROM tender_procurement_evidence_candidates
        WHERE ticker=?
        ORDER BY
            CASE evidence_strength
                WHEN 'confirmed_award' THEN 6
                WHEN 'near_confirmed' THEN 5
                WHEN 'strong_indication' THEN 4
                WHEN 'medium_indication' THEN 3
                WHEN 'weak_indication' THEN 2
                WHEN 'context_only' THEN 1
                ELSE 0
            END DESC,
            datetime(COALESCE(published_at, updated_at)) DESC
        LIMIT ?
        """,
        (str(ticker or "").strip().upper(), max(1, limit)),
    ).fetchall()
    items = []
    for row in rows:
        try:
            items.append(json.loads(row[0]))
        except (TypeError, json.JSONDecodeError):
            continue
    return items
