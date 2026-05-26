#!/usr/bin/env python3
"""Phase 20 internal proxy signal gate diagnostics.

The output is explicitly internal-proxy only. It must not be represented as
official sell-side consensus.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any

from smr_consensus_proxy import ensure_consensus_proxy_table
from smr_evidence_quality import evidence_quality_summary
from smr_proxy_extraction import ensure_proxy_signal_table
from smr_promotion_block_reason import build_ticker_block_diagnostics


def normalize_ticker(ticker: str | None) -> str:
    return str(ticker or "").strip().upper()


def loads_json(raw: str | None, fallback: Any) -> Any:
    if raw in (None, ""):
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def parse_dt(value: Any) -> datetime | None:
    text = str(value or "").strip().replace("T", " ")[:19]
    if not text:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[: len(fmt)], fmt)
        except ValueError:
            continue
    return None


def _direction(value: str | None) -> str:
    raw = str(value or "").lower()
    if raw in {"up", "positive", "raise", "raised"}:
        return "positive"
    if raw in {"down", "negative", "cut", "lower"}:
        return "negative"
    return "unknown"


def _quality_for_ids(conn: sqlite3.Connection, evidence_ids: list[str]) -> str:
    if not evidence_ids:
        return "blocked"
    summary = evidence_quality_summary(conn, evidence_ids)
    avg = float(summary.get("avg_quality_score") or 0.0)
    if summary.get("usable_for_promotion_count") or avg >= 0.68:
        return "high"
    if summary.get("usable_for_core_claim_count") or avg >= 0.55:
        return "medium"
    if avg >= 0.35:
        return "low"
    return "blocked"


def latest_proxy_snapshot(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    ensure_consensus_proxy_table(conn)
    ensure_proxy_signal_table(conn)
    ticker = normalize_ticker(ticker)
    row = conn.execute(
        """
        SELECT proxy_direction, confidence, source_evidence_ids_json, is_official_consensus,
               evidence_count, independent_source_count, proxy_quality, usable_for_promotion,
               created_at, metadata_json
        FROM consensus_revision_proxy
        WHERE ticker=?
        ORDER BY datetime(created_at) DESC, id DESC
        LIMIT 1
        """,
        (ticker,),
    ).fetchone()
    signals = conn.execute(
        """
        SELECT signal_id, direction, strength, source_evidence_id, source_type, confidence,
               created_at, metadata_json
        FROM proxy_signal_items
        WHERE ticker=?
        ORDER BY datetime(created_at) DESC, id DESC
        LIMIT 20
        """,
        (ticker,),
    ).fetchall()
    if not row:
        return {
            "ticker": ticker,
            "proxy_direction": "unknown",
            "confidence": 0.0,
            "evidence_ids": [],
            "is_official_consensus": False,
            "evidence_count": 0,
            "independent_source_count": 0,
            "proxy_quality": "missing",
            "usable_for_promotion": False,
            "created_at": None,
            "signals": [
                {
                    "signal_id": item[0],
                    "direction": item[1],
                    "strength": item[2],
                    "source_evidence_id": item[3],
                    "source_type": item[4],
                    "confidence": item[5],
                    "created_at": item[6],
                    "metadata": loads_json(item[7], {}),
                }
                for item in signals
            ],
        }
    evidence_ids = [str(item) for item in loads_json(row[2], []) if item]
    return {
        "ticker": ticker,
        "proxy_direction": row[0],
        "confidence": float(row[1] or 0.0),
        "evidence_ids": evidence_ids,
        "is_official_consensus": bool(row[3]),
        "evidence_count": int(row[4] or len(evidence_ids)),
        "independent_source_count": int(row[5] or 0),
        "proxy_quality": row[6],
        "usable_for_promotion": bool(row[7]),
        "created_at": row[8],
        "metadata": loads_json(row[9], {}),
        "signals": [
            {
                "signal_id": item[0],
                "direction": item[1],
                "strength": item[2],
                "source_evidence_id": item[3],
                "source_type": item[4],
                "confidence": item[5],
                "created_at": item[6],
                "metadata": loads_json(item[7], {}),
            }
            for item in signals
        ],
    }


def evaluate_proxy_signal_gate(
    conn: sqlite3.Connection,
    ticker: str,
    *,
    thesis_type: str | None = None,
    snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    snapshot = snapshot or latest_proxy_snapshot(conn, ticker)
    evidence_ids = list(dict.fromkeys(snapshot.get("evidence_ids") or [s.get("source_evidence_id") for s in snapshot.get("signals") or [] if s.get("source_evidence_id")]))
    directions = {_direction(item.get("direction")) for item in snapshot.get("signals") or [] if _direction(item.get("direction")) != "unknown"}
    main_direction = _direction(snapshot.get("proxy_direction")) or "unknown"
    if main_direction == "unknown" and directions:
        main_direction = sorted(directions)[0]
    conflict_count = 1 if len(directions) > 1 else 0
    evidence_quality = _quality_for_ids(conn, evidence_ids)
    independent_count = int(snapshot.get("independent_source_count") or 0)
    evidence_count = int(snapshot.get("evidence_count") or len(evidence_ids))
    confidence = float(snapshot.get("confidence") or 0.0)
    score = 0.0
    recency = "unknown"
    created_at = parse_dt(snapshot.get("created_at"))
    if created_at:
        age_days = max(0, (datetime.now() - created_at).days)
        recency = "fresh" if age_days <= 30 else ("usable_with_warning" if age_days <= 180 else "stale")
    thesis = str(thesis_type or "").lower()
    thesis_alignment = "partial"
    if thesis == "unknown":
        thesis_alignment = "weak"
    elif main_direction == "positive" and thesis in {"ai_infrastructure_demand", "revenue_growth", "valuation_rerating"}:
        thesis_alignment = "aligned"
    elif main_direction == "negative":
        thesis_alignment = "conflicting"
    if conflict_count:
        status = "conflicted"
    elif not evidence_ids:
        status = "missing"
    elif main_direction == "unknown":
        status = "invalid"
    else:
        quality_bonus = {"high": 0.22, "medium": 0.14, "low": 0.06, "blocked": 0.0}.get(evidence_quality, 0.0)
        score = min(1.0, confidence * 0.45 + min(independent_count, 3) * 0.12 + min(evidence_count, 4) * 0.045 + quality_bonus)
        if independent_count < 2:
            score = min(score, 0.68)
        if thesis_alignment in {"weak", "conflicting"}:
            score = min(score, 0.54)
        if score >= 0.78 and independent_count >= 2 and thesis_alignment == "aligned" and evidence_quality in {"high", "medium"}:
            status = "strong"
        elif score >= 0.56 and thesis_alignment in {"aligned", "partial"}:
            status = "medium"
        else:
            status = "weak"
    if status in {"conflicted", "missing", "invalid"}:
        score = 0.0 if status == "missing" else 0.35
    missing = []
    if status != "strong":
        missing.append("dominant_proxy_signal")
    if independent_count < 2:
        missing.append("independent_source_count>=2")
    if not evidence_ids:
        missing.append("proxy_evidence_id")
    if thesis_alignment in {"weak", "conflicting"}:
        missing.append("thesis_alignment")
    if evidence_quality in {"low", "blocked"}:
        missing.append("high_or_medium_proxy_evidence_quality")
    return {
        "ticker": ticker,
        "proxy_signal_gate": {
            "status": status,
            "direction": main_direction,
            "recency": recency,
            "evidence_quality": evidence_quality,
            "independent_source_count": independent_count,
            "evidence_count": evidence_count,
            "thesis_alignment": thesis_alignment,
            "conflict_count": conflict_count,
            "proxy_strength_score": round(score, 3),
            "usable_for_promotion": status == "strong",
            "usable_for_reduced_size_pending": status == "strong" or (status == "medium" and independent_count >= 2),
            "missing_requirements": list(dict.fromkeys(missing)),
            "evidence_ids": evidence_ids[:8],
            "is_official_consensus": False,
            "note": "internal proxy only; not official sell-side consensus",
        },
    }


def build_proxy_signal_gate(conn: sqlite3.Connection, ticker: str, *, watchlist_id: str = "ai_core") -> dict[str, Any]:
    diag = build_ticker_block_diagnostics(conn, ticker, watchlist_id=watchlist_id)
    return evaluate_proxy_signal_gate(conn, ticker, thesis_type=diag.get("primary_thesis_type"))


def proxy_gate_improved(payload: dict[str, Any]) -> bool:
    gate = payload.get("proxy_signal_gate") or {}
    return gate.get("status") in {"medium", "strong"}
