#!/usr/bin/env python3
"""Build the current SMR operating state surface."""

from __future__ import annotations

import json
import re
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import ensure_auto_handoff
from smr_paths import env_or_project_path, project_path, relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run

DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")
OUTPUT_DIR = env_or_project_path("SMR_CURRENT_STATE_DIR", "06_reports", "adhoc", "current_state")
CURRENT_STATE_PATH = project_path("00_control", "current_state.md")
DISPATCH_BOARD_PATH = project_path("00_control", "dispatch_board.md")
SCRIPT_NAME = "build_current_state_snapshot.py"


def safe_float(value, default=None):
    if value in (None, "", "None", "nan", "-", "--"):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def compact_text(value, limit=92):
    text = str(value or "").strip().replace("\n", " ")
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "..."


def relation_exists(conn, name):
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name=?",
        (name,),
    ).fetchone()
    return bool(row)


def registry_row_to_entry(row):
    if not row:
        return None
    return {
        "id": row[0],
        "entity_type": row[1],
        "entity_id": row[2],
        "status": row[3],
        "source": row[4],
        "relationships": json.loads(row[5] or "{}"),
        "payload": json.loads(row[6] or "{}"),
        "created_at": row[7],
    }


def latest_registry_snapshot(conn, entity_type):
    if not relation_exists(conn, "task_registry_entity_latest"):
        return None
    row = conn.execute(
        """
        SELECT id, entity_type, entity_id, status, source, relationships_json, payload_json, created_at
        FROM task_registry_entity_latest
        WHERE entity_type=?
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """,
        (entity_type,),
    ).fetchone()
    return registry_row_to_entry(row)


def parse_update_time(path):
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    match = re.search(r"\*\*更新日期\*\*：([^\n]+)", text)
    return match.group(1).strip() if match else ""


def load_dispatch_board_state():
    update_time = parse_update_time(DISPATCH_BOARD_PATH)
    stale_note = ""
    if update_time and not update_time.startswith(datetime.now().strftime("%Y-%m-%d")):
        stale_note = "dispatch_board 正文不是今日口径，应以 current_state 和最新 patch candidate 为准。"
    return {
        "path": relative_to_project(DISPATCH_BOARD_PATH),
        "update_time": update_time,
        "stale_note": stale_note,
    }


def top_opportunities(radar_snapshot, limit=8):
    payload = (radar_snapshot or {}).get("payload") or {}
    rows = payload.get("top_candidates") or []
    if not rows:
        for market_items in (payload.get("markets") or {}).values():
            rows.extend(market_items or [])
    rows = list({item.get("ts_code"): item for item in rows if item.get("ts_code")}.values())
    rows.sort(key=lambda item: safe_float(item.get("opportunity_score"), 0.0) or 0.0, reverse=True)
    return rows[:limit]


def paper_items(watch_snapshot, performance_snapshot):
    tickets = ((watch_snapshot or {}).get("payload") or {}).get("tickets") or []
    performance = {
        item.get("ticket_id"): item
        for item in (((performance_snapshot or {}).get("payload") or {}).get("items") or [])
        if item.get("ticket_id")
    }
    rows = []
    for ticket in tickets:
        perf = performance.get(ticket.get("ticket_id")) or {}
        levels = ticket.get("reference_levels") or {}
        rows.append(
            {
                "ticket_id": ticket.get("ticket_id"),
                "ts_code": ticket.get("ts_code"),
                "name": ticket.get("name") or ticket.get("ts_code"),
                "verdict": ticket.get("verdict"),
                "opportunity_score": ticket.get("opportunity_score"),
                "observe_above": levels.get("observe_above"),
                "invalidate_below": levels.get("invalidate_below"),
                "performance_status": perf.get("status") or "awaiting_market_data",
                "latest_return": perf.get("latest_return"),
                "action": perf.get("action") or ticket.get("paper_trigger"),
            }
        )
    return rows


def evidence_gap_items(snapshot, limit=8):
    rows = ((snapshot or {}).get("payload") or {}).get("items") or []
    gaps = [
        row
        for row in rows
        if row.get("evidence_state") in {"price_only", "stale_evidence", "overheated_without_fresh_evidence"}
    ]
    gaps.sort(key=lambda item: safe_float(item.get("opportunity_score"), 0.0) or 0.0, reverse=True)
    return gaps[:limit]


def freshness_problem_items(snapshot):
    rows = ((snapshot or {}).get("payload") or {}).get("items") or []
    rank = {"stale": 3, "missing": 3, "warn": 2, "fresh": 1}
    problems = [row for row in rows if row.get("status") in {"missing", "warn", "stale"}]
    problems.sort(key=lambda row: -rank.get(row.get("status"), 0))
    return problems


def p0_actions(payload):
    actions = []
    freshness = payload.get("freshness_problems") or []
    evidence_gaps = payload.get("evidence_gaps") or []
    paper = payload.get("paper_watch") or []
    dispatch = payload.get("dispatch_board") or {}
    trigger_count = sum(1 for item in paper if item.get("performance_status") == "trigger_confirmed")
    invalidated_count = sum(1 for item in paper if item.get("performance_status") == "invalidated")

    if freshness:
        actions.append(f"先处理新鲜度异常：{freshness[0]['component']} 当前为 {freshness[0]['status']}。")
    if trigger_count:
        actions.append(f"{trigger_count} 张纸面观察单已触发，需要研究/风控复核是否升级。")
    if invalidated_count:
        actions.append(f"{invalidated_count} 张纸面观察单失效，需要记录降级原因并校准信号。")
    if evidence_gaps:
        actions.append(f"高分机会仍有 {len(evidence_gaps)} 个证据缺口，优先补公开来源再判断。")
    if dispatch.get("stale_note"):
        actions.append("正式 dispatch_board 口径滞后，今日以 current_state 为主，并择机合并最新 patch candidate。")
    if not actions:
        actions.append("当前闭环无 P0 阻塞，继续按纸面观察和证据补强节奏推进。")
    return actions[:6]


def overall_status(payload):
    if any(item.get("status") in {"missing", "stale"} for item in payload.get("freshness_problems") or []):
        return "data_first"
    if payload.get("evidence_gaps"):
        return "evidence_first"
    if any(item.get("performance_status") == "trigger_confirmed" for item in payload.get("paper_watch") or []):
        return "review_triggers"
    return "normal_watch"


def render_pct(value):
    number = safe_float(value)
    if number is None:
        return "-"
    return f"{number:+.2%}"


def write_markdown(path, payload):
    lines = [
        "# SMR 当前作战状态",
        "",
        f"- generated_at: {payload['generated_at']}",
        f"- batch_date: {payload['batch_date']}",
        f"- operating_status: `{payload['operating_status']}`",
        f"- source_archive_rel_path: `{payload.get('summary_rel_path') or ''}`",
        "- boundary: paper_only；本页不包含真实交易指令。",
        "",
        "## 今日 P0",
        "",
    ]
    lines.extend(f"- {item}" for item in payload.get("p0_actions") or [])
    lines.extend(
        [
            "",
            "## 机会雷达",
            "",
            "| 标的 | 分数 | 桶 | 标签 | 下一步 |",
            "| --- | ---: | --- | --- | --- |",
        ]
    )
    for item in payload.get("top_opportunities") or []:
        lines.append(
            "| {subject} | {score} | {bucket} | {tags} | {next_check} |".format(
                subject=f"{item.get('name')} / {item.get('ts_code')}",
                score=f"{safe_float(item.get('opportunity_score'), 0.0):.2f}",
                bucket=item.get("radar_bucket") or "-",
                tags=", ".join(item.get("signal_tags") or []) or "-",
                next_check=compact_text((item.get("next_checks") or ["-"])[0], 58),
            )
        )
    lines.extend(
        [
            "",
            "## 纸面观察",
            "",
            "| 标的 | 状态 | 分数 | 观察上沿 | 失效下沿 | 最新收益 | 下一步 |",
            "| --- | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for item in payload.get("paper_watch") or []:
        lines.append(
            "| {subject} | {status} | {score} | {above} | {below} | {ret} | {action} |".format(
                subject=f"{item.get('name')} / {item.get('ts_code')}",
                status=item.get("performance_status") or item.get("verdict") or "-",
                score=f"{safe_float(item.get('opportunity_score'), 0.0):.2f}",
                above=item.get("observe_above") or "-",
                below=item.get("invalidate_below") or "-",
                ret=render_pct(item.get("latest_return")),
                action=compact_text(item.get("action"), 58),
            )
        )
    lines.extend(
        [
            "",
            "## 证据缺口",
            "",
            "| 标的 | 证据状态 | 最近来源 | 下一步 |",
            "| --- | --- | --- | --- |",
        ]
    )
    for item in payload.get("evidence_gaps") or []:
        lines.append(
            "| {subject} | {state} | {source} | {action} |".format(
                subject=f"{item.get('name')} / {item.get('ts_code')}",
                state=item.get("evidence_state") or "-",
                source=item.get("latest_source_updated_at") or "-",
                action=compact_text(item.get("recommended_action"), 64),
            )
        )
    if not payload.get("evidence_gaps"):
        lines.append("| - | - | - | 当前无高优先级证据缺口。 |")
    lines.extend(
        [
            "",
            "## 新鲜度",
            "",
            "| 组件 | 状态 | 最新时间 | 下一步 |",
            "| --- | --- | --- | --- |",
        ]
    )
    for item in payload.get("freshness_problems") or []:
        lines.append(
            "| {component} | {status} | {latest} | {action} |".format(
                component=item.get("component"),
                status=item.get("status"),
                latest=item.get("latest") or "-",
                action=compact_text(item.get("next_action"), 64),
            )
        )
    if not payload.get("freshness_problems"):
        lines.append("| - | fresh | - | 关键数据和产物均在可用窗口内。 |")
    lines.extend(
        [
            "",
            "## 状态来源",
            "",
            f"- dispatch_board_update_time: `{(payload.get('dispatch_board') or {}).get('update_time') or ''}`",
            f"- dispatch_board_note: {(payload.get('dispatch_board') or {}).get('stale_note') or 'dispatch_board 当前无明显滞后提示。'}",
            f"- radar_entry_id: `{payload.get('source_entry_ids', {}).get('opportunity_radar_snapshot') or ''}`",
            f"- paper_watch_entry_id: `{payload.get('source_entry_ids', {}).get('paper_trade_watchlist_snapshot') or ''}`",
            f"- evidence_gap_entry_id: `{payload.get('source_entry_ids', {}).get('opportunity_evidence_gap_snapshot') or ''}`",
            f"- data_freshness_entry_id: `{payload.get('source_entry_ids', {}).get('data_freshness_snapshot') or ''}`",
            "",
        ]
    )
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main():
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    batch_date = generated_at[:10]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = OUTPUT_DIR / f"{batch_date}_current_state_snapshot.md"

    conn = sqlite3.connect(DB_PATH)
    try:
        snapshots = {
            entity_type: latest_registry_snapshot(conn, entity_type)
            for entity_type in (
                "opportunity_radar_snapshot",
                "paper_trade_watchlist_snapshot",
                "paper_watch_performance_snapshot",
                "opportunity_evidence_gap_snapshot",
                "data_freshness_snapshot",
            )
        }
        payload = {
            "generated_at": generated_at,
            "batch_date": batch_date,
            "dispatch_board": load_dispatch_board_state(),
            "top_opportunities": top_opportunities(snapshots["opportunity_radar_snapshot"]),
            "paper_watch": paper_items(
                snapshots["paper_trade_watchlist_snapshot"],
                snapshots["paper_watch_performance_snapshot"],
            ),
            "evidence_gaps": evidence_gap_items(snapshots["opportunity_evidence_gap_snapshot"]),
            "freshness_problems": freshness_problem_items(snapshots["data_freshness_snapshot"]),
            "source_entry_ids": {
                key: (snapshot or {}).get("id")
                for key, snapshot in snapshots.items()
            },
        }
        payload["p0_actions"] = p0_actions(payload)
        payload["operating_status"] = overall_status(payload)
        payload["status_counts"] = {
            "paper_watch": dict(Counter(item.get("performance_status") for item in payload["paper_watch"])),
            "evidence": dict(Counter(item.get("evidence_state") for item in ((snapshots["opportunity_evidence_gap_snapshot"] or {}).get("payload") or {}).get("items") or [])),
            "freshness": dict(Counter(item.get("status") for item in ((snapshots["data_freshness_snapshot"] or {}).get("payload") or {}).get("items") or [])),
        }
        payload["summary_rel_path"] = relative_to_project(archive_path)
        payload["current_state_rel_path"] = relative_to_project(CURRENT_STATE_PATH)
        write_markdown(archive_path, payload)
        write_markdown(CURRENT_STATE_PATH, payload)
        registry_entry = register_snapshot(
            conn,
            entity_type="current_state_snapshot",
            entity_id=batch_date,
            status=payload["operating_status"],
            source=SCRIPT_NAME,
            relationships={
                "summary_rel_path": relative_to_project(archive_path),
                "current_state_rel_path": relative_to_project(CURRENT_STATE_PATH),
                **{f"source_{key}_entry_id": value for key, value in payload["source_entry_ids"].items() if value},
            },
            payload=payload,
            created_at=generated_at,
        )
        handoff_result = ensure_auto_handoff(
            conn,
            registry_entry,
            note="当前作战状态面板已生成，请研究/报告代理同步 P0 动作和关键阻塞。",
            created_by=SCRIPT_NAME,
        )
        conn.commit()
    finally:
        conn.close()

    log_run(
        SCRIPT_NAME,
        "success",
        "current state snapshot built",
        {
            "registry_entry_id": registry_entry["id"],
            "summary_rel_path": relative_to_project(archive_path),
            "current_state_rel_path": relative_to_project(CURRENT_STATE_PATH),
            "operating_status": payload["operating_status"],
            "p0_count": len(payload["p0_actions"]),
            "handoff_result": handoff_result["reason"],
            "handoff_id": handoff_result["handoff"]["handoff_id"] if handoff_result["handoff"] else None,
        },
    )
    print(f"Current state: {relative_to_project(CURRENT_STATE_PATH)}")
    print(f"  archive={relative_to_project(archive_path)}")
    print(f"  operating_status={payload['operating_status']}")


if __name__ == "__main__":
    main()
