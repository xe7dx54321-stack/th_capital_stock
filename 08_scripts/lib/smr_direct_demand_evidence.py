#!/usr/bin/env python3
"""Phase 21 direct demand, order, customer, and capex evidence helpers.

The module builds a conservative structured layer from already ingested
evidence. It does not fetch new large sources, create pending review, or treat
management commentary as confirmed customer orders.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from datetime import datetime
from typing import Any


DEMAND_EVIDENCE_CATEGORIES = {
    "customer_order",
    "framework_contract",
    "signed_contract",
    "tender_award",
    "procurement_award",
    "customer_capex",
    "downstream_capex",
    "shipment",
    "backlog",
    "capacity_utilization",
    "management_guidance",
    "product_launch_demand",
    "channel_check",
    "industry_data",
    "policy_demand",
    "news_mention",
    "rumor_or_unconfirmed",
}

DEMAND_STRENGTHS = {
    "confirmed_order",
    "strong_indication",
    "medium_indication",
    "weak_indication",
    "context_only",
    "blocked",
}

CONFIRMED_DEMAND_ESCALATION_CATEGORIES = {
    "confirmed_order",
    "signed_contract",
    "framework_agreement",
    "tender_award",
    "procurement_award",
    "customer_capex",
    "customer_project",
    "downstream_procurement",
    "backlog",
    "shipment",
    "management_guidance",
    "industry_context",
}

ORDER_KEYWORDS = ("订单", "在手订单", "新签订单", "order", "orders", "backlog")
CONTRACT_KEYWORDS = ("合同", "框架协议", "协议", "contract", "framework agreement")
SIGNED_CONTRACT_KEYWORDS = ("签署", "签订", "signed", "entered into")
TENDER_KEYWORDS = ("中标", "招标", "tender", "bid award", "awarded")
PROCUREMENT_KEYWORDS = ("采购", "procurement", "purchase order")
CUSTOMER_KEYWORDS = ("客户", "大客户", "用户", "customer", "key customer")
CAPEX_KEYWORDS = ("capex", "资本开支", "投资建设", "数据中心", "智算中心", "算力中心", "cloud capex")
SHIPMENT_KEYWORDS = ("出货", "交付", "shipment", "delivery", "deliveries")
CAPACITY_KEYWORDS = ("产能", "产能利用率", "排产", "capacity", "utilization", "ramp")
GUIDANCE_KEYWORDS = ("指引", "预计", "预期", "展望", "guidance", "expects", "outlook", "forecast")
DEMAND_KEYWORDS = (
    "需求",
    "算力需求",
    "AI服务器",
    "服务器",
    "数据中心",
    "智算中心",
    "云厂商",
    "运营商",
    "demand",
    "AI server",
    "data center",
    "cloud",
)
PRODUCT_LAUNCH_KEYWORDS = ("发布", "推出", "launch", "launched", "showcases", "unveils")
POLICY_KEYWORDS = ("政策", "国产化", "数字基建", "policy", "digital infrastructure")
CHANNEL_KEYWORDS = ("渠道调研", "channel check", "supply chain check")
RUMOR_KEYWORDS = ("传闻", "未经证实", "rumor", "unconfirmed", "market talk")
ACCOUNTING_CONTEXT_TERMS = (
    "采购与付款管理",
    "购买商品、接受劳务",
    "合同资产",
    "合同负债",
    "客户存款",
    "客户贷款",
    "原保险合同",
    "保单",
    "内部控制",
    "内控评价",
)

AI_INFRA_TERMS = (
    "ai",
    "人工智能",
    "算力",
    "AI服务器",
    "服务器",
    "数据中心",
    "智算中心",
    "云厂商",
    "数字基建",
    "高端芯片",
    "ai infrastructure",
    "ai server",
    "data center",
    "cloud capex",
)

NEGATIVE_TERMS = ("下降", "减少", "放缓", "低于", "下修", "decline", "decrease", "weaker", "cut", "lower")
POSITIVE_TERMS = (
    "增长",
    "提升",
    "增加",
    "爆发",
    "旺盛",
    "较快",
    "获得认可",
    "strong",
    "growth",
    "increase",
    "higher",
    "positive",
    "ramp",
)

SOURCE_QUALITY_LEVELS = {
    "primary": "high",
    "official": "high",
    "secondary": "medium",
    "tertiary": "low",
    "weak": "low",
}

STRENGTH_RANK = {
    "blocked": 0,
    "context_only": 1,
    "weak_indication": 2,
    "medium_indication": 3,
    "strong_indication": 4,
    "confirmed_order": 5,
}

QUALITY_RANK = {"blocked": 0, "low": 1, "medium": 2, "high": 3}


def escalation_category_for_item(item: dict[str, Any]) -> str:
    """Map Phase 21 demand categories into Phase 22 escalation buckets.

    This intentionally does not upgrade indications into confirmed orders.
    """

    category = str(item.get("evidence_category") or "")
    strength = str(item.get("demand_strength") or "")
    if category == "signed_contract":
        return "signed_contract"
    if category == "tender_award":
        return "tender_award"
    if category == "procurement_award":
        return "procurement_award"
    if category == "framework_contract":
        return "framework_agreement"
    if category in {"customer_capex", "downstream_capex"}:
        return "customer_capex"
    if category in {"customer_order", "product_launch_demand"}:
        return "customer_project"
    if category in {"policy_demand", "industry_data", "news_mention"}:
        return "industry_context"
    if category in CONFIRMED_DEMAND_ESCALATION_CATEGORIES:
        return category
    return "industry_context" if strength in {"weak_indication", "context_only"} else "management_guidance"


def normalize_ticker(ticker: str | None) -> str:
    return str(ticker or "").strip().upper()


def now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def loads_json(raw: str | None, fallback: Any) -> Any:
    if raw in (None, ""):
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def dumps_json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, sort_keys=True, default=str)


def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return bool(conn.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name=?", (name,)).fetchone())


def table_columns(conn: sqlite3.Connection, name: str) -> set[str]:
    if not table_exists(conn, name):
        return set()
    return {row[1] for row in conn.execute(f"PRAGMA table_info({name})").fetchall()}


def stable_demand_evidence_id(ticker: str, evidence_id: str | None, category: str, source_key: str | None) -> str:
    raw = "|".join([normalize_ticker(ticker), str(evidence_id or ""), str(category or ""), str(source_key or "")])
    return "demand_" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:18]


def ensure_direct_demand_evidence_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS direct_demand_evidence_items (
            demand_evidence_id TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            evidence_id TEXT NOT NULL,
            evidence_category TEXT NOT NULL,
            demand_direction TEXT,
            demand_strength TEXT NOT NULL,
            customer_or_downstream TEXT,
            amount REAL,
            period TEXT,
            source_type TEXT,
            source_quality TEXT,
            is_confirmed INTEGER NOT NULL DEFAULT 0,
            is_forward_looking INTEGER NOT NULL DEFAULT 0,
            is_management_commentary INTEGER NOT NULL DEFAULT 0,
            independent_source_key TEXT NOT NULL,
            claim_relevance TEXT,
            usable_for_bear_case_mitigation INTEGER NOT NULL DEFAULT 0,
            usable_for_proxy_signal INTEGER NOT NULL DEFAULT 0,
            usable_for_promotion INTEGER NOT NULL DEFAULT 0,
            limitations_json TEXT NOT NULL DEFAULT '[]',
            evidence_excerpt TEXT,
            metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_direct_demand_ticker ON direct_demand_evidence_items(ticker, demand_strength)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_direct_demand_evidence ON direct_demand_evidence_items(evidence_id)")


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    lower = str(text or "").lower()
    return any(term.lower() in lower for term in terms)


def _first_matching_index(text: str, terms: tuple[str, ...]) -> int:
    lower = str(text or "").lower()
    indexes = [lower.find(term.lower()) for term in terms if lower.find(term.lower()) >= 0]
    return min(indexes) if indexes else -1


def excerpt_around_keywords(text: str, terms: tuple[str, ...], *, max_len: int = 700) -> str:
    clean = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(clean) <= max_len:
        return clean
    idx = _first_matching_index(clean, terms)
    if idx < 0:
        return clean[:max_len]
    start = max(0, idx - 180)
    return clean[start : start + max_len].strip()


def source_quality_level(row: dict[str, Any]) -> str:
    if row.get("quality_score") is not None:
        try:
            score = float(row.get("quality_score"))
        except (TypeError, ValueError):
            score = None
        if score is not None:
            if score >= 0.68:
                return "high"
            if score >= 0.55:
                return "medium"
            if score >= 0.35:
                return "low"
            return "blocked"
    source_quality = str(row.get("source_quality") or "").lower()
    if source_quality in SOURCE_QUALITY_LEVELS:
        return SOURCE_QUALITY_LEVELS[source_quality]
    source_type = str(row.get("source_type") or row.get("document_type") or "").lower()
    if source_type in {"filing", "fundamentals"}:
        return "high"
    if source_type == "news":
        return "medium"
    return "low"


def independent_source_key(row: dict[str, Any]) -> str:
    metadata = row.get("metadata") or {}
    for key in (
        "source_id",
        "filing_id",
        "announcement_id",
        "news_id",
        "source_url",
        "url_or_doc_id",
        "raw_rel_path",
        "document_id",
    ):
        value = metadata.get(key) or row.get(key)
        if value:
            return str(value)
    source_key = row.get("source_key")
    published_at = row.get("published_at") or metadata.get("published_at") or metadata.get("notice_date")
    if source_key and published_at:
        return f"{source_key}:{published_at}"
    if source_key and row.get("evidence_id"):
        return f"{source_key}:{row.get('evidence_id')}"
    return ""


def _accounting_context_without_direct_demand(text: str) -> bool:
    return _contains_any(text, ACCOUNTING_CONTEXT_TERMS) and not _contains_any(text, AI_INFRA_TERMS + DEMAND_KEYWORDS + ORDER_KEYWORDS)


def demand_category_for_text(text: str, source_type: str | None = None) -> str | None:
    if _contains_any(text, RUMOR_KEYWORDS):
        return "rumor_or_unconfirmed"
    if _accounting_context_without_direct_demand(text):
        return None
    if _contains_any(text, TENDER_KEYWORDS):
        return "tender_award"
    if _contains_any(text, PROCUREMENT_KEYWORDS) and _contains_any(
        text,
        ("采购订单", "采购合同", "采购项目", "采购需求", "中标", "award", "purchase order", "procurement award"),
    ):
        return "procurement_award"
    if _contains_any(text, CONTRACT_KEYWORDS) and _contains_any(text, SIGNED_CONTRACT_KEYWORDS):
        return "signed_contract"
    if _contains_any(text, ("框架协议", "framework agreement")):
        return "framework_contract"
    if _contains_any(text, ORDER_KEYWORDS) and not _accounting_context_without_direct_demand(text):
        return "customer_order"
    if _contains_any(text, CAPEX_KEYWORDS) and _contains_any(text, CUSTOMER_KEYWORDS + DEMAND_KEYWORDS):
        return "downstream_capex"
    if _contains_any(text, SHIPMENT_KEYWORDS):
        return "shipment"
    if _contains_any(text, CAPACITY_KEYWORDS):
        return "capacity_utilization"
    if _contains_any(text, PRODUCT_LAUNCH_KEYWORDS) and _contains_any(text, ("ai", "AI", "人工智能", "产品", "product")):
        return "product_launch_demand"
    if _contains_any(text, POLICY_KEYWORDS) and _contains_any(text, DEMAND_KEYWORDS):
        return "policy_demand"
    if _contains_any(text, CHANNEL_KEYWORDS):
        return "channel_check"
    if _contains_any(text, GUIDANCE_KEYWORDS + DEMAND_KEYWORDS + CUSTOMER_KEYWORDS):
        if str(source_type or "").lower() == "news":
            return "news_mention"
        return "management_guidance"
    return None


def demand_direction_for_text(text: str) -> str:
    positive = sum(str(text or "").lower().count(term.lower()) for term in POSITIVE_TERMS)
    negative = sum(str(text or "").lower().count(term.lower()) for term in NEGATIVE_TERMS)
    if positive and negative:
        return "negative" if negative > positive else "positive"
    if negative:
        return "negative"
    if positive or _contains_any(text, DEMAND_KEYWORDS + ORDER_KEYWORDS + CONTRACT_KEYWORDS):
        return "positive"
    return "unknown"


def claim_relevance_for_text(text: str, thesis_type: str | None = None) -> str:
    thesis = str(thesis_type or "").lower()
    if thesis == "unknown":
        return "supporting" if _contains_any(text, AI_INFRA_TERMS) else "context"
    if "ai_infrastructure" in thesis or "ai" in thesis:
        if _contains_any(text, AI_INFRA_TERMS):
            return "core"
        if _contains_any(text, DEMAND_KEYWORDS + CUSTOMER_KEYWORDS):
            return "supporting"
        return "context"
    if _contains_any(text, DEMAND_KEYWORDS + ORDER_KEYWORDS + CONTRACT_KEYWORDS):
        return "supporting"
    return "context"


def demand_strength_for(
    category: str,
    *,
    source_quality: str,
    is_management_commentary: bool,
    has_evidence_id: bool,
    has_independent_source_key: bool,
) -> str:
    if not has_evidence_id or not has_independent_source_key:
        return "blocked"
    if category == "rumor_or_unconfirmed":
        return "blocked"
    if source_quality == "blocked":
        return "blocked"
    if category in {"signed_contract", "tender_award", "procurement_award"} and source_quality in {"high", "medium"}:
        return "confirmed_order"
    if category in {"customer_order", "framework_contract", "shipment", "backlog", "capacity_utilization", "customer_capex", "downstream_capex"}:
        return "strong_indication" if source_quality in {"high", "medium"} else "weak_indication"
    if category in {"management_guidance", "policy_demand", "industry_data"}:
        return "medium_indication" if source_quality in {"high", "medium"} else "weak_indication"
    if category == "product_launch_demand":
        return "medium_indication" if not is_management_commentary and source_quality in {"high", "medium"} else "weak_indication"
    if category == "channel_check":
        return "weak_indication"
    if category == "news_mention":
        return "weak_indication" if source_quality in {"high", "medium"} else "context_only"
    return "context_only"


def period_from_text(text: str, metadata: dict[str, Any]) -> str | None:
    if metadata.get("period"):
        return str(metadata["period"])
    match = re.search(r"(FY)?(20[2-9][0-9])", str(text or ""))
    if match:
        return match.group(0)
    return None


def amount_from_text(text: str) -> float | None:
    match = re.search(r"([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)\s*(?:亿元|万元|million|bn|billion)?", str(text or ""), re.I)
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return None


def customer_or_downstream_for_text(text: str) -> str | None:
    if _contains_any(text, ("数据中心", "智算中心", "data center", "cloud")):
        return "data center / cloud capex"
    if _contains_any(text, ("AI服务器", "server", "服务器")):
        return "AI server customer"
    if _contains_any(text, CUSTOMER_KEYWORDS):
        return "customer/downstream demand"
    if _contains_any(text, ("运营商", "operator")):
        return "telecom operator"
    return None


def classify_demand_evidence(
    row: dict[str, Any],
    *,
    ticker: str,
    thesis_type: str | None = "ai_infrastructure_demand",
) -> dict[str, Any] | None:
    text = str(row.get("text_excerpt") or row.get("text") or "")
    metadata = row.get("metadata") or {}
    evidence_id = str(row.get("evidence_id") or "").strip()
    source_type = str(row.get("source_type") or row.get("document_type") or "").lower()
    focus_text = excerpt_around_keywords(
        text,
        ORDER_KEYWORDS
        + CONTRACT_KEYWORDS
        + TENDER_KEYWORDS
        + PROCUREMENT_KEYWORDS
        + CUSTOMER_KEYWORDS
        + CAPEX_KEYWORDS
        + DEMAND_KEYWORDS
        + PRODUCT_LAUNCH_KEYWORDS,
        max_len=900,
    )
    category = demand_category_for_text(focus_text, source_type)
    if not category:
        return None
    source_quality = source_quality_level(row)
    source_key = independent_source_key(row)
    section = str(metadata.get("chunk_section_type") or row.get("chunk_section_type") or "").lower()
    is_management = bool(
        category == "management_guidance"
        or "management" in section
        or "guidance" in section
        or "investor" in section
        or str(metadata.get("filing_type") or "").lower() in {"annual_report", "earnings_release", "cn_exchange_announcement"}
    )
    strength = demand_strength_for(
        category,
        source_quality=source_quality,
        is_management_commentary=is_management,
        has_evidence_id=bool(evidence_id),
        has_independent_source_key=bool(source_key),
    )
    relevance = claim_relevance_for_text(focus_text, thesis_type)
    direction = demand_direction_for_text(focus_text)
    limitations: list[str] = []
    if is_management and strength != "confirmed_order":
        limitations.append("management commentary, not signed order")
    if category == "news_mention":
        limitations.append("news mention; not direct customer/order confirmation")
    if category == "rumor_or_unconfirmed":
        limitations.append("rumor or unconfirmed source is blocked")
    if strength in {"context_only", "weak_indication"}:
        limitations.append("not enough direct demand strength for promotion")
    if relevance != "core":
        limitations.append("not core direct evidence for thesis")
    if not evidence_id:
        limitations.append("missing evidence_id")
    if not source_key:
        limitations.append("missing independent_source_key")
    usable_quality = source_quality in {"high", "medium"}
    usable_for_bear = bool(strength in {"confirmed_order", "strong_indication", "medium_indication"} and usable_quality and relevance in {"core", "supporting"})
    usable_for_proxy = bool(strength in {"confirmed_order", "strong_indication", "medium_indication", "weak_indication"} and relevance in {"core", "supporting"} and direction in {"positive", "negative"})
    return {
        "ticker": normalize_ticker(ticker),
        "demand_evidence_id": stable_demand_evidence_id(ticker, evidence_id, category, source_key),
        "evidence_id": evidence_id,
        "evidence_category": category,
        "demand_direction": direction,
        "demand_strength": strength,
        "customer_or_downstream": customer_or_downstream_for_text(focus_text),
        "amount": amount_from_text(focus_text),
        "period": period_from_text(focus_text, metadata),
        "source_type": "filing_or_news" if source_type in {"filing", "news"} else (source_type or "unknown"),
        "source_quality": source_quality,
        "is_confirmed": strength == "confirmed_order",
        "is_forward_looking": _contains_any(text, GUIDANCE_KEYWORDS),
        "is_management_commentary": is_management,
        "independent_source_key": source_key,
        "claim_relevance": relevance,
        "usable_for_bear_case_mitigation": usable_for_bear,
        "usable_for_proxy_signal": usable_for_proxy,
        "usable_for_promotion": False,
        "limitations": list(dict.fromkeys(limitations)),
        "evidence_excerpt": focus_text,
        "metadata": {
            "phase": 21,
            "source_key": row.get("source_key"),
            "source_quality_raw": row.get("source_quality"),
            "published_at": row.get("published_at") or metadata.get("published_at") or metadata.get("notice_date"),
            "chunk_id": row.get("chunk_id") or metadata.get("chunk_id"),
            "section": section,
            "internal_proxy_only": True,
            "promotion_rules_relaxed": False,
        },
    }


def _candidate_evidence_rows(conn: sqlite3.Connection, ticker: str, *, limit: int = 300) -> list[dict[str, Any]]:
    ticker = normalize_ticker(ticker)
    rows: list[dict[str, Any]] = []
    if table_exists(conn, "evidence_items"):
        columns = table_columns(conn, "evidence_items")
        quality_expr = "quality_score" if "quality_score" in columns else "NULL AS quality_score"
        proxy_expr = "usable_for_proxy_signal" if "usable_for_proxy_signal" in columns else "NULL AS usable_for_proxy_signal"
        for row in conn.execute(
            f"""
            SELECT evidence_id, source_key, source_type, source_quality, source_status,
                   published_at, ingested_at, text_excerpt, url_or_doc_id, metadata_json,
                   {quality_expr}, {proxy_expr}
            FROM evidence_items
            WHERE upper(COALESCE(metadata_json, '')) LIKE ?
               OR upper(COALESCE(text_excerpt, '')) LIKE ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (f"%{ticker}%", f"%{ticker}%", max(limit, 50)),
        ).fetchall():
            metadata = loads_json(row[9], {})
            rows.append(
                {
                    "evidence_id": row[0],
                    "source_key": row[1],
                    "source_type": row[2],
                    "source_quality": row[3],
                    "source_status": row[4],
                    "published_at": row[5],
                    "ingested_at": row[6],
                    "text_excerpt": row[7],
                    "url_or_doc_id": row[8],
                    "metadata": metadata,
                    "quality_score": row[10],
                    "usable_for_proxy_signal": row[11],
                }
            )
    if table_exists(conn, "document_chunks"):
        chunk_columns = table_columns(conn, "document_chunks")
        source_expr = "document_type" if "document_type" in chunk_columns else "'filing' AS document_type"
        for row in conn.execute(
            f"""
            SELECT chunk_id, evidence_id, source_key, {source_expr}, chunk_section_type,
                   text, metadata_json, ticker
            FROM document_chunks
            WHERE upper(COALESCE(ticker, ''))=?
               OR upper(COALESCE(metadata_json, '')) LIKE ?
               OR upper(COALESCE(text, '')) LIKE ?
            ORDER BY datetime(COALESCE(created_at, '1970-01-01')) DESC, chunk_index DESC
            LIMIT ?
            """,
            (ticker, f"%{ticker}%", f"%{ticker}%", max(limit, 50)),
        ).fetchall():
            metadata = loads_json(row[6], {})
            rows.append(
                {
                    "chunk_id": row[0],
                    "evidence_id": row[1],
                    "source_key": row[2],
                    "source_type": row[3],
                    "source_quality": "primary" if str(row[3] or "").lower() == "filing" else "secondary",
                    "chunk_section_type": row[4],
                    "text_excerpt": row[5],
                    "metadata": {**metadata, "ticker": row[7] or ticker, "chunk_section_type": row[4]},
                    "published_at": metadata.get("published_at") or metadata.get("notice_date"),
                    "quality_score": None,
                }
            )
    return rows


def upsert_direct_demand_evidence(conn: sqlite3.Connection, item: dict[str, Any]) -> dict[str, Any]:
    ensure_direct_demand_evidence_table(conn)
    now = now_ts()
    conn.execute(
        """
        INSERT INTO direct_demand_evidence_items (
            demand_evidence_id, ticker, evidence_id, evidence_category, demand_direction,
            demand_strength, customer_or_downstream, amount, period, source_type,
            source_quality, is_confirmed, is_forward_looking, is_management_commentary,
            independent_source_key, claim_relevance, usable_for_bear_case_mitigation,
            usable_for_proxy_signal, usable_for_promotion, limitations_json,
            evidence_excerpt, metadata_json, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(demand_evidence_id) DO UPDATE SET
            demand_direction=excluded.demand_direction,
            demand_strength=excluded.demand_strength,
            source_quality=excluded.source_quality,
            usable_for_bear_case_mitigation=excluded.usable_for_bear_case_mitigation,
            usable_for_proxy_signal=excluded.usable_for_proxy_signal,
            limitations_json=excluded.limitations_json,
            evidence_excerpt=excluded.evidence_excerpt,
            metadata_json=excluded.metadata_json,
            updated_at=excluded.updated_at
        """,
        (
            item["demand_evidence_id"],
            item["ticker"],
            item["evidence_id"],
            item["evidence_category"],
            item["demand_direction"],
            item["demand_strength"],
            item.get("customer_or_downstream"),
            item.get("amount"),
            item.get("period"),
            item.get("source_type"),
            item.get("source_quality"),
            1 if item.get("is_confirmed") else 0,
            1 if item.get("is_forward_looking") else 0,
            1 if item.get("is_management_commentary") else 0,
            item["independent_source_key"],
            item.get("claim_relevance"),
            1 if item.get("usable_for_bear_case_mitigation") else 0,
            1 if item.get("usable_for_proxy_signal") else 0,
            1 if item.get("usable_for_promotion") else 0,
            dumps_json(item.get("limitations") or []),
            item.get("evidence_excerpt"),
            dumps_json(item.get("metadata") or {}),
            now,
            now,
        ),
    )
    return item


def extract_direct_demand_evidence(
    conn: sqlite3.Connection,
    ticker: str,
    *,
    thesis_type: str | None = "ai_infrastructure_demand",
    limit: int = 80,
    persist: bool = True,
) -> list[dict[str, Any]]:
    ticker = normalize_ticker(ticker)
    candidates = _candidate_evidence_rows(conn, ticker, limit=max(limit * 4, 120))
    best_by_id: dict[str, dict[str, Any]] = {}
    for row in candidates:
        item = classify_demand_evidence(row, ticker=ticker, thesis_type=thesis_type)
        if not item:
            continue
        key = item["demand_evidence_id"]
        current = best_by_id.get(key)
        if current is None or (STRENGTH_RANK[item["demand_strength"]], QUALITY_RANK[item["source_quality"]]) > (
            STRENGTH_RANK[current["demand_strength"]],
            QUALITY_RANK[current["source_quality"]],
        ):
            best_by_id[key] = item
    items = list(best_by_id.values())
    items.sort(
        key=lambda item: (
            STRENGTH_RANK.get(item.get("demand_strength"), 0),
            QUALITY_RANK.get(item.get("source_quality"), 0),
            bool(item.get("claim_relevance") == "core"),
        ),
        reverse=True,
    )
    items = items[: max(1, limit)]
    if persist:
        ensure_direct_demand_evidence_table(conn)
        conn.execute("DELETE FROM direct_demand_evidence_items WHERE ticker=?", (ticker,))
        for item in items:
            upsert_direct_demand_evidence(conn, item)
    return items


def _row_to_item(row: sqlite3.Row | tuple[Any, ...]) -> dict[str, Any]:
    keys = [
        "demand_evidence_id",
        "ticker",
        "evidence_id",
        "evidence_category",
        "demand_direction",
        "demand_strength",
        "customer_or_downstream",
        "amount",
        "period",
        "source_type",
        "source_quality",
        "is_confirmed",
        "is_forward_looking",
        "is_management_commentary",
        "independent_source_key",
        "claim_relevance",
        "usable_for_bear_case_mitigation",
        "usable_for_proxy_signal",
        "usable_for_promotion",
        "limitations_json",
        "evidence_excerpt",
        "metadata_json",
        "created_at",
        "updated_at",
    ]
    data = dict(zip(keys, row))
    data["is_confirmed"] = bool(data.get("is_confirmed"))
    data["is_forward_looking"] = bool(data.get("is_forward_looking"))
    data["is_management_commentary"] = bool(data.get("is_management_commentary"))
    data["usable_for_bear_case_mitigation"] = bool(data.get("usable_for_bear_case_mitigation"))
    data["usable_for_proxy_signal"] = bool(data.get("usable_for_proxy_signal"))
    data["usable_for_promotion"] = bool(data.get("usable_for_promotion"))
    data["limitations"] = loads_json(data.pop("limitations_json"), [])
    data["metadata"] = loads_json(data.pop("metadata_json"), {})
    return data


def load_direct_demand_evidence(conn: sqlite3.Connection, ticker: str, *, limit: int = 80) -> list[dict[str, Any]]:
    ensure_direct_demand_evidence_table(conn)
    rows = conn.execute(
        """
        SELECT demand_evidence_id, ticker, evidence_id, evidence_category, demand_direction,
               demand_strength, customer_or_downstream, amount, period, source_type,
               source_quality, is_confirmed, is_forward_looking, is_management_commentary,
               independent_source_key, claim_relevance, usable_for_bear_case_mitigation,
               usable_for_proxy_signal, usable_for_promotion, limitations_json,
               evidence_excerpt, metadata_json, created_at, updated_at
        FROM direct_demand_evidence_items
        WHERE ticker=?
        ORDER BY
            CASE demand_strength
                WHEN 'confirmed_order' THEN 5
                WHEN 'strong_indication' THEN 4
                WHEN 'medium_indication' THEN 3
                WHEN 'weak_indication' THEN 2
                WHEN 'context_only' THEN 1
                ELSE 0
            END DESC,
            updated_at DESC
        LIMIT ?
        """,
        (normalize_ticker(ticker), max(1, limit)),
    ).fetchall()
    return [_row_to_item(row) for row in rows]


def summarize_demand_evidence(ticker: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    usable_items = [
        item
        for item in items
        if item.get("usable_for_bear_case_mitigation") or item.get("usable_for_proxy_signal")
    ]
    directions = {item.get("demand_direction") for item in usable_items if item.get("demand_direction") in {"positive", "negative"}}
    if len(directions) > 1:
        dominant_direction = "conflicted"
    elif directions:
        dominant_direction = next(iter(directions))
    else:
        dominant_direction = "unknown"
    best_strength = max((item.get("demand_strength") for item in items), key=lambda value: STRENGTH_RANK.get(str(value), 0), default="missing")
    independent_sources = {
        item.get("independent_source_key")
        for item in usable_items
        if item.get("independent_source_key") and item.get("independent_source_key") != "watchlist_metadata_patch"
    }
    return {
        "ticker": normalize_ticker(ticker),
        "evidence_count": len(items),
        "confirmed_order_count": sum(1 for item in items if item.get("demand_strength") == "confirmed_order"),
        "strong_indication_count": sum(1 for item in items if item.get("demand_strength") == "strong_indication"),
        "medium_indication_count": sum(1 for item in items if item.get("demand_strength") == "medium_indication"),
        "weak_indication_count": sum(1 for item in items if item.get("demand_strength") == "weak_indication"),
        "context_or_blocked_count": sum(1 for item in items if item.get("demand_strength") in {"context_only", "blocked"}),
        "independent_source_count": len(independent_sources),
        "dominant_direction": dominant_direction,
        "best_demand_strength": best_strength,
        "usable_for_proxy_signal": any(item.get("usable_for_proxy_signal") for item in items),
        "usable_for_bear_case_mitigation": any(item.get("usable_for_bear_case_mitigation") for item in items),
        "evidence_ids": [item.get("evidence_id") for item in usable_items if item.get("evidence_id")][:12],
        "independent_source_keys": sorted(independent_sources)[:12],
    }


def build_direct_demand_evidence_payload(
    conn: sqlite3.Connection,
    ticker: str,
    *,
    thesis_type: str | None = "ai_infrastructure_demand",
    limit: int = 40,
    persist: bool = True,
) -> dict[str, Any]:
    items = extract_direct_demand_evidence(conn, ticker, thesis_type=thesis_type, limit=limit, persist=persist)
    return {
        "ticker": normalize_ticker(ticker),
        "demand_evidence_summary": summarize_demand_evidence(ticker, items),
        "items": items,
        "safety": {
            "promotion_rules_relaxed": False,
            "direct_demand_auto_pending": False,
            "raw_files_persisted": False,
        },
    }
