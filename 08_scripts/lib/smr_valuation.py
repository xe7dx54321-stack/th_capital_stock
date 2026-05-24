#!/usr/bin/env python3
"""Lightweight valuation snapshot v2 for promotion-aware research checks."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any

from smr_paths import project_path


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _dumps(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, sort_keys=True, default=str)


def _loads(raw: str | None, fallback: Any) -> Any:
    if raw in (None, ""):
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


VALUATION_PEER_SET_PATH = project_path("00_control", "valuation_peer_sets.json")
HISTORICAL_METRIC_PRIORITY = ("ps_ttm", "pb", "pe_ttm", "ev_ebitda_ttm")
HISTORICAL_MIN_SAMPLE = 60


def _as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_trade_date(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text[:19] if " " in text else text[:10], fmt)
        except ValueError:
            continue
    return None


def load_peer_set_config(path: Any | None = None) -> dict[str, Any]:
    config_path = path or VALUATION_PEER_SET_PATH
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, AttributeError):
        return {"peer_sets": {}, "ticker_to_peer_set": {}}


def peer_set_definition(ticker: str, config: dict[str, Any] | None = None) -> tuple[str | None, dict[str, Any]]:
    config = config or load_peer_set_config()
    ticker_key = str(ticker or "").upper()
    peer_set_id = (config.get("ticker_to_peer_set") or {}).get(ticker_key)
    if not peer_set_id:
        return None, {}
    peer_set = dict((config.get("peer_sets") or {}).get(peer_set_id) or {})
    return peer_set_id, peer_set


def ensure_valuation_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS valuation_snapshot (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            market TEXT,
            generated_at TEXT NOT NULL,
            valuation_available INTEGER NOT NULL DEFAULT 0,
            current_price REAL,
            market_cap REAL,
            pe_ttm REAL,
            ps_ttm REAL,
            pb REAL,
            historical_percentile REAL,
            peer_comparison_json TEXT NOT NULL DEFAULT '{}',
            valuation_status TEXT NOT NULL,
            missing_data_json TEXT NOT NULL DEFAULT '[]',
            allowed_usage TEXT NOT NULL,
            metadata_json TEXT NOT NULL DEFAULT '{}'
        )
        """
    )
    columns = {row[1] for row in conn.execute("PRAGMA table_info(valuation_snapshot)").fetchall()}
    additions = {
        "ev_ebitda_ttm": "REAL",
        "historical_percentile_1y": "REAL",
        "historical_percentile_3y": "REAL",
        "historical_percentile_5y": "REAL",
        "peer_set_json": "TEXT NOT NULL DEFAULT '[]'",
        "peer_percentile": "REAL",
        "broker_target_price": "REAL",
        "broker_forward_eps_proxy": "REAL",
        "valuation_confidence": "REAL",
    }
    for column, ddl in additions.items():
        if column not in columns:
            conn.execute(f"ALTER TABLE valuation_snapshot ADD COLUMN {column} {ddl}")


def market_for_ticker(ticker: str | None) -> str | None:
    text = str(ticker or "")
    if text.endswith((".SZ", ".SH", ".BJ")):
        return "A"
    if text.endswith(".HK"):
        return "H"
    if text:
        return "US"
    return None


def relation_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name=?", (name,)).fetchone()
    return bool(row)


def table_columns(conn: sqlite3.Connection, name: str) -> set[str]:
    if not relation_exists(conn, name):
        return set()
    return {row[1] for row in conn.execute(f"PRAGMA table_info({name})").fetchall()}


def latest_daily_price(conn: sqlite3.Connection, ticker: str, market: str | None) -> tuple[float | None, str | None]:
    if market == "US" and relation_exists(conn, "us_daily_bar"):
        columns = table_columns(conn, "us_daily_bar")
        ticker_column = "ts_code" if "ts_code" in columns else "symbol"
        row = conn.execute(
            f"SELECT close, trade_date FROM us_daily_bar WHERE {ticker_column}=? ORDER BY trade_date DESC LIMIT 1",
            (ticker,),
        ).fetchone()
        return (float(row[0]), row[1]) if row and row[0] is not None else (None, None)
    if relation_exists(conn, "daily_bar"):
        row = conn.execute(
            "SELECT close, trade_date FROM daily_bar WHERE ts_code=? ORDER BY trade_date DESC LIMIT 1",
            (ticker,),
        ).fetchone()
        return (float(row[0]), row[1]) if row and row[0] is not None else (None, None)
    return None, None


def latest_factor(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    if not relation_exists(conn, "factor_daily"):
        return {}
    columns = table_columns(conn, "factor_daily")
    wanted = [col for col in ("pe_ttm", "ps_ttm", "pb", "total_mv", "market_cap", "ev_ebitda_ttm") if col in columns]
    if wanted:
        row = conn.execute(
            f"SELECT {', '.join(wanted)}, trade_date FROM factor_daily WHERE ts_code=? ORDER BY trade_date DESC LIMIT 1",
            (ticker,),
        ).fetchone()
        if not row:
            return {}
        values = {wanted[index]: row[index] for index in range(len(wanted))}
        values["factor_trade_date"] = row[len(wanted)]
        return values
    if {"factor_name", "factor_value", "trade_date", "ts_code"}.issubset(columns):
        rows = conn.execute(
            """
            SELECT factor_name, factor_value, trade_date
            FROM factor_daily
            WHERE ts_code=?
            ORDER BY trade_date DESC
            """,
            (ticker,),
        ).fetchall()
        if not rows:
            return {}
        latest_date = rows[0][2]
        values = {"factor_trade_date": latest_date}
        for name, value, trade_date in rows:
            if trade_date != latest_date:
                continue
            key = str(name or "").lower()
            if key in {"pe_ttm", "ps_ttm", "pb", "total_mv", "market_cap", "ev_ebitda_ttm"}:
                values[key] = value
        return values
    return {}


def historical_factor_values(conn: sqlite3.Connection, ticker: str, metric: str, limit: int = 900) -> list[float]:
    if not relation_exists(conn, "factor_daily"):
        return []
    columns = table_columns(conn, "factor_daily")
    values: list[float] = []
    if metric in columns:
        rows = conn.execute(
            f"""
            SELECT {metric}
            FROM factor_daily
            WHERE ts_code=? AND {metric} IS NOT NULL
            ORDER BY trade_date DESC
            LIMIT ?
            """,
            (ticker, max(1, int(limit))),
        ).fetchall()
        values = [_as_float(row[0]) for row in rows]
    elif {"factor_name", "factor_value", "trade_date", "ts_code"}.issubset(columns):
        rows = conn.execute(
            """
            SELECT factor_value
            FROM factor_daily
            WHERE ts_code=? AND lower(factor_name)=? AND factor_value IS NOT NULL
            ORDER BY trade_date DESC
            LIMIT ?
            """,
            (ticker, metric.lower(), max(1, int(limit))),
        ).fetchall()
        values = [_as_float(row[0]) for row in rows]
    return [value for value in values if value is not None]


def historical_price_count(conn: sqlite3.Connection, ticker: str, market: str | None, limit: int = 900) -> int:
    if market == "US" and relation_exists(conn, "us_daily_bar"):
        columns = table_columns(conn, "us_daily_bar")
        ticker_column = "ts_code" if "ts_code" in columns else "symbol"
        row = conn.execute(
            f"SELECT COUNT(*) FROM (SELECT trade_date FROM us_daily_bar WHERE {ticker_column}=? ORDER BY trade_date DESC LIMIT ?)",
            (ticker, max(1, int(limit))),
        ).fetchone()
        return int(row[0]) if row else 0
    if relation_exists(conn, "daily_bar"):
        row = conn.execute(
            "SELECT COUNT(*) FROM (SELECT trade_date FROM daily_bar WHERE ts_code=? ORDER BY trade_date DESC LIMIT ?)",
            (ticker, max(1, int(limit))),
        ).fetchone()
        return int(row[0]) if row else 0
    return 0


def build_historical_valuation(conn: sqlite3.Connection, ticker: str, factor: dict[str, Any], *, lookback_years: int = 3) -> dict[str, Any]:
    market = market_for_ticker(ticker)
    limit = max(60, lookback_years * 252)
    price_samples = historical_price_count(conn, ticker, market, limit=limit)
    metrics: dict[str, Any] = {}
    missing_reasons: list[str] = []
    available_percentiles: list[float] = []
    for metric in HISTORICAL_METRIC_PRIORITY:
        current = _as_float(factor.get(metric))
        if current is None:
            metrics[metric] = {"status": "missing", "reason": f"{metric}_missing"}
            missing_reasons.append(f"{metric}_missing")
            continue
        if metric == "pe_ttm" and current <= 0:
            metrics[metric] = {"current": current, "status": "not_meaningful", "reason": "negative_or_missing_earnings"}
            missing_reasons.append("pe_ttm_not_meaningful")
            continue
        samples = [value for value in historical_factor_values(conn, ticker, metric, limit=limit) if value is not None]
        if metric == "pe_ttm":
            samples = [value for value in samples if value > 0]
        if len(samples) < HISTORICAL_MIN_SAMPLE:
            metrics[metric] = {
                "current": current,
                "sample_count": len(samples),
                "status": "missing",
                "reason": "sample_insufficient",
            }
            missing_reasons.append(f"{metric}_sample_insufficient")
            continue
        below_or_equal = sum(1 for value in samples if value <= current)
        percentile = round(below_or_equal / len(samples), 4)
        metrics[metric] = {
            "current": current,
            "percentile": percentile,
            "sample_count": len(samples),
            "status": "available",
        }
        available_percentiles.append(percentile)
    if available_percentiles:
        status = "available" if len(available_percentiles) >= 2 else "partial"
    elif price_samples <= 1:
        status = "missing"
        missing_reasons.append("price_history_missing")
    else:
        status = "missing"
    return {
        "status": status,
        "lookback_years": lookback_years,
        "price_sample_count": price_samples,
        "metrics": metrics,
        "missing_reasons": sorted(set(missing_reasons)),
        "primary_percentile": available_percentiles[0] if available_percentiles else None,
    }


def latest_consensus_proxy(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    if not relation_exists(conn, "consensus_revision_proxy"):
        return {}
    columns = table_columns(conn, "consensus_revision_proxy")
    required = {"ticker", "confidence", "source_evidence_ids_json", "is_official_consensus", "created_at"}
    if not required.issubset(columns):
        return {}
    row = conn.execute(
        """
        SELECT period, confidence, source_evidence_ids_json, is_official_consensus,
               current_value, proxy_quality, usable_for_promotion, metadata_json
        FROM consensus_revision_proxy
        WHERE ticker=?
        ORDER BY datetime(created_at) DESC, id DESC
        LIMIT 1
        """,
        (ticker,),
    ).fetchone()
    if not row:
        return {}
    return {
        "period": row[0],
        "confidence": _as_float(row[1]) or 0.0,
        "source_evidence_ids": _loads(row[2], []),
        "is_official_consensus": bool(row[3]),
        "current_value": _as_float(row[4]),
        "proxy_quality": row[5],
        "usable_for_promotion": bool(row[6]),
        "metadata": _loads(row[7], {}),
    }


def build_forward_eps_snapshot(conn: sqlite3.Connection, ticker: str, fundamentals: dict[str, Any]) -> dict[str, Any]:
    proxy = latest_consensus_proxy(conn, ticker)
    evidence_ids = [str(item) for item in proxy.get("source_evidence_ids") or [] if str(item).strip()]
    value = _as_float(proxy.get("current_value"))
    if value is None:
        value = _as_float(fundamentals.get("eps_diluted")) or _as_float(fundamentals.get("eps_basic"))
    if value is not None and evidence_ids and not proxy.get("is_official_consensus"):
        confidence = max(float(proxy.get("confidence") or 0.0), 0.55)
        if str(proxy.get("proxy_quality") or "").lower() == "strong":
            confidence = max(confidence, 0.61)
        allowed_usage = "supporting_evidence" if confidence >= 0.6 else "context_only"
        return {
            "status": "proxy",
            "value": value,
            "currency": "HKD" if str(ticker).endswith(".HK") else None,
            "period": proxy.get("period") or "next_fiscal_period_proxy",
            "source": "internal_proxy",
            "source_evidence_ids": evidence_ids,
            "confidence": round(confidence, 3),
            "is_official_consensus": False,
            "allowed_usage": allowed_usage,
            "proxy_quality": proxy.get("proxy_quality"),
            "note": "internal proxy EPS only; not official sell-side consensus",
        }
    if value is not None:
        return {
            "status": "proxy",
            "value": value,
            "currency": "HKD" if str(ticker).endswith(".HK") else None,
            "period": "latest_fundamentals_eps_proxy",
            "source": "fundamentals_eps_proxy",
            "source_evidence_ids": [],
            "confidence": 0.45,
            "is_official_consensus": False,
            "allowed_usage": "context_only",
            "reason": "proxy_eps_missing_evidence_id",
            "note": "fundamentals EPS proxy only; not official sell-side consensus and not promotion support",
        }
    reason = "official_consensus_disabled_and_proxy_not_available"
    return {
        "status": "missing",
        "reason": reason,
        "is_official_consensus": False,
        "allowed_usage": "context_only",
    }


def build_peer_set_snapshot(conn: sqlite3.Connection, ticker: str, factor: dict[str, Any]) -> dict[str, Any]:
    peer_set_id, peer_set = peer_set_definition(ticker)
    if not peer_set_id:
        return {
            "peer_set_id": None,
            "peer_set_status": "missing",
            "peer_count_available": 0,
            "peer_count_required": 0,
            "peer_multiples": [],
            "peer_comparison_status": "missing",
            "peer_missing_reasons": ["peer_set_config_missing"],
        }
    tickers = [str(item).upper() for item in peer_set.get("tickers") or []]
    peers = [item for item in tickers if item != str(ticker or "").upper()]
    required = int(peer_set.get("required_min_peers") or 2)
    peer_multiples = []
    missing_reasons: list[str] = []
    for peer in peers:
        peer_market = market_for_ticker(peer)
        peer_price, peer_price_date = latest_daily_price(conn, peer, peer_market)
        peer_factor = latest_factor(conn, peer)
        data_status = "available"
        reasons = []
        if peer_price is None:
            reasons.append("peer_price_missing")
        if not any(peer_factor.get(metric) is not None for metric in peer_set.get("metrics") or []):
            reasons.append("peer_fundamentals_missing")
        if reasons:
            data_status = "missing"
            missing_reasons.extend(reasons)
        peer_multiples.append(
            {
                "ticker": peer,
                "price": peer_price,
                "price_trade_date": peer_price_date,
                "pe_ttm": peer_factor.get("pe_ttm"),
                "ps_ttm": peer_factor.get("ps_ttm"),
                "pb": peer_factor.get("pb"),
                "ev_ebitda_ttm": peer_factor.get("ev_ebitda_ttm"),
                "data_status": data_status,
                "missing_reasons": reasons,
            }
        )
    available = [item for item in peer_multiples if item["data_status"] == "available"]
    if len(available) >= required:
        status = "available"
        comparison_status = "supporting"
    elif available and peer_set.get("fallback_allowed"):
        status = "partial"
        comparison_status = "supporting"
        missing_reasons.append("peer_count_insufficient")
    else:
        status = "missing"
        comparison_status = "missing"
        missing_reasons.append("peer_count_insufficient")
    return {
        "peer_set_id": peer_set_id,
        "peer_set_status": status,
        "peer_count_available": len(available),
        "peer_count_required": required,
        "peer_multiples": peer_multiples,
        "peer_comparison_status": comparison_status,
        "peer_missing_reasons": sorted(set(missing_reasons)),
    }


def latest_fundamentals(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    try:
        from smr_fundamentals import latest_fundamentals_snapshot

        return latest_fundamentals_snapshot(conn, ticker)
    except Exception:
        return {}


def latest_valuation_snapshot(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    ensure_valuation_table(conn)
    row = conn.execute(
        """
        SELECT ticker, market, generated_at, valuation_available, current_price, market_cap,
               pe_ttm, ps_ttm, pb, historical_percentile, peer_comparison_json,
               valuation_status, missing_data_json, allowed_usage, metadata_json,
               ev_ebitda_ttm, historical_percentile_1y, historical_percentile_3y,
               historical_percentile_5y, peer_set_json, peer_percentile,
               broker_target_price, broker_forward_eps_proxy, valuation_confidence
        FROM valuation_snapshot
        WHERE ticker=?
        ORDER BY datetime(generated_at) DESC, id DESC
        LIMIT 1
        """,
        (ticker,),
    ).fetchone()
    if not row:
        return {}
    keys = [
        "ticker",
        "market",
        "generated_at",
        "valuation_available",
        "current_price",
        "market_cap",
        "pe_ttm",
        "ps_ttm",
        "pb",
        "historical_percentile",
        "peer_comparison_json",
        "valuation_status",
        "missing_data_json",
        "allowed_usage",
        "metadata_json",
        "ev_ebitda_ttm",
        "historical_percentile_1y",
        "historical_percentile_3y",
        "historical_percentile_5y",
        "peer_set_json",
        "peer_percentile",
        "broker_target_price",
        "broker_forward_eps_proxy",
        "valuation_confidence",
    ]
    data = dict(zip(keys, row))
    data["valuation_available"] = bool(data.get("valuation_available"))
    data["peer_comparison"] = _loads(data.pop("peer_comparison_json"), {})
    data["missing_data"] = _loads(data.pop("missing_data_json"), [])
    data["metadata"] = _loads(data.pop("metadata_json"), {})
    data["peer_set"] = _loads(data.pop("peer_set_json"), [])
    metadata = data.get("metadata") or {}
    inputs_used = metadata.get("inputs_used") or {}
    if inputs_used.get("peer_set"):
        data["peer_comparison"] = inputs_used.get("peer_set")
    data["price_trade_date"] = metadata.get("price_trade_date")
    data["price_status"] = metadata.get("price_status")
    data["peer_set_id"] = metadata.get("peer_set_id") or (data.get("peer_comparison") or {}).get("peer_set_id")
    data["peer_set_status"] = metadata.get("peer_set_status") or (data.get("peer_comparison") or {}).get("peer_set_status")
    data["peer_count_available"] = metadata.get("peer_count_available") or (data.get("peer_comparison") or {}).get("peer_count_available")
    data["peer_count_required"] = metadata.get("peer_count_required") or (data.get("peer_comparison") or {}).get("peer_count_required")
    data["historical_valuation"] = inputs_used.get("historical_valuation") or {}
    data["historical_percentile_status"] = metadata.get("historical_percentile_status") or (data["historical_valuation"].get("status") if data.get("historical_valuation") else None)
    data["forward_eps"] = inputs_used.get("forward_eps") or {}
    return data


def _daily_rows_for_market(health: dict[str, Any], market: str | None) -> list[dict[str, Any]]:
    return [
        item for item in health.get("items") or []
        if item.get("data_type") == "daily_bar" and (not market or item.get("market") in {market, "global"})
    ]


def build_valuation_snapshot(
    conn: sqlite3.Connection,
    ticker: str,
    data_health_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ensure_valuation_table(conn)
    market = market_for_ticker(ticker)
    current_price, price_date = latest_daily_price(conn, ticker, market)
    factor = latest_factor(conn, ticker)
    fundamentals = latest_fundamentals(conn, ticker)
    peer_snapshot = build_peer_set_snapshot(conn, ticker, factor)
    historical_snapshot = build_historical_valuation(conn, ticker, factor)
    forward_eps = build_forward_eps_snapshot(conn, ticker, fundamentals)
    health = data_health_snapshot or {}
    daily_rows = _daily_rows_for_market(health, market)
    stale_price = any(item.get("freshness_status") in {"stale", "missing"} for item in daily_rows)

    missing = []
    if current_price is None:
        missing.append("current_price")
    if "pe_ttm" not in factor:
        missing.append("pe_ttm")
    if "ps_ttm" not in factor:
        missing.append("ps_ttm")
    if "pb" not in factor:
        missing.append("pb")
    if not fundamentals:
        missing.append("fundamentals_snapshot")
    missing.append("official_consensus")
    if forward_eps.get("status") == "missing":
        missing.append("forward_eps")
    if historical_snapshot.get("status") == "missing":
        missing.append("historical_percentile")
    if peer_snapshot.get("peer_set_status") == "missing":
        missing.append("peer_set")
    if stale_price:
        missing.append("fresh_price")

    available = bool(current_price is not None or factor)
    has_basic_multiple = any(factor.get(key) is not None for key in ("pe_ttm", "ps_ttm", "pb"))
    peer_comparison: dict[str, Any] = peer_snapshot
    peer_set: list[str] = [item.get("ticker") for item in peer_snapshot.get("peer_multiples") or [] if item.get("ticker")]
    broker_forward_eps_proxy = forward_eps.get("value") if forward_eps.get("status") == "proxy" else None
    valuation_confidence = 0.0
    if current_price is not None:
        valuation_confidence += 0.25
    if has_basic_multiple:
        valuation_confidence += 0.3
    if peer_snapshot.get("peer_set_status") in {"available", "partial"}:
        valuation_confidence += 0.2
    if forward_eps.get("status") == "proxy":
        valuation_confidence += 0.25
    if historical_snapshot.get("status") in {"available", "partial"}:
        valuation_confidence += 0.15
    if fundamentals.get("freshness_status") in {"fresh", "degraded"}:
        valuation_confidence += 0.1

    if stale_price:
        valuation_status = "fresh_snapshot_price_stale"
        allowed_usage = "blocked_due_to_stale_price"
    elif (
        forward_eps.get("status") == "proxy"
        and peer_snapshot.get("peer_set_status") == "available"
        and historical_snapshot.get("status") == "available"
        and forward_eps.get("allowed_usage") != "context_only"
    ):
        valuation_status = "input_hardened"
        allowed_usage = "supporting_evidence"
    elif available and (current_price is not None or has_basic_multiple):
        valuation_status = "partial"
        allowed_usage = "supporting_evidence"
    else:
        valuation_status = "missing"
        allowed_usage = "context_only"

    snapshot = {
        "ticker": ticker,
        "market": market,
        "generated_at": _now(),
        "valuation_available": available,
        "current_price": current_price,
        "price_trade_date": price_date,
        "market_cap": factor.get("total_mv") or factor.get("market_cap"),
        "pe_ttm": factor.get("pe_ttm"),
        "ps_ttm": factor.get("ps_ttm"),
        "pb": factor.get("pb"),
        "ev_ebitda_ttm": factor.get("ev_ebitda_ttm"),
        "historical_percentile": historical_snapshot.get("primary_percentile"),
        "historical_percentile_1y": None,
        "historical_percentile_3y": historical_snapshot.get("primary_percentile"),
        "historical_percentile_5y": None,
        "peer_comparison": peer_comparison,
        "peer_set": peer_set,
        "peer_percentile": None,
        "broker_target_price": None,
        "broker_forward_eps_proxy": broker_forward_eps_proxy,
        "valuation_confidence": round(valuation_confidence, 2),
        "valuation_status": valuation_status,
        "missing_data": sorted(set(missing)),
        "allowed_usage": allowed_usage,
        "fundamentals_snapshot": fundamentals,
        "price_status": "stale" if stale_price else "fresh" if current_price is not None else "missing",
        "peer_set_id": peer_snapshot.get("peer_set_id"),
        "peer_set_status": peer_snapshot.get("peer_set_status"),
        "peer_count_available": peer_snapshot.get("peer_count_available"),
        "peer_count_required": peer_snapshot.get("peer_count_required"),
        "historical_valuation": historical_snapshot,
        "historical_percentile_status": historical_snapshot.get("status"),
        "forward_eps": forward_eps,
    }
    conn.execute(
        """
        INSERT INTO valuation_snapshot (
            ticker, market, generated_at, valuation_available, current_price, market_cap, pe_ttm,
            ps_ttm, pb, historical_percentile, peer_comparison_json, valuation_status,
            missing_data_json, allowed_usage, metadata_json, ev_ebitda_ttm,
            historical_percentile_1y, historical_percentile_3y, historical_percentile_5y,
            peer_set_json, peer_percentile, broker_target_price, broker_forward_eps_proxy,
            valuation_confidence
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ticker,
            market,
            snapshot["generated_at"],
            1 if available else 0,
            current_price,
            snapshot["market_cap"],
            snapshot["pe_ttm"],
            snapshot["ps_ttm"],
            snapshot["pb"],
            snapshot["historical_percentile"],
            _dumps(peer_comparison),
            valuation_status,
            _dumps(snapshot["missing_data"]),
            allowed_usage,
            _dumps(
                {
                    "price_trade_date": price_date,
                    "price_status": snapshot["price_status"],
                    "factor_trade_date": factor.get("factor_trade_date"),
                    "fundamentals_snapshot_id": fundamentals.get("snapshot_id"),
                    "fundamentals_status": fundamentals.get("freshness_status"),
                    "inputs_used": {
                        "price": bool(current_price is not None),
                        "basic_multiples": bool(has_basic_multiple),
                        "forward_eps": forward_eps,
                        "peer_set": peer_snapshot,
                        "historical_valuation": historical_snapshot,
                    },
                    "peer_set_id": peer_snapshot.get("peer_set_id"),
                    "peer_set_status": peer_snapshot.get("peer_set_status"),
                    "peer_count_available": peer_snapshot.get("peer_count_available"),
                    "peer_count_required": peer_snapshot.get("peer_count_required"),
                    "historical_percentile_status": historical_snapshot.get("status"),
                    "forward_eps": forward_eps,
                }
            ),
            snapshot["ev_ebitda_ttm"],
            None,
            None,
            None,
            _dumps(peer_set),
            None,
            None,
            broker_forward_eps_proxy,
            snapshot["valuation_confidence"],
        ),
    )
    return snapshot


def valuation_sub_blockers(snapshot: dict[str, Any] | None, fundamentals: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    snapshot = snapshot or {}
    fundamentals = fundamentals or snapshot.get("fundamentals_snapshot") or {}
    missing = set(snapshot.get("missing_data") or [])
    peer_comparison = snapshot.get("peer_comparison") or {}
    historical = snapshot.get("historical_valuation") or {}
    forward_eps = snapshot.get("forward_eps") or {}
    blockers: list[dict[str, Any]] = []
    if not snapshot:
        blockers.append({"code": "VALUATION_EVIDENCE_MISSING", "message": "valuation snapshot is missing"})
        snapshot = {
            "missing_data": ["forward_eps", "historical_percentile", "peer_set"],
            "valuation_confidence": 0.0,
        }
        missing = set(snapshot["missing_data"])
    if snapshot.get("allowed_usage") == "blocked_due_to_stale_price" or "fresh_price" in missing:
        blockers.append({"code": "PRICE_STALE", "message": "latest price is stale or daily_bar freshness gate failed"})
    if snapshot.get("valuation_status") in {"stale", "stale_price"}:
        blockers.append({"code": "VALUATION_STALE", "message": "valuation snapshot is stale and must be recomputed"})
    if fundamentals and fundamentals.get("freshness_status") not in {"fresh", "degraded", "explainable_missing"}:
        blockers.append({"code": "FUNDAMENTALS_STALE_FOR_VALUATION", "message": "fundamentals are stale or missing for valuation"})
    if forward_eps.get("status") == "missing" or (not snapshot.get("broker_forward_eps_proxy") and "forward_eps" in missing):
        blockers.append({"code": "FORWARD_EPS_MISSING", "message": "forward EPS proxy is missing; do not compute forward PE"})
    historical_status = historical.get("status") or snapshot.get("historical_percentile_status")
    if historical_status == "partial":
        blockers.append({"code": "HISTORICAL_PERCENTILE_PARTIAL", "message": "historical percentile is partial and supporting-only"})
    elif not snapshot.get("historical_percentile") and "historical_percentile" in missing:
        blockers.append({"code": "HISTORICAL_PERCENTILE_MISSING", "message": "historical valuation percentile is missing"})
    for reason in historical.get("missing_reasons") or []:
        if "price_history_missing" in reason:
            blockers.append({"code": "HISTORICAL_PRICE_HISTORY_MISSING", "message": "historical price history is missing"})
        elif "sample_insufficient" in reason:
            blockers.append({"code": "HISTORICAL_SAMPLE_INSUFFICIENT", "message": "historical valuation sample is insufficient"})
        elif "not_meaningful" in reason:
            blockers.append({"code": "HISTORICAL_METRIC_NOT_MEANINGFUL", "message": "historical metric is not meaningful"})
        elif "missing" in reason:
            blockers.append({"code": "HISTORICAL_FUNDAMENTALS_MISSING", "message": "historical valuation factor is missing"})
    peer_status = peer_comparison.get("peer_set_status") or snapshot.get("peer_set_status")
    peer_reasons = peer_comparison.get("peer_missing_reasons") or []
    if peer_status == "partial":
        blockers.append({"code": "PEER_COUNT_INSUFFICIENT", "message": "peer set is partial and supporting-only"})
    elif (not snapshot.get("peer_set") and "peer_set" in missing) or peer_status == "missing":
        blockers.append({"code": "PEER_SET_MISSING", "message": "auditable peer set is missing"})
    for reason in peer_reasons:
        code = {
            "peer_set_config_missing": "PEER_SET_CONFIG_MISSING",
            "peer_price_missing": "PEER_PRICE_MISSING",
            "peer_fundamentals_missing": "PEER_FUNDAMENTALS_MISSING",
            "peer_count_insufficient": "PEER_COUNT_INSUFFICIENT",
            "peer_data_missing": "PEER_DATA_MISSING",
        }.get(str(reason), "PEER_DATA_MISSING")
        blockers.append({"code": code, "message": f"peer set issue: {reason}"})
    if not any(snapshot.get(key) is not None for key in ("current_price", "pe_ttm", "ps_ttm", "pb", "broker_forward_eps_proxy")):
        blockers.append({"code": "VALUATION_EVIDENCE_MISSING", "message": "valuation has no usable price, multiple, or EPS evidence"})
    if float(snapshot.get("valuation_confidence") or 0.0) < 0.45:
        blockers.append({"code": "VALUATION_CONFIDENCE_LOW", "message": "valuation confidence is below supporting-evidence threshold"})
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for blocker in blockers:
        code = blocker.get("code")
        if code in seen:
            continue
        seen.add(code)
        deduped.append(blocker)
    return deduped


def diagnose_valuation_snapshot(
    conn: sqlite3.Connection,
    ticker: str,
    data_health_snapshot: dict[str, Any] | None = None,
    before: dict[str, Any] | None = None,
) -> dict[str, Any]:
    market = market_for_ticker(ticker)
    before_snapshot = before if before is not None else latest_valuation_snapshot(conn, ticker)
    fundamentals = latest_fundamentals(conn, ticker)
    current_price, price_date = latest_daily_price(conn, ticker, market)
    health = data_health_snapshot or {}
    daily_rows = _daily_rows_for_market(health, market)
    price_status = "missing" if current_price is None else "fresh"
    if any(row.get("freshness_status") in {"stale", "missing"} for row in daily_rows):
        price_status = "stale"
    snapshot_age_days = None
    if before_snapshot.get("generated_at"):
        try:
            snapshot_age_days = max(0.0, (datetime.now() - datetime.fromisoformat(str(before_snapshot["generated_at"]).replace("T", " ")[:19])).total_seconds() / 86400)
        except ValueError:
            snapshot_age_days = None
    temp_snapshot = dict(before_snapshot) if before_snapshot else {}
    if temp_snapshot:
        temp_snapshot.setdefault("missing_data", [])
    sub_blockers = valuation_sub_blockers(temp_snapshot, fundamentals)
    missing_inputs = sorted(
        {
            "forward_eps" if item["code"] == "FORWARD_EPS_MISSING" else
            "historical_percentile" if item["code"] == "HISTORICAL_PERCENTILE_MISSING" else
            "peer_set" if item["code"] == "PEER_SET_MISSING" else
            "fresh_price" if item["code"] == "PRICE_STALE" else
            "valuation_evidence" if item["code"] == "VALUATION_EVIDENCE_MISSING" else
            item["code"].lower()
            for item in sub_blockers
        }
    )
    return {
        "price_status": price_status,
        "price_trade_date": price_date,
        "current_price": current_price,
        "fundamentals_status": fundamentals.get("freshness_status") or "missing",
        "valuation_snapshot_age_days": round(snapshot_age_days, 2) if snapshot_age_days is not None else None,
        "missing_inputs": missing_inputs,
        "sub_blockers": [item["code"] for item in sub_blockers],
        "sub_blocker_details": sub_blockers,
        "fundamentals_snapshot_id": fundamentals.get("snapshot_id"),
        "allowed_usage": before_snapshot.get("allowed_usage"),
        "valuation_status": before_snapshot.get("valuation_status"),
        "peer_set_status": before_snapshot.get("peer_set_status") or (before_snapshot.get("peer_comparison") or {}).get("peer_set_status"),
        "peer_set_id": before_snapshot.get("peer_set_id") or (before_snapshot.get("peer_comparison") or {}).get("peer_set_id"),
        "historical_percentile_status": before_snapshot.get("historical_percentile_status") or (before_snapshot.get("historical_valuation") or {}).get("status"),
        "forward_eps_status": (before_snapshot.get("forward_eps") or {}).get("status") or ("proxy" if before_snapshot.get("broker_forward_eps_proxy") else "missing"),
    }
