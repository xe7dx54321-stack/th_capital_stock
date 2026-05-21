#!/usr/bin/env python3
"""Build a freshness snapshot for market data, sources, and key workflow outputs."""

from __future__ import annotations

import json
import sqlite3
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import ensure_auto_handoff
from smr_data_health import refresh_system_data_health
from smr_decision import record_agent_run
from smr_paths import env_or_project_path, relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run

DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")
OUTPUT_DIR = env_or_project_path("SMR_SYSTEM_HEALTH_DIR", "06_reports", "adhoc", "system_health")
SCRIPT_NAME = "build_data_freshness_snapshot.py"

DATA_CHECKS = (
    {"component": "A/H daily_bar", "kind": "market_data", "table": "daily_bar", "date_col": "trade_date", "warn_days": 1, "stale_days": 2},
    {"component": "US daily_bar", "kind": "market_data", "table": "us_daily_bar", "date_col": "trade_date", "warn_days": 1, "stale_days": 2},
)

SNAPSHOT_CHECKS = (
    {"component": "dynamic_pool_snapshot", "entity_type": "dynamic_pool_snapshot", "warn_hours": 14, "stale_hours": 30},
    {"component": "opportunity_radar_snapshot", "entity_type": "opportunity_radar_snapshot", "warn_hours": 14, "stale_hours": 30},
    {"component": "paper_trade_watchlist_snapshot", "entity_type": "paper_trade_watchlist_snapshot", "warn_hours": 14, "stale_hours": 30},
    {"component": "paper_watch_performance_snapshot", "entity_type": "paper_watch_performance_snapshot", "warn_hours": 14, "stale_hours": 30},
    {"component": "risk_monitor_snapshot", "entity_type": "risk_monitor_snapshot", "warn_hours": 24, "stale_hours": 48},
    {"component": "daily_reporting_snapshot", "entity_type": "daily_reporting_snapshot", "warn_hours": 24, "stale_hours": 48},
)

SOURCE_CHECKS = (
    {
        "component": "external_source_snapshot",
        "kind": "source_manifest",
        "source_type": "external_source_snapshot",
        "warn_days": 3,
        "stale_days": 5,
    },
)


def relation_exists(conn, name):
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name=?",
        (name,),
    ).fetchone()
    return bool(row)


def parse_date(value):
    text = str(value or "").strip()[:10]
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def parse_datetime(value):
    text = str(value or "").strip()
    if not text:
        return None
    for candidate in (text, text.replace("T", " ")[:19]):
        try:
            return datetime.fromisoformat(candidate)
        except ValueError:
            continue
    return None


def business_day_age(day, today):
    if day is None:
        return None
    if day >= today:
        return 0
    age = 0
    cursor = day
    while cursor < today:
        cursor = date.fromordinal(cursor.toordinal() + 1)
        if cursor.weekday() < 5:
            age += 1
    return age


def hour_age(ts, now):
    if ts is None:
        return None
    return max(0.0, (now - ts).total_seconds() / 3600.0)


def status_for_age(age, warn_threshold, stale_threshold):
    if age is None:
        return "missing"
    if age >= stale_threshold:
        return "stale"
    if age >= warn_threshold:
        return "warn"
    return "fresh"


def max_table_date(conn, table, date_col):
    if not relation_exists(conn, table):
        return None
    row = conn.execute(f"SELECT MAX({date_col}) FROM {table}").fetchone()
    return row[0] if row else None


def latest_registry_entry(conn, entity_type):
    if not relation_exists(conn, "task_registry_entity_latest"):
        return None
    row = conn.execute(
        """
        SELECT id, entity_id, status, created_at, relationships_json, payload_json
        FROM task_registry_entity_latest
        WHERE entity_type=?
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """,
        (entity_type,),
    ).fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "entity_id": row[1],
        "status": row[2],
        "created_at": row[3],
        "relationships": json.loads(row[4] or "{}"),
        "payload": json.loads(row[5] or "{}"),
    }


def latest_source_manifest(conn, source_type):
    if not relation_exists(conn, "source_manifest"):
        return None
    row = conn.execute(
        """
        SELECT COUNT(*), MAX(updated_at), MAX(created_at)
        FROM source_manifest
        WHERE source_type=? AND status='active'
        """,
        (source_type,),
    ).fetchone()
    if not row or not row[0]:
        return None
    return {
        "count": row[0],
        "updated_at": row[1],
        "created_at": row[2],
    }


def build_data_items(conn, today):
    items = []
    for check in DATA_CHECKS:
        latest_value = max_table_date(conn, check["table"], check["date_col"])
        latest_day = parse_date(latest_value)
        age = business_day_age(latest_day, today)
        status = status_for_age(age, check["warn_days"], check["stale_days"])
        items.append(
            {
                "component": check["component"],
                "kind": check["kind"],
                "latest": latest_value,
                "age_business_days": age,
                "status": status,
                "next_action": action_for_status(status, "market_data"),
            }
        )
    return items


def build_snapshot_items(conn, now):
    items = []
    for check in SNAPSHOT_CHECKS:
        entry = latest_registry_entry(conn, check["entity_type"])
        created_at = (entry or {}).get("created_at")
        age = hour_age(parse_datetime(created_at), now)
        status = status_for_age(age, check["warn_hours"], check["stale_hours"])
        items.append(
            {
                "component": check["component"],
                "kind": "workflow_snapshot",
                "latest": created_at,
                "latest_entry_id": (entry or {}).get("id"),
                "latest_entity_id": (entry or {}).get("entity_id"),
                "age_hours": round(age, 2) if age is not None else None,
                "status": status,
                "next_action": action_for_status(status, "workflow_snapshot"),
            }
        )
    return items


def build_source_items(conn, today):
    items = []
    for check in SOURCE_CHECKS:
        latest = latest_source_manifest(conn, check["source_type"])
        updated_at = (latest or {}).get("updated_at")
        age = business_day_age(parse_date(updated_at), today)
        status = status_for_age(age, check["warn_days"], check["stale_days"])
        items.append(
            {
                "component": check["component"],
                "kind": check["kind"],
                "latest": updated_at,
                "active_count": (latest or {}).get("count", 0),
                "age_business_days": age,
                "status": status,
                "next_action": action_for_status(status, "source_manifest"),
            }
        )
    return items


def action_for_status(status, kind):
    if status == "fresh":
        return "保持当前频率。"
    if status == "warn":
        if kind == "market_data":
            return "优先补跑对应市场数据采集，避免下游信号继续使用旧行情。"
        if kind == "source_manifest":
            return "刷新 source manifest，并对高分机会补抓公开来源。"
        return "补跑对应工作流，确认快照是否需要重建。"
    if status == "stale":
        if kind == "market_data":
            return "暂停依赖该市场的新机会判断，先修复数据采集。"
        if kind == "source_manifest":
            return "把来源抓取列为 P0，避免价格信号缺少事件支撑。"
        return "把该工作流列为 P0 补跑项。"
    return "检查表或快照是否缺失。"


def overall_status(items):
    statuses = Counter(item.get("status") for item in items)
    if statuses.get("missing") or statuses.get("stale"):
        return "stale"
    if statuses.get("warn"):
        return "warn"
    return "fresh"


def render_age(item):
    if item.get("age_business_days") is not None:
        return f"{item['age_business_days']}bd"
    if item.get("age_hours") is not None:
        return f"{item['age_hours']:.1f}h"
    return "-"


def write_markdown(path, payload):
    lines = [
        "# 数据与产物新鲜度快照",
        "",
        f"- generated_at: {payload['generated_at']}",
        f"- batch_date: {payload['batch_date']}",
        f"- overall_status: `{payload['overall_status']}`",
        "",
        "## 核心结论",
        "",
    ]
    for line in payload["overview_lines"]:
        lines.append(f"- {line}")
    lines.extend(
        [
            "",
            "## 明细",
            "",
            "| 组件 | 类型 | 最新时间 | 年龄 | 状态 | 下一步 |",
            "| --- | --- | --- | ---: | --- | --- |",
        ]
    )
    for item in payload["items"]:
        lines.append(
            "| {component} | {kind} | {latest} | {age} | {status} | {action} |".format(
                component=item["component"],
                kind=item["kind"],
                latest=item.get("latest") or "-",
                age=render_age(item),
                status=item.get("status") or "-",
                action=item.get("next_action") or "-",
            )
        )
    trusted = payload.get("trusted_data_health") or {}
    if trusted:
        lines.extend(
            [
                "",
                "## Freshness Gate 底座",
                "",
                f"- overall_status: `{trusted.get('overall_status') or '-'}`",
                f"- status_counts: `{trusted.get('status_counts') or {}}`",
                f"- blocking_counts: `{trusted.get('blocking_counts') or {}}`",
                "",
                "| source_key | market | data_type | last_data_timestamp | freshness_status | blocking_level | reason |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for row in trusted.get("items") or []:
            lines.append(
                "| {source_key} | {market} | {data_type} | {last_data_timestamp} | {freshness_status} | {blocking_level} | {reason} |".format(
                    source_key=row.get("source_key") or "-",
                    market=row.get("market") or "-",
                    data_type=row.get("data_type") or "-",
                    last_data_timestamp=row.get("last_data_timestamp") or "-",
                    freshness_status=row.get("freshness_status") or "-",
                    blocking_level=row.get("blocking_level") or "-",
                    reason=(row.get("staleness_reason") or "-").replace("|", "/"),
                )
            )
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main():
    now = datetime.now()
    today = now.date()
    generated_at = now.strftime("%Y-%m-%d %H:%M:%S")
    batch_date = generated_at[:10]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{batch_date}_data_freshness_snapshot.md"

    conn = sqlite3.connect(DB_PATH)
    try:
        items = [
            *build_data_items(conn, today),
            *build_snapshot_items(conn, now),
            *build_source_items(conn, today),
        ]
        trusted_data_health = refresh_system_data_health(conn)
        status = overall_status(items)
        if trusted_data_health.get("overall_status") == "blocked":
            status = "stale"
        elif trusted_data_health.get("overall_status") == "degraded" and status == "fresh":
            status = "warn"
        counts = dict(Counter(item["status"] for item in items))
        problem_items = [item for item in items if item.get("status") in {"missing", "warn", "stale"}]
        payload = {
            "generated_at": generated_at,
            "batch_date": batch_date,
            "overall_status": status,
            "status_counts": counts,
            "problem_count": len(problem_items),
            "items": items,
            "trusted_data_health": trusted_data_health,
            "overview_lines": [
                f"本轮检查 {len(items)} 个数据/产物组件，状态分布：{counts}。",
                f"需要关注的组件 {len(problem_items)} 个。",
                "这层只判断新鲜度，不替代研究结论；若市场数据过旧，下游机会判断应降权。",
            ],
        }
        write_markdown(output_path, payload)
        registry_entry = register_snapshot(
            conn,
            entity_type="data_freshness_snapshot",
            entity_id=batch_date,
            status=status,
            source=SCRIPT_NAME,
            relationships={"summary_rel_path": relative_to_project(output_path)},
            payload={**payload, "summary_rel_path": relative_to_project(output_path)},
            created_at=generated_at,
        )
        handoff_result = ensure_auto_handoff(
            conn,
            registry_entry,
            note="数据和产物新鲜度快照已生成，请同步到当前状态面板和调度候选。",
            created_by=SCRIPT_NAME,
        )
        record_agent_run(
            conn,
            agent_or_script=SCRIPT_NAME,
            status="success",
            entity_type="data_freshness_snapshot",
            entity_id=batch_date,
            data_health_snapshot=trusted_data_health,
            output_status=status,
        )
        conn.commit()
    finally:
        conn.close()

    log_run(
        SCRIPT_NAME,
        "success",
        "data freshness snapshot built",
        {
            "registry_entry_id": registry_entry["id"],
            "summary_rel_path": relative_to_project(output_path),
            "overall_status": status,
            "status_counts": counts,
            "problem_count": len(problem_items),
            "handoff_result": handoff_result["reason"],
            "handoff_id": handoff_result["handoff"]["handoff_id"] if handoff_result["handoff"] else None,
        },
    )
    print(f"Data freshness snapshot: {relative_to_project(output_path)}")
    print(f"  overall_status={status}")
    print(f"  status_counts={counts}")


if __name__ == "__main__":
    main()
