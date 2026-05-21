#!/usr/bin/env python3
"""Build the daily trusted-system health report for SMR automation."""

from __future__ import annotations

import json
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import ensure_auto_handoff
from smr_data_diagnostics import diagnose_data_freshness
from smr_data_health import check_freshness_gate, gate_to_dict, refresh_system_data_health
from smr_decision import record_agent_run
from smr_paths import env_or_project_path, relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_source_registry import source_registry_snapshot

DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")
OUTPUT_DIR = env_or_project_path("SMR_SYSTEM_HEALTH_DIR", "06_reports", "adhoc", "system_health")
SCRIPT_NAME = "build_daily_system_health_report.py"

MODULE_GATES = {
    "opportunity_radar": ["daily_bar", "news", "filings", "consensus_revision"],
    "market_signal": ["daily_bar"],
    "paper_watch": ["daily_bar"],
    "risk_agent": ["daily_bar", "fundamentals"],
    "report_generation": ["daily_bar", "filings", "fundamentals", "consensus_revision"],
    "deep_market_scan": ["news", "filings", "fundamentals"],
}


def relation_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name=?",
        (name,),
    ).fetchone()
    return bool(row)


def load_json(raw_value: str | None, default: Any) -> Any:
    if raw_value in (None, ""):
        return default
    try:
        return json.loads(raw_value)
    except json.JSONDecodeError:
        return default


def status_counts_today(conn: sqlite3.Connection, table: str, status_col: str, date_col: str, today: str) -> dict[str, int]:
    if not relation_exists(conn, table):
        return {}
    rows = conn.execute(
        f"""
        SELECT {status_col}, COUNT(*)
        FROM {table}
        WHERE substr({date_col}, 1, 10)=?
        GROUP BY {status_col}
        """,
        (today,),
    ).fetchall()
    return {str(row[0] or "unknown"): int(row[1] or 0) for row in rows}


def latest_report_status_counts(conn: sqlite3.Connection, today: str) -> dict[str, int]:
    if not relation_exists(conn, "task_registry_entry"):
        return {}
    rows = conn.execute(
        """
        SELECT status, COUNT(*)
        FROM task_registry_entry
        WHERE entity_type='investment_report_snapshot'
          AND substr(created_at, 1, 10)=?
        GROUP BY status
        """,
        (today,),
    ).fetchall()
    return {str(row[0] or "unknown"): int(row[1] or 0) for row in rows}


def build_module_impacts(conn: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    impacts: dict[str, dict[str, Any]] = {}
    for module_name, required in MODULE_GATES.items():
        gate = check_freshness_gate(
            conn,
            module_name=module_name,
            required_data_types=required,
            allow_degraded=True,
            refresh=False,
        )
        impacts[module_name] = gate_to_dict(gate)
    return impacts


def overall_label(health: dict[str, Any], impacts: dict[str, dict[str, Any]]) -> str:
    capabilities = health.get("capability_status") or {}
    if capabilities:
        statuses = [item.get("status") for item in capabilities.values()]
        if statuses and all(status == "blocked" for status in statuses):
            return "BLOCKED"
        if any(status in {"blocked", "degraded", "allowed_with_warning"} for status in statuses):
            return "DEGRADED"
        return "FRESH"
    if any(gate.get("status") == "block" for gate in impacts.values()):
        return "BLOCKED"
    if health.get("overall_status") in {"blocked", "degraded", "warn"}:
        return "DEGRADED"
    if any(gate.get("status") in {"degrade", "warn"} for gate in impacts.values()):
        return "DEGRADED"
    return "FRESH"


def next_actions(health: dict[str, Any], source_snapshot: dict[str, Any]) -> list[str]:
    actions = []
    for row in health.get("items") or []:
        if row.get("blocking_level") == "block":
            actions.append(f"修复 {row.get('market')} {row.get('data_type')} 采集：{row.get('staleness_reason')}")
    disabled_keys = [item.get("source_key") for item in source_snapshot.get("disabled_or_planned") or []]
    if "consensus_revision" in disabled_keys:
        actions.append("接入或明确替代 consensus_revision，否则所有预期修正判断只能标为缺失。")
    if not actions:
        actions.append("保持当前调度，并抽查最新报告的 evidence/lint 元数据。")
    return actions[:8]


def render_markdown(payload: dict[str, Any]) -> str:
    source_snapshot = payload.get("source_registry_snapshot") or {}
    health = payload.get("data_health_snapshot") or {}
    impacts = payload.get("module_impacts") or {}
    capabilities = health.get("capability_status") or {}
    diagnostics = payload.get("data_freshness_diagnostics") or []
    lines = [
        "# Daily System Health",
        "",
        f"- generated_at: `{payload.get('generated_at')}`",
        f"- batch_date: `{payload.get('batch_date')}`",
        f"- overall_status: `{payload.get('overall_status')}`",
        "",
        "## Blocking Issues",
        "",
    ]
    blocking_rows = [row for row in health.get("items") or [] if row.get("blocking_level") == "block"]
    if not blocking_rows:
        lines.append("- 当前没有 block 级数据问题。")
    for row in blocking_rows:
        metadata = row.get("metadata") or {}
        expected = metadata.get("expected_latest_trading_day")
        actual = metadata.get("actual_latest_trading_day")
        extra = f" / expected={expected} actual={actual}" if expected or actual else ""
        lines.append(
            f"- {row.get('market')} {row.get('data_type')}: {row.get('freshness_status')} / {row.get('staleness_reason')}{extra}"
        )

    lines.extend(["", "## Capability Status", ""])
    if not capabilities:
        lines.append("- 当前没有 capability matrix。")
    for capability, item in capabilities.items():
        reason = "；".join((item.get("reasons") or [])[:2])
        lines.append(f"- {capability}: `{item.get('status')}` / {reason or '-'}")

    lines.extend(["", "## Freshness Diagnostics", ""])
    if not diagnostics:
        lines.append("- 暂无诊断结果。")
    for item in diagnostics[:20]:
        lines.append(
            "- "
            f"{item.get('source_key')}[{item.get('market')}]: `{item.get('probable_cause')}` / "
            f"expected={item.get('expected_latest_trading_day') or '-'} / "
            f"actual={item.get('actual_latest_trading_day') or item.get('last_data_timestamp') or '-'} / "
            f"repair={item.get('recommended_repair_action') or '-'}"
        )

    lines.extend(["", "## Disabled / Planned Sources", ""])
    disabled = source_snapshot.get("disabled_or_planned") or []
    if not disabled:
        lines.append("- 当前没有 planned/disabled 来源。")
    for item in disabled[:30]:
        lines.append(f"- {item.get('source_key')}: {item.get('status')} / {item.get('impact')}")

    lines.extend(["", "## Impact", ""])
    for module_name, gate in impacts.items():
        allowed = ", ".join(gate.get("allowed_actions") or [])
        reasons = "；".join((gate.get("reasons") or [])[:2])
        lines.append(f"- {module_name}: `{gate.get('status')}` / allowed: {allowed or '-'} / {reasons or '-'}")

    generated = payload.get("generated_today") or {}
    ledger = payload.get("decision_ledger_today") or {}
    lines.extend(
        [
            "",
            "## Generated Today",
            "",
            f"- report_status_counts: `{generated}`",
            f"- decision_ledger_status_counts: `{ledger}`",
            "",
            "## Next Required Actions",
            "",
        ]
    )
    for action in payload.get("next_required_actions") or []:
        lines.append(f"- {action}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    # Kept for compatibility with jobs that treat an empty local runtime as a
    # valid development state.
    if "--allow-empty" in sys.argv:
        sys.argv.remove("--allow-empty")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    batch_date = now[:10]
    output_path = OUTPUT_DIR / f"{batch_date}_daily_system_health.md"

    conn = sqlite3.connect(DB_PATH)
    try:
        health = refresh_system_data_health(conn)
        source_snapshot = source_registry_snapshot()
        impacts = build_module_impacts(conn)
        diagnostics = diagnose_data_freshness(conn, refresh=False)
        payload = {
            "generated_at": now,
            "batch_date": batch_date,
            "overall_status": overall_label(health, impacts),
            "data_health_snapshot": health,
            "source_registry_snapshot": source_snapshot,
            "module_impacts": impacts,
            "data_freshness_diagnostics": diagnostics,
            "generated_today": latest_report_status_counts(conn, batch_date),
            "decision_ledger_today": status_counts_today(conn, "decision_ledger", "status", "created_at", batch_date),
        }
        payload["next_required_actions"] = next_actions(health, source_snapshot)
        output_path.write_text(render_markdown(payload), encoding="utf-8")
        registry_entry = register_snapshot(
            conn,
            entity_type="daily_system_health_report",
            entity_id=batch_date,
            status=payload["overall_status"].lower(),
            source=SCRIPT_NAME,
            relationships={"summary_rel_path": relative_to_project(output_path)},
            payload={**payload, "summary_rel_path": relative_to_project(output_path)},
            created_at=now,
        )
        handoff_result = ensure_auto_handoff(
            conn,
            registry_entry,
            note="Daily System Health 已生成，请同步当前状态并优先处理 block/degrade 数据问题。",
            created_by=SCRIPT_NAME,
        )
        record_agent_run(
            conn,
            agent_or_script=SCRIPT_NAME,
            status="success",
            entity_type="daily_system_health_report",
            entity_id=batch_date,
            data_health_snapshot=health,
            source_registry_snapshot=source_snapshot,
            output_status=payload["overall_status"].lower(),
            block_reasons=payload["next_required_actions"],
        )
        conn.commit()
    finally:
        conn.close()

    log_run(
        SCRIPT_NAME,
        "success",
        "daily system health report built",
        {
            "registry_entry_id": registry_entry["id"],
            "summary_rel_path": relative_to_project(output_path),
            "overall_status": payload["overall_status"],
            "handoff_result": handoff_result["reason"],
            "handoff_id": handoff_result["handoff"]["handoff_id"] if handoff_result["handoff"] else None,
        },
    )
    print(f"Daily system health report: {relative_to_project(output_path)}")
    print(f"  overall_status={payload['overall_status']}")


if __name__ == "__main__":
    main()
