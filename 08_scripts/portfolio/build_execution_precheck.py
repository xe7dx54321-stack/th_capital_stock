#!/usr/bin/env python3
"""Build a precheck summary before any portfolio action is treated as executable."""

import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH, get_latest_registry_entry, get_registry_entry_by_id
from smr_paths import env_or_project_path, relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run

OUTPUT_DIR = env_or_project_path("SMR_PORTFOLIO_PRECHECK_DIR", "04_portfolio", "prechecks")


def load_snapshot_entry(conn, entity_type, entity_id=None, required=True):
    if entity_id:
        entry = get_latest_registry_entry(conn, entity_type, entity_id)
        if entry is not None:
            return entry
    row = conn.execute(
        """
        SELECT id
        FROM task_registry_entity_latest
        WHERE entity_type=?
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """,
        (entity_type,),
    ).fetchone()
    if not row:
        if required:
            raise SystemExit(f"{entity_type} not found")
        return None
    entry = get_registry_entry_by_id(conn, row[0])
    if entry is None and required:
        raise SystemExit(f"latest {entity_type} entry missing")
    return entry


def ordered_unique(values):
    seen = set()
    rows = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        rows.append(text)
    return rows


def precheck_status(plan_payload, risk_payload, pnl_payload):
    status_counts = plan_payload.get("status_counts") or {}
    if (risk_payload.get("unacknowledged_alert_count") or 0) > 0:
        return "blocked"
    if (status_counts.get("blocked") or 0) > 0:
        return "blocked"
    if (status_counts.get("watch_only") or 0) > 0:
        return "watch_only"
    if (plan_payload.get("plan_count") or 0) > 0:
        return "ready"
    if (pnl_payload.get("open_position_count") or 0) <= 0:
        return "reference_only"
    return "empty"


def build_global_checks(plan_payload, risk_payload, pnl_payload):
    checks = []
    if (risk_payload.get("unacknowledged_alert_count") or 0) > 0:
        checks.append("当前存在未确认风险预警，任何动作都先不要当成可执行。")
    else:
        checks.append("当前没有未确认风险预警。")

    if (pnl_payload.get("open_position_count") or 0) <= 0:
        checks.append("当前真实 open positions 仍为空，执行计划只能按参照层推演理解。")
    else:
        checks.append(f"当前真实 open positions 约 {pnl_payload.get('open_position_count')} 只。")

    status_counts = plan_payload.get("status_counts") or {}
    blocked = status_counts.get("blocked", 0)
    watch_only = status_counts.get("watch_only", 0)
    ready = status_counts.get("ready", 0)
    if blocked:
        checks.append(f"有 {blocked} 组方案被门禁拦住，先处理阻塞项。")
    if watch_only:
        checks.append(f"有 {watch_only} 组方案仍是观察单，不能直接走正式执行。")
    if ready:
        checks.append(f"有 {ready} 组方案通过当前门禁，可以进入下单前最后复核。")
    return ordered_unique(checks)


def build_plan_digest(plan_payload):
    rows = []
    for plan in (plan_payload.get("plans") or [])[:5]:
        add_item = plan.get("add") or {}
        remove_item = plan.get("remove") or {}
        gate = plan.get("gate_result") or {}
        rows.append(
            {
                "title": f"调入 {add_item.get('name') or add_item.get('ts_code') or '-'} / 调出 {remove_item.get('name') or remove_item.get('ts_code') or '-'}",
                "gate_status": gate.get("status") or "-",
                "trade_amount": plan.get("trade_amount"),
                "first_check": ((plan.get("execution_checklist") or [None])[0]) or "-",
                "first_risk": ((plan.get("risk_flags") or [None])[0]) or "-",
            }
        )
    return rows


def render_markdown(created_at, precheck_date, precheck_status_value, checks, plan_digest, relationships):
    lines = [
        "# SMR 执行前检查",
        "",
        f"- created_at: {created_at}",
        f"- precheck_date: {precheck_date}",
        f"- precheck_status: {precheck_status_value}",
        f"- execution_plan_rel_path: `{relationships.get('execution_plan_rel_path') or '-'}`",
        f"- risk_snapshot_rel_path: `{relationships.get('risk_snapshot_rel_path') or '-'}`",
        f"- pnl_snapshot_source: `{relationships.get('pnl_snapshot_source') or '-'}`",
        "",
        "## 全局闸门",
        "",
    ]
    for item in checks:
        lines.append(f"- {item}")

    lines.extend(["", "## 方案级检查", ""])
    if not plan_digest:
        lines.append("- 当前没有可提炼的执行方案。")
    else:
        for item in plan_digest:
            lines.append(
                f"- {item['title']}｜{item['gate_status']}｜金额 `{item['trade_amount']}`｜"
                f"先检查：{item['first_check']}｜主要风险：{item['first_risk']}"
            )
    return "\n".join(lines) + "\n"


def build_execution_precheck_for_date(conn, entity_id=None, created_at=None):
    created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    execution_entry = load_snapshot_entry(conn, "rotation_execution_plan_snapshot", entity_id, required=True)
    precheck_date = execution_entry.get("entity_id")
    risk_entry = load_snapshot_entry(conn, "risk_monitor_snapshot", precheck_date, required=False)
    pnl_entry = load_snapshot_entry(conn, "portfolio_pnl_snapshot", precheck_date, required=False)

    execution_payload = execution_entry.get("payload", {}) or {}
    risk_payload = (risk_entry or {}).get("payload", {}) or {}
    pnl_payload = (pnl_entry or {}).get("payload", {}) or {}

    relationships = {
        "summary_rel_path": None,
        "execution_plan_rel_path": (execution_entry.get("relationships", {}) or {}).get("summary_rel_path")
        or execution_payload.get("summary_rel_path"),
        "risk_snapshot_rel_path": ((risk_entry or {}).get("relationships", {}) or {}).get("alert_file_rel_path")
        or risk_payload.get("alert_file_rel_path"),
        "pnl_snapshot_source": (pnl_entry or {}).get("source"),
        "execution_plan_entry_id": execution_entry.get("id"),
        "risk_snapshot_entry_id": (risk_entry or {}).get("id"),
        "pnl_snapshot_entry_id": (pnl_entry or {}).get("id"),
    }

    checks = build_global_checks(execution_payload, risk_payload, pnl_payload)
    plan_digest = build_plan_digest(execution_payload)
    status_value = precheck_status(execution_payload, risk_payload, pnl_payload)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{precheck_date}_execution_precheck.md"
    relationships["summary_rel_path"] = relative_to_project(output_path)
    output_path.write_text(
        render_markdown(created_at, precheck_date, status_value, checks, plan_digest, relationships),
        encoding="utf-8",
    )

    payload = {
        "precheck_status": status_value,
        "global_checks": checks,
        "plan_digest": plan_digest,
        "execution_plan_rel_path": relationships["execution_plan_rel_path"],
        "summary_rel_path": relationships["summary_rel_path"],
        "risk_unacknowledged_alert_count": risk_payload.get("unacknowledged_alert_count", 0),
        "pnl_open_position_count": pnl_payload.get("open_position_count", 0),
    }
    register_snapshot(
        conn,
        entity_type="execution_precheck_snapshot",
        entity_id=precheck_date,
        status=status_value,
        source="build_execution_precheck.py",
        relationships=relationships,
        payload=payload,
        created_at=created_at,
    )
    return {
        "entity_id": precheck_date,
        "precheck_status": status_value,
        "output_path": output_path,
        "relationships": relationships,
    }


def main():
    parser = argparse.ArgumentParser(description="Build execution precheck snapshot")
    parser.add_argument("--date", help="Prefer this entity_id date")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    result = build_execution_precheck_for_date(conn, args.date)
    conn.commit()
    conn.close()

    log_run(
        "build_execution_precheck.py",
        "success",
        "execution precheck built",
        {
            "entity_id": result["entity_id"],
            "precheck_status": result["precheck_status"],
            "summary_rel_path": relative_to_project(result["output_path"]),
        },
    )
    print(f"Execution precheck built: {result['entity_id']}")
    print(f"Summary file: {result['output_path']}")
    print(f"Precheck status: {result['precheck_status']}")


if __name__ == "__main__":
    main()
