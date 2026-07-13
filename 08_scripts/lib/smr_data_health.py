#!/usr/bin/env python3
"""Data freshness monitor and gate for trusted SMR research automation."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from smr_market_calendar import get_expected_latest_trading_day, get_missing_trading_sessions, iso_dates
from smr_paths import project_path
from smr_source_registry import load_source_registry, source_registry_snapshot
from smr_wiki import generate_execution_id

RULES_PATH = project_path("00_control", "data_freshness_rules.json")

FRESHNESS_STATUSES = {"fresh", "degraded", "stale", "missing", "disabled", "planned", "unknown"}
BLOCKING_LEVELS = {"none", "warn", "degrade", "block"}
BLOCKING_RANK = {"none": 0, "warn": 1, "degrade": 2, "block": 3}
GATE_RANK = {"pass": 0, "warn": 1, "degrade": 2, "block": 3}
CAPABILITY_RANK = {"allowed": 0, "allowed_with_warning": 1, "degraded": 2, "blocked": 3}


@dataclass(frozen=True)
class HealthClassification:
    """Semantic cause plus the legacy-compatible status used by existing gates."""

    condition: str
    freshness_status: str
    blocking_level: str
    reason: str


@dataclass
class FreshnessGateResult:
    status: str
    reasons: list[str]
    stale_sources: list[dict[str, Any]]
    missing_sources: list[dict[str, Any]]
    data_health_snapshot: dict[str, Any]
    allowed_actions: list[str]


def ensure_data_health_tables(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA busy_timeout=15000")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS data_source_health (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_key TEXT NOT NULL,
            market TEXT,
            asset_type TEXT,
            data_type TEXT NOT NULL,
            last_success_at TEXT,
            last_data_timestamp TEXT,
            expected_update_frequency TEXT,
            freshness_status TEXT NOT NULL,
            stale_after_minutes INTEGER,
            blocking_level TEXT NOT NULL,
            staleness_reason TEXT,
            affected_modules_json TEXT NOT NULL DEFAULT '[]',
            metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source_key, market, asset_type, data_type)
        );

        CREATE INDEX IF NOT EXISTS idx_data_source_health_status
        ON data_source_health(freshness_status, blocking_level, updated_at DESC);
        """
    )


def relation_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name=?",
        (name,),
    ).fetchone()
    return bool(row)


def table_columns(conn: sqlite3.Connection, name: str) -> set[str]:
    if not relation_exists(conn, name):
        return set()
    return {row[1] for row in conn.execute(f"PRAGMA table_info({name})").fetchall()}


def load_rules() -> dict[str, Any]:
    if RULES_PATH.exists():
        return json.loads(RULES_PATH.read_text(encoding="utf-8"))
    return {"data_freshness_rules": {}, "module_dependencies": {}}


def normalize_market(market: str | None) -> str:
    text = str(market or "global").strip().upper()
    if text in {"CN", "A", "SZ", "SH", "BJ"}:
        return "A"
    if text in {"HK", "H"}:
        return "H"
    if text in {"US", "USA"}:
        return "US"
    return text or "global"


def rule_for(data_type: str, market: str | None = None, rules: dict[str, Any] | None = None) -> dict[str, Any]:
    rules = rules or load_rules()
    data_rules = (rules.get("data_freshness_rules") or {}).get(data_type) or {}
    normalized_market = normalize_market(market)
    return dict(data_rules.get(normalized_market) or data_rules.get("global") or {})


def parse_dt(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    candidates = [text, text.replace("T", " ")[:19], text[:10] + " 00:00:00"]
    for candidate in candidates:
        try:
            return datetime.fromisoformat(candidate)
        except ValueError:
            continue
    return None


def parse_date(value: Any) -> date | None:
    dt_value = parse_dt(value)
    return dt_value.date() if dt_value else None


def minutes_since(value: Any, now: datetime | None = None) -> float | None:
    ts = parse_dt(value)
    if ts is None:
        return None
    now = now or datetime.now()
    return max(0.0, (now - ts).total_seconds() / 60.0)


def max_value(conn: sqlite3.Connection, table: str, column: str, where: str = "", params: tuple[Any, ...] = ()) -> Any:
    if not relation_exists(conn, table):
        return None
    query = f"SELECT MAX({column}) FROM {table}"
    if where:
        query += f" WHERE {where}"
    row = conn.execute(query, params).fetchone()
    return row[0] if row else None


def latest_registry_created_at(conn: sqlite3.Connection, source: str | None = None) -> str | None:
    if not relation_exists(conn, "task_registry_entry"):
        return None
    params: list[Any] = []
    query = "SELECT MAX(created_at) FROM task_registry_entry"
    if source:
        query += " WHERE source=?"
        params.append(source)
    row = conn.execute(query, params).fetchone()
    return row[0] if row else None


def source_registry_planned_or_disabled(data_type: str, source_key: str) -> str | None:
    registry = load_source_registry()
    if source_key in registry:
        status = registry[source_key].get("status")
        if status in {"planned", "disabled", "deprecated", "error"}:
            return status
    for item in registry.values():
        if item.get("source_key") == source_key or item.get("data_type") == data_type:
            status = item.get("status")
            if status in {"planned", "disabled", "deprecated", "error"}:
                return status
    return None


def discover_source_timestamps(conn: sqlite3.Connection, data_type: str, market: str | None, source_key: str) -> tuple[str | None, str | None, dict[str, Any]]:
    normalized_market = normalize_market(market)
    metadata: dict[str, Any] = {}
    if data_type == "daily_bar":
        if normalized_market == "US":
            latest = max_value(conn, "us_daily_bar", "trade_date")
            expected = get_expected_latest_trading_day("US")
            actual = parse_date(latest)
            missing = get_missing_trading_sessions("US", actual, expected)
            return latest, latest, {
                "table": "us_daily_bar",
                "freshness_basis": "market_calendar",
                "expected_latest_trading_day": expected.isoformat(),
                "actual_latest_trading_day": actual.isoformat() if actual else None,
                "missing_sessions": iso_dates(missing),
            }
        where = ""
        params: tuple[Any, ...] = ()
        if normalized_market in {"A", "H"}:
            where = "market=?"
            params = (normalized_market,)
        latest = max_value(conn, "daily_bar", "trade_date", where, params)
        expected = get_expected_latest_trading_day(normalized_market)
        actual = parse_date(latest)
        missing = get_missing_trading_sessions(normalized_market, actual, expected)
        return latest, latest, {
            "table": "daily_bar",
            "market": normalized_market,
            "freshness_basis": "market_calendar",
            "expected_latest_trading_day": expected.isoformat(),
            "actual_latest_trading_day": actual.isoformat() if actual else None,
            "missing_sessions": iso_dates(missing),
        }
    if data_type == "news":
        latest = max_value(
            conn,
            "market_event",
            "COALESCE(publish_time, created_at)",
            "event_family LIKE ? OR event_type LIKE ?",
            ("%news%", "%news%"),
        )
        if latest is None:
            latest = max_value(conn, "source_manifest", "updated_at", "source_type IN (?, ?)", ("news_article", "news_search"))
        return latest, latest, {"tables": ["market_event", "source_manifest"]}
    if data_type == "filings":
        latest = None
        if relation_exists(conn, "market_event"):
            columns = table_columns(conn, "market_event")
            conditions = ["event_family LIKE ?"]
            params: list[Any] = ["%company_event%"]
            if "source_key" in columns:
                conditions.append("source_key IN (?, ?, ?, ?, ?)")
                params.extend(
                    [
                        "cninfo_announcement",
                        "hkex_announcement",
                        "sec_filing_document",
                        "sec_earnings_material",
                        "official_ir_material",
                    ]
                )
            if "source_kind" in columns:
                conditions.append("source_kind IN (?, ?, ?, ?, ?)")
                params.extend(
                    [
                        "announcement",
                        "cninfo_announcement",
                        "sec_filing_document",
                        "sec_earnings_material",
                        "official_ir_material",
                    ]
                )
            if "payload_json" in columns:
                conditions.append("json_extract(payload_json, '$.source_kind') IN (?, ?, ?, ?, ?)")
                params.extend(
                    [
                        "announcement",
                        "cninfo_announcement",
                        "sec_filing_document",
                        "sec_earnings_material",
                        "official_ir_material",
                    ]
                )
            latest = max_value(
                conn,
                "market_event",
                "COALESCE(publish_time, created_at)",
                " OR ".join(f"({condition})" for condition in conditions),
                tuple(params),
            )
        if latest is None:
            latest = max_value(
                conn,
                "source_manifest",
                "updated_at",
                "source_type IN (?, ?, ?, ?, ?)",
                ("announcement", "cninfo_announcement", "sec_filing_document", "sec_earnings_material", "official_ir_material"),
            )
        return latest, latest, {"tables": ["market_event", "source_manifest"]}
    if data_type == "fundamentals":
        latest_snapshot = max_value(conn, "fundamentals_snapshot", "created_at")
        latest_factor = max_value(conn, "factor_daily", "trade_date")
        latest = latest_snapshot or latest_factor
        return latest, latest, {"table": "fundamentals_snapshot" if latest_snapshot else "factor_daily"}
    if data_type == "consensus_revision":
        return None, None, {"source_registry_status": source_registry_planned_or_disabled(data_type, source_key) or "unknown"}
    latest = latest_registry_created_at(conn, source_key)
    return latest, latest, metadata


def classify_daily_bar_freshness(
    source_key: str,
    market: str | None,
    metadata: dict[str, Any],
    rule: dict[str, Any],
) -> tuple[str, str, str]:
    source_status = source_registry_planned_or_disabled("daily_bar", source_key)
    if source_status in {"planned", "disabled", "deprecated", "error"}:
        blocking = rule.get("blocking_level_when_missing") or rule.get("blocking_level_when_stale") or "block"
        return source_status, blocking, f"{source_key} 在 source registry 中为 {source_status}。"
    expected = metadata.get("expected_latest_trading_day")
    actual = metadata.get("actual_latest_trading_day")
    missing_sessions = metadata.get("missing_sessions") or []
    if not actual:
        blocking = rule.get("blocking_level_when_missing") or rule.get("blocking_level_when_stale") or "block"
        return "missing", blocking, f"daily_bar[{normalize_market(market)}] 没有找到任何行情日期。"
    if expected and str(actual) < str(expected):
        blocking = rule.get("blocking_level_when_stale") or "block"
        detail = f"缺少交易日 {', '.join(missing_sessions[:5])}" if missing_sessions else "实际行情日早于应有交易日"
        return "stale", blocking, f"daily_bar[{normalize_market(market)}] actual={actual} < expected={expected}；{detail}。"
    return "fresh", "none", ""


def classify_health_semantics(
    data_type: str,
    source_key: str,
    last_data_timestamp: str | None,
    stale_after_minutes: int | None,
    rule: dict[str, Any],
    now: datetime | None = None,
    collection_state: str | None = None,
) -> HealthClassification:
    """Explain why a source is healthy or unhealthy without changing legacy gates."""
    if collection_state == "market_closed":
        return HealthClassification("market_closed", "fresh", "none", "Market is closed; no update is due.")
    if collection_state == "source_not_due":
        return HealthClassification("source_not_due", "fresh", "none", "Source is not due for collection.")
    if collection_state == "fetch_failed":
        blocking = rule.get("blocking_level_when_fetch_failed") or "degrade"
        return HealthClassification("fetch_failed", "degraded", blocking, f"{source_key} collection failed.")
    if collection_state == "not_configured" or rule.get("configured") is False:
        blocking = rule.get("blocking_level_when_missing") or rule.get("blocking_level_when_stale") or "warn"
        return HealthClassification("not_configured", "missing", blocking, f"{data_type} is not configured.")

    configured_status = rule.get("freshness_status")
    source_status = source_registry_planned_or_disabled(data_type, source_key)
    if configured_status in {"planned", "disabled"}:
        blocking = rule.get("blocking_level_when_missing") or "degrade"
        if BLOCKING_RANK.get(blocking, 0) < BLOCKING_RANK["degrade"]:
            blocking = "degrade"
        return HealthClassification(configured_status, configured_status, blocking, f"{data_type} is {configured_status}.")
    if source_status in {"planned", "disabled", "deprecated", "error"}:
        if source_status == "error":
            blocking = rule.get("blocking_level_when_fetch_failed") or "degrade"
            return HealthClassification("fetch_failed", "degraded", blocking, f"{source_key} source registry reports an error.")
        blocking = rule.get("blocking_level_when_missing") or "degrade"
        return HealthClassification(source_status, source_status, blocking, f"{source_key} is {source_status} in the source registry.")

    age = minutes_since(last_data_timestamp, now=now)
    if age is None:
        blocking = rule.get("blocking_level_when_missing") or rule.get("blocking_level_when_stale") or "warn"
        return HealthClassification("missing_data", "missing", blocking, f"{data_type} has no recent data timestamp.")
    stale_after = stale_after_minutes or 1440
    stale_blocking = rule.get("blocking_level_when_stale") or "warn"
    if age > stale_after:
        return HealthClassification(
            "data_stale",
            "stale",
            stale_blocking,
            f"{data_type} exceeded stale_after_minutes={stale_after}; age is about {int(age)} minutes.",
        )
    if age > stale_after * 0.75:
        blocking = "warn" if stale_blocking == "block" else stale_blocking
        return HealthClassification(
            "nearing_stale",
            "degraded",
            blocking,
            f"{data_type} is nearing its stale threshold; age is about {int(age)} minutes.",
        )
    return HealthClassification("current", "fresh", "none", "")


def classify_freshness(
    data_type: str,
    source_key: str,
    last_data_timestamp: str | None,
    stale_after_minutes: int | None,
    rule: dict[str, Any],
    now: datetime | None = None,
) -> tuple[str, str, str]:
    result = classify_health_semantics(
        data_type=data_type,
        source_key=source_key,
        last_data_timestamp=last_data_timestamp,
        stale_after_minutes=stale_after_minutes,
        rule=rule,
        now=now,
    )
    return result.freshness_status, result.blocking_level, result.reason


def upsert_health_row(conn: sqlite3.Connection, row: dict[str, Any]) -> dict[str, Any]:
    ensure_data_health_tables(conn)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = {
        "source_key": row.get("source_key"),
        "market": row.get("market") or "global",
        "asset_type": row.get("asset_type") or "stock",
        "data_type": row.get("data_type"),
        "last_success_at": row.get("last_success_at"),
        "last_data_timestamp": row.get("last_data_timestamp"),
        "expected_update_frequency": row.get("expected_update_frequency"),
        "freshness_status": row.get("freshness_status") or "unknown",
        "stale_after_minutes": row.get("stale_after_minutes"),
        "blocking_level": row.get("blocking_level") or "warn",
        "staleness_reason": row.get("staleness_reason"),
        "affected_modules": row.get("affected_modules") or [],
        "metadata": row.get("metadata") or {},
        "updated_at": now,
    }
    conn.execute(
        """
        INSERT INTO data_source_health (
            source_key, market, asset_type, data_type, last_success_at, last_data_timestamp,
            expected_update_frequency, freshness_status, stale_after_minutes, blocking_level,
            staleness_reason, affected_modules_json, metadata_json, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_key, market, asset_type, data_type) DO UPDATE SET
            last_success_at=excluded.last_success_at,
            last_data_timestamp=excluded.last_data_timestamp,
            expected_update_frequency=excluded.expected_update_frequency,
            freshness_status=excluded.freshness_status,
            stale_after_minutes=excluded.stale_after_minutes,
            blocking_level=excluded.blocking_level,
            staleness_reason=excluded.staleness_reason,
            affected_modules_json=excluded.affected_modules_json,
            metadata_json=excluded.metadata_json,
            updated_at=excluded.updated_at
        """,
        (
            row["source_key"],
            row["market"],
            row["asset_type"],
            row["data_type"],
            row["last_success_at"],
            row["last_data_timestamp"],
            row["expected_update_frequency"],
            row["freshness_status"],
            row["stale_after_minutes"],
            row["blocking_level"],
            row["staleness_reason"],
            json.dumps(row["affected_modules"], ensure_ascii=False),
            json.dumps(row["metadata"], ensure_ascii=False, sort_keys=True),
            now,
            now,
        ),
    )
    return row


def update_data_source_health(
    conn: sqlite3.Connection,
    source_key: str,
    market: str | None,
    data_type: str,
    asset_type: str = "stock",
    rules: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rules = rules or load_rules()
    rule = rule_for(data_type, market, rules)
    source_key = rule.get("source_key") or source_key
    stale_after = int(rule.get("stale_after_minutes") or 1440)
    last_success_at, last_data_timestamp, metadata = discover_source_timestamps(conn, data_type, market, source_key)
    if data_type == "daily_bar" and metadata.get("freshness_basis") == "market_calendar":
        status, blocking, reason = classify_daily_bar_freshness(source_key, market, metadata, rule)
        if status == "fresh":
            expected = metadata.get("expected_latest_trading_day")
            condition = "market_closed" if rule.get("healthy_when_market_closed") and expected and str(expected) < date.today().isoformat() else "current"
        elif status == "stale":
            condition = "data_stale"
        elif status == "missing":
            condition = "missing_data"
        elif status == "error":
            condition = "fetch_failed"
        else:
            condition = status
    else:
        classification = classify_health_semantics(data_type, source_key, last_data_timestamp, stale_after, rule)
        status = classification.freshness_status
        blocking = classification.blocking_level
        reason = classification.reason
        condition = classification.condition
    row = {
        "source_key": source_key,
        "market": normalize_market(market),
        "asset_type": asset_type,
        "data_type": data_type,
        "last_success_at": last_success_at,
        "last_data_timestamp": last_data_timestamp,
        "expected_update_frequency": rule.get("expected_update_frequency") or ("daily_close" if data_type in {"daily_bar", "fundamentals"} else "intraday_batch"),
        "freshness_status": status,
        "stale_after_minutes": stale_after,
        "blocking_level": blocking,
        "staleness_reason": reason,
        "affected_modules": rule.get("affected_modules") or [],
        "metadata": {**metadata, "condition": condition, "rule": rule},
    }
    return upsert_health_row(conn, row)


def critical_health_specs(rules: dict[str, Any] | None = None) -> list[tuple[str, str, str]]:
    rules = rules or load_rules()
    specs: list[tuple[str, str, str]] = []
    data_rules = rules.get("data_freshness_rules") or {}
    for data_type, market_rules in data_rules.items():
        for market, rule in market_rules.items():
            source_key = (rule or {}).get("source_key") or data_type
            specs.append((source_key, market, data_type))
    return specs


def refresh_system_data_health(conn: sqlite3.Connection) -> dict[str, Any]:
    rules = load_rules()
    for source_key, market, data_type in critical_health_specs(rules):
        rule = rule_for(data_type, market, rules)
        stale_after = int(rule.get("stale_after_minutes") or 1440)
        affected_modules = rule.get("affected_modules") or []
        if data_type == "news":
            try:
                from smr_news_ingestion import update_news_health_rows

                update_news_health_rows(
                    conn,
                    stale_after_minutes=stale_after,
                    affected_modules=affected_modules,
                )
                continue
            except Exception:
                pass
        if data_type == "filings":
            try:
                from smr_filings_ingestion import update_filings_health_rows

                update_filings_health_rows(
                    conn,
                    stale_after_minutes=stale_after,
                    affected_modules=affected_modules,
                )
                continue
            except Exception:
                pass
        update_data_source_health(conn, source_key=source_key, market=market, data_type=data_type, rules=rules)
    return build_health_snapshot(health_rows(conn))


def health_rows(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    ensure_data_health_tables(conn)
    rows = conn.execute(
        """
        SELECT source_key, market, asset_type, data_type, last_success_at, last_data_timestamp,
               expected_update_frequency, freshness_status, stale_after_minutes, blocking_level,
               staleness_reason, affected_modules_json, metadata_json, updated_at
        FROM data_source_health
        ORDER BY data_type, market, source_key
        """
    ).fetchall()
    result = []
    for row in rows:
        result.append(
            {
                "source_key": row[0],
                "market": row[1],
                "asset_type": row[2],
                "data_type": row[3],
                "last_success_at": row[4],
                "last_data_timestamp": row[5],
                "expected_update_frequency": row[6],
                "freshness_status": row[7],
                "stale_after_minutes": row[8],
                "blocking_level": row[9],
                "staleness_reason": row[10],
                "affected_modules": json.loads(row[11] or "[]"),
                "metadata": json.loads(row[12] or "{}"),
                "updated_at": row[13],
            }
        )
    return result


def behavior_to_capability_status(behavior: str | None, row_blocking: str | None = None) -> str:
    value = str(behavior or "").strip().lower()
    if value in {"allow", "allowed", "pass"}:
        return "allowed"
    if value in {"allow_with_warning", "warn", "warning"}:
        return "allowed_with_warning"
    if value in {"degrade", "degraded"}:
        return "degraded"
    if value in {"block", "blocked"}:
        return "blocked"
    blocking = row_blocking or "none"
    return {
        "none": "allowed",
        "warn": "allowed_with_warning",
        "degrade": "degraded",
        "block": "blocked",
    }.get(blocking, "allowed_with_warning")


def capability_behavior_for(config: dict[str, Any], row: dict[str, Any]) -> str | None:
    data_type = row.get("data_type")
    freshness = row.get("freshness_status")
    if data_type == "daily_bar" and freshness in {"stale", "degraded", "missing", "unknown"}:
        return config.get("on_daily_bar_stale")
    if data_type == "consensus_revision" and freshness in {"planned", "disabled", "missing", "unknown"}:
        return config.get("on_consensus_revision_missing")
    if freshness in {"stale", "degraded"}:
        return config.get(f"on_{data_type}_stale")
    if freshness in {"missing", "planned", "disabled", "unknown"}:
        return config.get(f"on_{data_type}_missing") or config.get(f"on_{data_type}_stale")
    return None


def build_capability_status(rows: list[dict[str, Any]], rules: dict[str, Any] | None = None) -> dict[str, Any]:
    rules = rules or load_rules()
    matrix = rules.get("capability_matrix") or {}
    known_data_types = set((rules.get("data_freshness_rules") or {}).keys())
    by_type: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_type.setdefault(row.get("data_type") or "unknown", []).append(row)
    capabilities: dict[str, Any] = {}
    for capability, config in matrix.items():
        required = [item for item in config.get("required_data_types") or [] if item in known_data_types]
        optional = [item for item in config.get("optional_data_types") or [] if item in known_data_types]
        status = "allowed"
        reasons: list[str] = []
        impacted_rows: list[dict[str, Any]] = []
        for data_type in required + optional:
            source_rows = by_type.get(data_type) or []
            if not source_rows:
                row_status = behavior_to_capability_status(config.get(f"on_{data_type}_missing"), "warn")
                if CAPABILITY_RANK[row_status] > CAPABILITY_RANK[status]:
                    status = row_status
                reasons.append(f"{data_type}: 没有 data_source_health 记录。")
                continue
            for row in source_rows:
                freshness = row.get("freshness_status")
                if freshness == "fresh" and row.get("blocking_level") == "none":
                    continue
                behavior = capability_behavior_for(config, row)
                row_status = behavior_to_capability_status(behavior, row.get("blocking_level"))
                if CAPABILITY_RANK[row_status] > CAPABILITY_RANK[status]:
                    status = row_status
                impacted_rows.append(row)
                if row.get("staleness_reason"):
                    reasons.append(f"{data_type}[{row.get('market')}]: {row.get('staleness_reason')}")
        capabilities[capability] = {
            "status": status,
            "required_data_types": required,
            "optional_data_types": optional,
            "reasons": reasons,
            "impacted_sources": [
                {
                    "source_key": row.get("source_key"),
                    "market": row.get("market"),
                    "data_type": row.get("data_type"),
                    "freshness_status": row.get("freshness_status"),
                    "blocking_level": row.get("blocking_level"),
                    "staleness_reason": row.get("staleness_reason"),
                    "metadata": row.get("metadata") or {},
                }
                for row in impacted_rows
            ],
        }
    return capabilities


def build_health_snapshot(rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    blocking_counts: dict[str, int] = {}
    for row in rows:
        status_counts[row.get("freshness_status") or "unknown"] = status_counts.get(row.get("freshness_status") or "unknown", 0) + 1
        blocking_counts[row.get("blocking_level") or "none"] = blocking_counts.get(row.get("blocking_level") or "none", 0) + 1
    max_block = max((BLOCKING_RANK.get(row.get("blocking_level") or "none", 0) for row in rows), default=0)
    overall = "fresh"
    if max_block >= BLOCKING_RANK["block"]:
        overall = "blocked"
    elif max_block >= BLOCKING_RANK["degrade"]:
        overall = "degraded"
    elif max_block >= BLOCKING_RANK["warn"]:
        overall = "warn"
    capability_status = build_capability_status(rows)
    if capability_status:
        statuses = [item.get("status") for item in capability_status.values()]
        if statuses and all(status == "blocked" for status in statuses):
            overall = "blocked"
        elif any(status in {"blocked", "degraded", "allowed_with_warning"} for status in statuses):
            overall = "degraded"
        else:
            overall = "fresh"
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "overall_status": overall,
        "status_counts": status_counts,
        "blocking_counts": blocking_counts,
        "capability_status": capability_status,
        "items": rows,
        "source_registry_snapshot": source_registry_snapshot(),
    }


def get_system_data_health(conn: sqlite3.Connection, refresh: bool = True) -> dict[str, Any]:
    if refresh:
        return refresh_system_data_health(conn)
    rows = health_rows(conn)
    if not rows:
        return refresh_system_data_health(conn)
    return build_health_snapshot(rows)


def rows_for_module(rows: list[dict[str, Any]], module_name: str, required_data_types: list[str], market: str | None = None) -> list[dict[str, Any]]:
    normalized_market = normalize_market(market) if market else None
    selected = []
    for row in rows:
        if row.get("data_type") not in required_data_types:
            continue
        row_market = normalize_market(row.get("market"))
        if normalized_market and row_market not in {normalized_market, "GLOBAL"} and row_market != "global":
            continue
        affected = row.get("affected_modules") or []
        if module_name and affected and module_name not in affected:
            continue
        selected.append(row)
    return selected


def gate_status_from_rows(rows: list[dict[str, Any]], allow_degraded: bool = True) -> str:
    if not rows:
        return "warn"
    max_level = "none"
    for row in rows:
        blocking = row.get("blocking_level") or "none"
        if not allow_degraded and blocking == "degrade":
            blocking = "block"
        if BLOCKING_RANK.get(blocking, 0) > BLOCKING_RANK.get(max_level, 0):
            max_level = blocking
    return {"none": "pass", "warn": "warn", "degrade": "degrade", "block": "block"}.get(max_level, "warn")


def allowed_actions_for_status(status: str) -> list[str]:
    if status == "pass":
        return ["generate_observation", "generate_research", "generate_recommendation_candidate"]
    if status == "warn":
        return ["generate_observation", "generate_research", "generate_research_with_warning"]
    if status == "degrade":
        return ["generate_observation", "generate_research_with_warning"]
    return ["generate_data_warning", "generate_static_research_only"]


def check_freshness_gate(
    conn: sqlite3.Connection,
    module_name: str,
    required_data_types: list[str] | None = None,
    market: str | None = None,
    allow_degraded: bool = True,
    refresh: bool = True,
) -> FreshnessGateResult:
    rules = load_rules()
    required_data_types = required_data_types or ((rules.get("module_dependencies") or {}).get(module_name) or [])
    snapshot = get_system_data_health(conn, refresh=refresh)
    selected = rows_for_module(snapshot.get("items") or [], module_name, required_data_types, market=market)
    status = gate_status_from_rows(selected, allow_degraded=allow_degraded)
    stale = [row for row in selected if row.get("freshness_status") in {"stale", "degraded"}]
    missing = [row for row in selected if row.get("freshness_status") in {"missing", "disabled", "planned", "unknown"}]
    reasons = []
    for row in selected:
        reason = row.get("staleness_reason")
        if reason:
            reasons.append(f"{row.get('data_type')}[{row.get('market')}]: {reason}")
    if not selected:
        reasons.append(f"{module_name} 没有找到可用 data health 行。")
    return FreshnessGateResult(
        status=status,
        reasons=reasons,
        stale_sources=stale,
        missing_sources=missing,
        data_health_snapshot=snapshot,
        allowed_actions=allowed_actions_for_status(status),
    )


def gate_to_dict(gate: FreshnessGateResult | dict[str, Any] | None) -> dict[str, Any]:
    if gate is None:
        return {}
    if isinstance(gate, dict):
        return gate
    return asdict(gate)


def blocked_payload_for_gate(module_name: str, gate: FreshnessGateResult) -> dict[str, Any]:
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "mode": "paper_only",
        "module_name": module_name,
        "blocked_by_data": True,
        "freshness_gate_result": gate_to_dict(gate),
        "data_health_snapshot": gate.data_health_snapshot,
        "overview_lines": [
            f"{module_name} 已被 Freshness Gate 阻断：{'; '.join(gate.reasons[:3])}",
            "当前只允许生成数据告警或静态研究，不允许机会打分、买卖建议或纸面交易动作。",
        ],
    }


def new_agent_run_id(prefix: str = "agent_run") -> str:
    return generate_execution_id(prefix)
