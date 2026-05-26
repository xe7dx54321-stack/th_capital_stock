#!/usr/bin/env python3
"""Phase 25 end-demand proxy model.

The model only uses already-ingested local evidence plus static theme context.
Industry-level demand can support a thesis, but it is never treated as a
company-specific order.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from smr_supply_chain_theme_template import get_supply_chain_template


DRIVER_KEYWORDS = {
    "end_customer_capex": (
        "capex",
        "capital expenditure",
        "data center",
        "hyperscaler",
        "\u4e91\u5382\u5546",
        "\u6570\u636e\u4e2d\u5fc3",
        "\u667a\u7b97\u4e2d\u5fc3",
    ),
    "GPU_accelerator_demand": (
        "gpu",
        "accelerator",
        "nvidia",
        "ai chip",
        "\u52a0\u901f\u5361",
        "\u7b97\u529b\u82af\u7247",
    ),
    "AI_cluster_networking_demand": (
        "networking",
        "cluster",
        "interconnect",
        "ethernet",
        "\u4ee5\u592a\u7f51",
        "\u4e92\u8fde",
        "\u4ea4\u6362\u673a",
        "AI\u96c6\u7fa4",
    ),
    "optical_module_upgrade_cycle": (
        "optical module",
        "transceiver",
        "\u5149\u6a21\u5757",
        "\u5347\u7ea7",
        "800g",
        "1.6t",
    ),
    "800G_demand": ("800g", "800G", "800 g", "\u5149\u6a21\u5757"),
    "1_6T_demand": ("1.6t", "1.6T", "1600g", "1600G"),
    "CPO_LPO_adoption": ("cpo", "lpo", "co-packaged", "\u7845\u5149", "\u5149\u7535\u5c01\u88c5"),
}

THEME_TERMS = (
    "AI",
    "data center",
    "optical",
    "800G",
    "1.6T",
    "CPO",
    "LPO",
    "\u5149\u6a21\u5757",
    "\u7b97\u529b",
    "\u667a\u7b97",
    "\u6570\u636e\u4e2d\u5fc3",
)

POSITIVE_TERMS = (
    "growth",
    "increase",
    "accelerate",
    "strong",
    "demand",
    "capex",
    "\u589e\u957f",
    "\u63d0\u5347",
    "\u65fa\u76db",
    "\u9700\u6c42",
    "\u52a0\u901f",
)
NEGATIVE_TERMS = ("cut", "decline", "slow", "weak", "\u4e0b\u6ed1", "\u653e\u7f13", "\u51cf\u5c11")


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    lower = str(text or "").lower()
    return any(term.lower() in lower for term in terms)


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return bool(conn.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name=?", (name,)).fetchone())


def _columns(conn: sqlite3.Connection, name: str) -> set[str]:
    if not _table_exists(conn, name):
        return set()
    return {row[1] for row in conn.execute(f"PRAGMA table_info({name})").fetchall()}


def _loads(raw: Any) -> Any:
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return {}


def _candidate_rows(conn: sqlite3.Connection, theme: str, *, limit: int = 160) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    evidence_cols = _columns(conn, "evidence_items")
    required_evidence_cols = {"evidence_id", "source_key", "source_type", "source_quality", "source_status", "published_at", "text_excerpt", "metadata_json"}
    if required_evidence_cols.issubset(evidence_cols):
        order_terms = []
        for col in ("published_at", "ingested_at", "created_at"):
            if col in evidence_cols:
                order_terms.append(col)
        order_expr = f"datetime(COALESCE({', '.join(order_terms)}, '1970-01-01')) DESC" if order_terms else "rowid DESC"
        if "id" in evidence_cols:
            order_expr += ", id DESC"
        for row in conn.execute(
            f"""
            SELECT evidence_id, source_key, source_type, source_quality, source_status,
                   published_at, text_excerpt, metadata_json
            FROM evidence_items
            ORDER BY {order_expr}
            LIMIT ?
            """,
            (limit,),
        ).fetchall():
            text = str(row[6] or "")
            if _contains_any(text, THEME_TERMS):
                rows.append(
                    {
                        "evidence_id": row[0],
                        "source_key": row[1],
                        "source_type": row[2],
                        "source_quality": row[3],
                        "source_status": row[4],
                        "published_at": row[5],
                        "text": text,
                        "metadata": _loads(row[7]),
                    }
                )
    direct_cols = _columns(conn, "direct_demand_evidence_items")
    required_direct_cols = {
        "evidence_id",
        "source_type",
        "source_quality",
        "demand_strength",
        "evidence_excerpt",
        "metadata_json",
        "independent_source_key",
    }
    if required_direct_cols.issubset(direct_cols):
        order_col = "updated_at" if "updated_at" in direct_cols else "rowid"
        for row in conn.execute(
            f"""
            SELECT evidence_id, source_type, source_quality, demand_strength,
                   evidence_excerpt, metadata_json, independent_source_key
            FROM direct_demand_evidence_items
            ORDER BY {order_col} DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall():
            text = str(row[4] or "")
            if _contains_any(text, THEME_TERMS):
                metadata = _loads(row[5])
                rows.append(
                    {
                        "evidence_id": row[0],
                        "source_key": row[6],
                        "source_type": row[1],
                        "source_quality": row[2],
                        "source_status": "active",
                        "published_at": metadata.get("published_at"),
                        "text": text,
                        "metadata": metadata,
                    }
                )
    return rows


def _direction_for(text: str) -> str:
    lower = str(text or "").lower()
    positive = sum(lower.count(term.lower()) for term in POSITIVE_TERMS)
    negative = sum(lower.count(term.lower()) for term in NEGATIVE_TERMS)
    if positive and negative:
        return "positive" if positive >= negative else "negative"
    if positive:
        return "positive"
    if negative:
        return "negative"
    return "unknown"


def _confidence_for(evidence_count: int, source_quality: str) -> str:
    if evidence_count >= 3 and source_quality in {"high", "medium"}:
        return "medium"
    if evidence_count >= 1:
        return "low_to_medium" if source_quality in {"high", "medium"} else "low"
    return "low"


def build_end_demand_proxy(conn: sqlite3.Connection, theme: str = "ai_optical_interconnect") -> dict[str, Any]:
    template = get_supply_chain_template(theme)
    rows = _candidate_rows(conn, theme)
    drivers = []
    active_positive = 0
    active_negative = 0
    active_evidence_count = 0
    for driver, keywords in DRIVER_KEYWORDS.items():
        matches = [row for row in rows if _contains_any(row.get("text") or "", keywords)]
        evidence_ids = [row.get("evidence_id") for row in matches if row.get("evidence_id")][:8]
        directions = [_direction_for(row.get("text") or "") for row in matches]
        positive = directions.count("positive")
        negative = directions.count("negative")
        if positive and negative:
            direction = "conflicted" if positive == negative else ("positive" if positive > negative else "negative")
        elif positive:
            direction = "positive"
        elif negative:
            direction = "negative"
        else:
            direction = "context_only"
        source_quality = "medium" if evidence_ids else "planned_only"
        confidence = _confidence_for(len(evidence_ids), source_quality)
        limitations = ["industry-level proxy, not company-specific order"]
        if not evidence_ids:
            limitations.append("requires external industry forecast connector")
        else:
            active_evidence_count += len(evidence_ids)
            active_positive += 1 if direction == "positive" else 0
            active_negative += 1 if direction == "negative" else 0
        drivers.append(
            {
                "driver": driver,
                "direction": direction,
                "confidence": confidence,
                "evidence_ids": evidence_ids,
                "source_quality": source_quality,
                "limitations": limitations,
                "active_evidence": bool(evidence_ids),
                "allowed_usage": "supporting_evidence" if evidence_ids else "context_only",
            }
        )
    if active_positive and active_negative:
        overall_direction = "conflicted"
    elif active_positive:
        overall_direction = "positive"
    elif active_negative:
        overall_direction = "negative"
    else:
        overall_direction = "positive"
    overall_confidence = "medium" if active_evidence_count >= 4 else ("low_to_medium" if active_evidence_count else "low")
    return {
        "theme": theme,
        "theme_template_status": template.get("status"),
        "end_demand_proxy": {
            "overall_direction": overall_direction,
            "overall_confidence": overall_confidence,
            "active_evidence_count": active_evidence_count,
            "drivers": drivers,
            "planned_sources": template.get("planned_sources") or [],
            "limitations": ["industry-level demand is not company-specific order"],
            "safety": {
                "industry_proxy_treated_as_company_order": False,
                "planned_source_used_as_active_evidence": False,
            },
        },
    }
