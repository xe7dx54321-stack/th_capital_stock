#!/usr/bin/env python3
"""Live evidence to internal consensus proxy signals.

This module extracts conservative, auditable proxy signals from live evidence.
It never marks the result as official sell-side consensus.
"""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime
from typing import Any

from smr_consensus_proxy import build_consensus_revision_proxy, ensure_consensus_proxy_table
from smr_filing_chunk_selector import select_relevant_document_chunks


SIGNAL_TYPES = {
    "earnings_surprise",
    "revenue_surprise",
    "eps_surprise",
    "guidance_raise",
    "guidance_cut",
    "margin_guidance",
    "capex_guidance",
    "broker_eps_revision",
    "broker_target_revision",
    "post_earnings_price_reaction",
    "transcript_tone_shift",
}

PRIMARY_SOURCE_TYPES = {"filing", "fundamentals"}
LOW_SIGNAL_FILING_SECTIONS = {"cover_page", "signature", "exhibit_index", "legal_boilerplate", "administrative"}

PROXY_TEXT_MARKERS = (
    "beat",
    "beats",
    "better-than-expected",
    "blowout earnings",
    "exceeded estimates",
    "above expectations",
    "above prior outlook",
    "raised guidance",
    "raises guidance",
    "higher guidance",
    "forecast for growth",
    "revenue guidance",
    "gross margin guidance",
    "eps guidance",
    "price-target hikes",
    "price target",
    "record quarter",
    "record revenue",
)

TICKER_ALIASES = {
    "NVDA": {"NVDA", "NVIDIA"},
    "09988.HK": {"09988.HK", "9988", "BABA", "ALIBABA", "阿里巴巴"},
    "000001.SZ": {"000001.SZ", "000001", "平安银行"},
}


def now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def stable_signal_id(ticker: str, signal_type: str, evidence_id: str | None, metric: str | None, text: str) -> str:
    import hashlib

    raw = "|".join(str(part or "") for part in (ticker, signal_type, evidence_id, metric, text[:220]))
    return "proxy_sig_" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:18]


def loads_json(raw: str | None, fallback: Any) -> Any:
    if raw in (None, ""):
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return bool(conn.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name=?", (name,)).fetchone())


def table_columns(conn: sqlite3.Connection, name: str) -> set[str]:
    if not table_exists(conn, name):
        return set()
    return {row[1] for row in conn.execute(f"PRAGMA table_info({name})").fetchall()}


def ensure_proxy_signal_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS proxy_signal_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_id TEXT UNIQUE NOT NULL,
            ticker TEXT NOT NULL,
            market TEXT,
            period TEXT,
            signal_type TEXT NOT NULL,
            metric TEXT,
            current_value REAL,
            previous_value REAL,
            consensus_value REAL,
            surprise_pct REAL,
            direction TEXT,
            strength REAL,
            source_evidence_id TEXT,
            source_type TEXT,
            extraction_method TEXT,
            confidence REAL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            metadata_json TEXT NOT NULL DEFAULT '{}'
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_proxy_signal_items_ticker ON proxy_signal_items(ticker, created_at DESC)")


def market_for_ticker(ticker: str | None) -> str | None:
    text = str(ticker or "").upper()
    if text.endswith((".SZ", ".SH", ".BJ")):
        return "A"
    if text.endswith(".HK"):
        return "H"
    if text:
        return "US"
    return None


def ticker_metadata_matches(ticker: str, metadata: dict[str, Any]) -> bool:
    values = {str(metadata.get(key) or "").upper() for key in ("ticker", "symbol", "ts_code") if metadata.get(key)}
    for item in metadata.get("tickers") or []:
        if item:
            values.add(str(item).upper())
    return ticker.upper() in values


def ticker_aliases(ticker: str) -> set[str]:
    aliases = set(TICKER_ALIASES.get(ticker.upper(), set()))
    aliases.update(
        {
            ticker.upper(),
            ticker.upper().replace(".HK", ""),
            ticker.upper().replace(".SZ", ""),
            ticker.upper().replace(".SH", ""),
        }
    )
    return {alias for alias in aliases if alias}


def ticker_text_matches(ticker: str, metadata: dict[str, Any], text: str = "") -> bool:
    aliases = ticker_aliases(ticker)
    haystack = f"{text} {json.dumps(metadata, ensure_ascii=False)}".upper()
    return any(alias and alias in haystack for alias in aliases)


def ticker_body_matches(ticker: str, text: str = "", title: str | None = None) -> bool:
    aliases = ticker_aliases(ticker)
    haystack = f"{text} {title or ''}".upper()
    return any(alias in haystack for alias in aliases)


def source_context_matches_ticker(ticker: str, metadata: dict[str, Any], source_type: str | None = None) -> bool:
    aliases = set(TICKER_ALIASES.get(ticker.upper(), set()))
    aliases.update(
        {
            ticker.upper(),
            ticker.upper().replace(".HK", ""),
            ticker.upper().replace(".SZ", ""),
            ticker.upper().replace(".SH", ""),
        }
    )
    haystack = " ".join(
        str(metadata.get(key) or "")
        for key in ("source_id", "source_url", "source_path", "source_rel_path", "raw_rel_path", "meta_rel_path", "title")
    ).strip().upper()
    if source_type in PRIMARY_SOURCE_TYPES or str(source_type or "").lower() == "filing":
        return any(alias and alias in haystack for alias in aliases) if haystack else ticker_metadata_matches(ticker, metadata)
    return True


def proxy_signal_text_score(text: str, metadata: dict[str, Any] | None = None) -> float:
    lower = str(text or "").lower()
    metadata = metadata or {}
    hits = sum(1 for marker in PROXY_TEXT_MARKERS if marker in lower)
    if "revenue" in lower and any(token in lower for token in ("growth", "jumped", "increased", "forecast", "estimate", "expect")):
        hits += 1
    if "eps" in lower and any(token in lower for token in ("beat", "above", "estimate", "expectation")):
        hits += 1
    if metadata.get("usable_for_proxy_signal"):
        hits += 1
    return min(1.0, hits * 0.2)


def source_type_rank(source_type: str | None) -> int:
    value = str(source_type or "").lower()
    if value == "fundamentals":
        return 0
    if value == "filing":
        return 1
    if value == "news":
        return 2
    return 3


def proxy_quality_rank(value: str | None) -> int:
    return {"invalid": 0, "weak": 1, "medium": 2, "strong": 3}.get(str(value or "").lower(), 0)


def evidence_priority(row: dict[str, Any]) -> tuple[float, float, int]:
    metadata = row.get("metadata") or {}
    text = str(row.get("text_excerpt") or "")
    section = str(metadata.get("chunk_section_type") or "").lower()
    signal_score = proxy_signal_text_score(text, metadata)
    quality = float(row.get("quality_score") or 0.0)
    if section in LOW_SIGNAL_FILING_SECTIONS or metadata.get("exclude_reason"):
        signal_score -= 0.5
    source_bonus = 0.35 if str(row.get("source_type") or "").lower() == "fundamentals" else 0.0
    return (signal_score + source_bonus, quality, -source_type_rank(row.get("source_type")))


def evidence_matches_ticker_for_proxy(ticker: str, source_type: str, metadata: dict[str, Any], text: str = "") -> bool:
    metadata_match = ticker_metadata_matches(ticker, metadata)
    text_match = ticker_text_matches(ticker, metadata, text)
    if source_type in PRIMARY_SOURCE_TYPES or source_type == "filing":
        return metadata_match and source_context_matches_ticker(ticker, metadata, source_type)
    if source_type == "news":
        haystack = f"{text} {metadata.get('title') or ''}".upper()
        negative_aliases = {"NVDA": {"ADBE", "ADOBE", "CRM", "SALESFORCE"}}.get(ticker.upper(), set())
        body_match = ticker_body_matches(ticker, text, metadata.get("title"))
        if negative_aliases and any(alias in haystack for alias in negative_aliases) and not body_match:
            return False
        return metadata_match and body_match
    return metadata_match or text_match


def is_live_metadata(metadata: dict[str, Any]) -> bool:
    value = metadata.get("live")
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "live"}
    return False


def evidence_usable_for_proxy(row: dict[str, Any]) -> bool:
    metadata = row.get("metadata") or {}
    source_type = str(row.get("source_type") or "").lower()
    if metadata.get("exclude_reason"):
        return False
    if not is_live_metadata(metadata):
        return False
    if source_type == "filing":
        section = str(metadata.get("chunk_section_type") or "").lower()
        if section in LOW_SIGNAL_FILING_SECTIONS:
            return False
        return bool(row.get("usable_for_proxy_signal")) and proxy_signal_text_score(row.get("text_excerpt") or "", metadata) >= 0.2
    if source_type == "news":
        return proxy_signal_text_score(row.get("text_excerpt") or "", metadata) >= 0.2
    if source_type == "fundamentals":
        return True
    return False


def live_evidence_for_proxy(conn: sqlite3.Connection, ticker: str, limit: int = 16) -> list[dict[str, Any]]:
    if not table_exists(conn, "evidence_items"):
        return []
    columns = table_columns(conn, "evidence_items")
    usable_proxy_expr = "usable_for_proxy_signal" if "usable_for_proxy_signal" in columns else "NULL AS usable_for_proxy_signal"
    quality_expr = "quality_score" if "quality_score" in columns else "NULL AS quality_score"
    rows = conn.execute(
        f"""
        SELECT evidence_id, source_key, source_type, source_quality, published_at, ingested_at,
               text_excerpt, metadata_json, {quality_expr}, {usable_proxy_expr}
        FROM evidence_items
        WHERE metadata_json LIKE '%"live"%'
        ORDER BY id DESC
        LIMIT ?
        """,
        (max(limit * 80, 1000),),
    ).fetchall()
    results: list[dict[str, Any]] = []
    seen = set()
    for row in rows:
        metadata = loads_json(row[7], {})
        text = str(row[6] or "")
        if not evidence_matches_ticker_for_proxy(ticker, str(row[2] or ""), metadata, text):
            continue
        if row[0] in seen:
            continue
        seen.add(row[0])
        candidate = {
            "evidence_id": row[0],
            "source_key": row[1],
            "source_type": row[2],
            "source_quality": row[3],
            "published_at": row[4],
            "ingested_at": row[5],
            "text_excerpt": text,
            "metadata": metadata,
            "quality_score": row[8],
            "usable_for_proxy_signal": bool(row[9]) if row[9] is not None else None,
        }
        if not evidence_usable_for_proxy(candidate):
            continue
        results.append(
            {
                **candidate,
            }
        )
    if len(results) < limit and table_exists(conn, "document_chunks"):
        for chunk in select_relevant_document_chunks(conn, ticker=ticker, limit=limit, proxy_only=True):
            evidence_id = chunk.get("evidence_id")
            if not evidence_id or evidence_id in seen:
                continue
            seen.add(evidence_id)
            metadata = {**(chunk.get("metadata") or {}), "ticker": ticker, "chunk_section_type": chunk.get("chunk_section_type")}
            if not is_live_metadata(metadata):
                continue
            if not source_context_matches_ticker(ticker, metadata, "filing"):
                continue
            candidate = {
                "evidence_id": evidence_id,
                "source_key": chunk.get("source_key"),
                "source_type": "filing",
                "source_quality": "primary",
                "published_at": chunk.get("published_at"),
                "ingested_at": chunk.get("ingested_at"),
                "text_excerpt": chunk.get("text") or "",
                "metadata": metadata,
                "quality_score": None,
                "usable_for_proxy_signal": True,
            }
            if not evidence_usable_for_proxy(candidate):
                continue
            results.append(
                {
                    **candidate,
                }
            )
    results.sort(key=evidence_priority, reverse=True)
    return results[:limit]


def parse_first_number(text: str) -> float | None:
    match = re.search(r"([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)", text)
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return None


def parse_percent_near(text: str, keywords: tuple[str, ...]) -> float | None:
    lower = text.lower()
    for keyword in keywords:
        idx = lower.find(keyword.lower())
        if idx < 0:
            continue
        window = text[max(0, idx - 80) : idx + 180]
        match = re.search(r"([+-]?[0-9]+(?:\.[0-9]+)?)\s*%", window)
        if match:
            return float(match.group(1)) / 100.0
    return None


def direction_from_text(text: str) -> tuple[str, float]:
    lower = text.lower()
    up_terms = ("raise", "raised", "higher", "increase", "increased", "growth", "beat", "above", "improved", "strong")
    down_terms = ("cut", "lower", "decrease", "declined", "miss", "below", "weaker", "headwind")
    up = sum(lower.count(term) for term in up_terms)
    down = sum(lower.count(term) for term in down_terms)
    if up > down:
        return "up", min(0.5 + up * 0.05, 0.85)
    if down > up:
        return "down", min(0.5 + down * 0.05, 0.85)
    return "unknown", 0.35


def extract_signals_from_evidence(ticker: str, row: dict[str, Any]) -> list[dict[str, Any]]:
    text = re.sub(r"\s+", " ", str(row.get("text_excerpt") or "")).strip()
    lower = text.lower()
    if not text:
        return []
    source_type = str(row.get("source_type") or "")
    confidence_base = 0.58 if source_type in PRIMARY_SOURCE_TYPES else 0.48
    if row.get("quality_score") is not None:
        confidence_base = max(confidence_base, min(float(row["quality_score"]), 0.88))
    direction, tone_strength = direction_from_text(text)
    if source_type == "fundamentals" and direction == "unknown":
        available_metrics = [
            metric
            for metric in ("revenue", "net_income", "eps", "gross_margin", "fcf")
            if re.search(rf"{metric}=(-?(?!none\b)[0-9][0-9,\.]*)", lower)
        ]
        if len(available_metrics) >= 2:
            direction = "up"
            tone_strength = max(tone_strength, 0.62)
    candidates: list[tuple[str, str, str]] = []
    if any(token in lower for token in ("guidance", "outlook", "expects", "forecast", "forecast for growth", "exceeded estimates")):
        candidates.append(("guidance_raise" if direction != "down" else "guidance_cut", "revenue", "regex_numeric"))
    if "revenue" in lower or "net sales" in lower or "top line" in lower:
        candidates.append(("revenue_surprise", "revenue", "regex_numeric"))
    if "eps" in lower or "earnings per share" in lower or "bottom line" in lower or "earnings" in lower:
        candidates.append(("eps_surprise", "eps", "regex_numeric"))
    if "gross margin" in lower or "margin" in lower:
        candidates.append(("margin_guidance", "margin", "regex_numeric"))
    if "capex" in lower or "capital expenditure" in lower:
        candidates.append(("capex_guidance", "capex", "regex_numeric"))
    if any(token in lower for token in ("target price", "price target")):
        candidates.append(("broker_target_revision", "target_price", "broker_report_parse"))
    if "price target" in lower or "target" in lower and "bank of america" in lower:
        candidates.append(("broker_target_revision", "target_price", "broker_report_parse"))
    if any(token in lower for token in ("estimate", "revision", "analyst")) and ("eps" in lower or "earnings" in lower):
        candidates.append(("broker_eps_revision", "eps", "broker_report_parse"))
    if any(token in lower for token in ("transcript", "q&a", "management said")):
        candidates.append(("transcript_tone_shift", "tone", "llm_extraction"))
    if not candidates and any(token in lower for token in ("beat", "beats", "better-than-expected", "blowout earnings", "solid beats")):
        candidates.append(("earnings_surprise", "earnings", "regex_numeric"))
    signals = []
    for signal_type, metric, method in candidates:
        if signal_type not in SIGNAL_TYPES:
            continue
        percent = parse_percent_near(text, (metric, signal_type.replace("_", " "), "guidance", "revenue", "eps", "margin"))
        current_value = parse_first_number(text)
        strength = min(0.95, max(tone_strength, abs(percent or 0.0) * 2.4 if percent is not None else 0.0, confidence_base))
        signal_direction = direction
        if signal_direction == "unknown" and signal_type in {"revenue_surprise", "eps_surprise", "earnings_surprise", "guidance_raise"}:
            signal_direction = "up" if any(token in lower for token in ("beat", "beats", "above", "increased", "growth", "exceeded", "better-than-expected", "strong")) else "unknown"
        if signal_type == "broker_target_revision" and signal_direction == "unknown":
            signal_direction = "up" if any(token in lower for token in ("reset", "raises", "raised", "higher")) else "unknown"
        signals.append(
            {
                "signal_id": stable_signal_id(ticker, signal_type, row.get("evidence_id"), metric, text),
                "ticker": ticker,
                "market": market_for_ticker(ticker),
                "period": None,
                "signal_type": signal_type,
                "metric": metric,
                "current_value": current_value,
                "previous_value": None,
                "consensus_value": None,
                "surprise_pct": percent,
                "direction": signal_direction,
                "strength": round(strength, 3),
                "source_evidence_id": row.get("evidence_id"),
                "source_type": source_type,
                "extraction_method": method,
                "confidence": round(min(0.92, confidence_base + (0.06 if percent is not None else 0.0)), 3),
                "metadata": {
                    "source_key": row.get("source_key"),
                    "source_quality": row.get("source_quality"),
                    "evidence_quality_score": row.get("quality_score"),
                    "excerpt": text[:600],
                    "not_official_consensus": True,
                },
            }
        )
    return signals


def upsert_proxy_signal(conn: sqlite3.Connection, signal: dict[str, Any]) -> None:
    ensure_proxy_signal_table(conn)
    conn.execute(
        """
        INSERT INTO proxy_signal_items (
            signal_id, ticker, market, period, signal_type, metric, current_value,
            previous_value, consensus_value, surprise_pct, direction, strength,
            source_evidence_id, source_type, extraction_method, confidence, created_at,
            metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(signal_id) DO UPDATE SET
            direction=excluded.direction,
            strength=excluded.strength,
            confidence=excluded.confidence,
            metadata_json=excluded.metadata_json
        """,
        (
            signal["signal_id"],
            signal["ticker"],
            signal.get("market"),
            signal.get("period"),
            signal["signal_type"],
            signal.get("metric"),
            signal.get("current_value"),
            signal.get("previous_value"),
            signal.get("consensus_value"),
            signal.get("surprise_pct"),
            signal.get("direction"),
            signal.get("strength"),
            signal.get("source_evidence_id"),
            signal.get("source_type"),
            signal.get("extraction_method"),
            signal.get("confidence"),
            now_ts(),
            json.dumps(signal.get("metadata") or {}, ensure_ascii=False, sort_keys=True, default=str),
        ),
    )


def aggregate_signal_quality(signals: list[dict[str, Any]]) -> tuple[str, bool, str]:
    valid = [item for item in signals if item.get("direction") in {"up", "down"} and item.get("source_evidence_id")]
    if not valid:
        return "invalid", False, "no_valid_proxy_signals"
    directions = {item["direction"] for item in valid}
    if len(directions) > 1:
        return "invalid", False, "conflicting_proxy_signal_directions"
    evidence_ids = {item.get("source_evidence_id") for item in valid if item.get("source_evidence_id")}
    source_types = {item.get("source_type") for item in valid if item.get("source_type")}
    primary_count = sum(1 for item in valid if item.get("source_type") in PRIMARY_SOURCE_TYPES)
    avg_conf = sum(float(item.get("confidence") or 0.0) for item in valid) / len(valid)
    if len(valid) >= 2 and primary_count >= 1 and len(evidence_ids) >= 2 and avg_conf >= 0.7:
        return "strong", True, "multi_signal_primary_supported_internal_proxy"
    if primary_count >= 1 and avg_conf >= 0.55:
        return "medium", False, "primary_signal_but_needs_more_independent_confirmation"
    if len(source_types) >= 1:
        return "weak", False, "proxy_signal_exists_but_not_promotion_grade"
    return "invalid", False, "proxy_signal_low_confidence"


def build_live_consensus_proxy(conn: sqlite3.Connection, ticker: str, limit: int = 16) -> dict[str, Any]:
    ensure_consensus_proxy_table(conn)
    ensure_proxy_signal_table(conn)
    evidence_rows = live_evidence_for_proxy(conn, ticker, limit=limit)
    signals: list[dict[str, Any]] = []
    for row in evidence_rows:
        for signal in extract_signals_from_evidence(ticker, row):
            upsert_proxy_signal(conn, signal)
            signals.append(signal)
    quality, usable, quality_reason = aggregate_signal_quality(signals)
    anchor_rows = sorted(
        evidence_rows,
        key=lambda row: (
            source_type_rank(row.get("source_type")),
            -(float(row.get("quality_score") or 0.0)),
            -(proxy_signal_text_score(str(row.get("text_excerpt") or ""), row.get("metadata") or {})),
        ),
    )
    selected_evidence_ids: list[str] = []
    seen_evidence_ids: set[str] = set()
    for row in anchor_rows:
        evidence_id = row.get("evidence_id")
        if not evidence_id or evidence_id in seen_evidence_ids:
            continue
        seen_evidence_ids.add(evidence_id)
        selected_evidence_ids.append(evidence_id)
        if len(selected_evidence_ids) >= 8:
            break
    if signals:
        direction = next((item.get("direction") for item in signals if item.get("direction") in {"up", "down"}), "unknown")
        confidence = round(max(float(item.get("confidence") or 0.0) for item in signals), 3)
        text = " ".join(
            f"{ticker} {item['signal_type']} {item.get('metric') or ''} {item.get('direction') or ''}"
            for item in signals[:6]
        )
        method = "guidance_change" if any(item["signal_type"] in {"guidance_raise", "guidance_cut"} for item in signals) else "earnings_surprise"
        proxy = build_consensus_revision_proxy(
            conn,
            f"{text} {'raised higher beat' if direction == 'up' else 'cut lower miss' if direction == 'down' else ''}",
            evidence_ids=selected_evidence_ids or [item["source_evidence_id"] for item in signals if item.get("source_evidence_id")][:8],
            ticker=ticker,
            method=method,
        )
        if proxy_quality_rank(proxy.get("proxy_quality")) < proxy_quality_rank(quality):
            proxy["proxy_quality"] = quality
            proxy["usable_for_promotion"] = usable
            proxy["quality_reason"] = quality_reason
        else:
            proxy["usable_for_promotion"] = bool(proxy.get("usable_for_promotion")) or usable
        proxy["confidence"] = max(proxy.get("confidence") or 0.0, confidence)
    else:
        proxy = {
            "ticker": ticker,
            "market": market_for_ticker(ticker),
            "is_official_consensus": False,
            "proxy_quality": "invalid",
            "usable_for_promotion": False,
            "evidence_ids": [],
            "note": "no live proxy signals extracted; internal proxy only",
        }
    proxy.update(
        {
            "is_official_consensus": False,
            "official_consensus_active": False,
            "proxy_signals": signals,
            "proxy_signal_count": len(signals),
            "quality_reason": proxy.get("quality_reason") or quality_reason,
            "source": "smr_proxy_extraction",
            "note": "internal consensus proxy only; not official sell-side consensus",
        }
    )
    return proxy
