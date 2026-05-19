#!/usr/bin/env python3
"""Build deterministic attack-defense notes for opportunity candidates."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_paths import env_or_project_path, project_path, relative_to_project
from smr_agents import ensure_auto_handoff
from smr_registry import register_snapshot
from smr_runlog import log_run

DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")
OUTPUT_DIR = env_or_project_path("SMR_OPPORTUNITY_ATTACK_DEFENSE_DIR", "02_research", "opportunity_attack_defense")
POLICY_PATH = project_path("00_control", "opportunity_engine_policy.json")
SCRIPT_NAME = "build_thesis_attack_defense_snapshot.py"


def safe_float(value, default=None):
    if value in (None, "", "None", "nan", "-", "--"):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def render_pct(value):
    number = safe_float(value)
    if number is None:
        return "-"
    return f"{number:.2%}"


def latest_registry_snapshot(conn, entity_type, entity_id=None):
    filters = ["entity_type=?"]
    params = [entity_type]
    if entity_id:
        filters.append("entity_id=?")
        params.append(entity_id)
    row = conn.execute(
        f"""
        SELECT id, entity_type, entity_id, status, source, relationships_json, payload_json, created_at
        FROM task_registry_entity_latest
        WHERE {' AND '.join(filters)}
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """,
        params,
    ).fetchone()
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


def flatten_radar_candidates(radar_snapshot, limit):
    payload = (radar_snapshot or {}).get("payload") or {}
    rows = []
    for market_items in (payload.get("markets") or {}).values():
        rows.extend(market_items or [])
    if not rows:
        rows = payload.get("top_candidates") or []
    rows.sort(key=lambda item: (-(safe_float(item.get("opportunity_score"), 0.0) or 0.0), item.get("ts_code") or ""))
    return rows[:limit]


def evidence_by_symbol(evidence_snapshot):
    payload = (evidence_snapshot or {}).get("payload") or {}
    return {item.get("ts_code"): item for item in payload.get("items") or [] if item.get("ts_code")}


def guard_thresholds():
    if not POLICY_PATH.exists():
        return {}
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    return policy.get("risk_guards") or {}


def defense_points(candidate, evidence):
    metrics = candidate.get("metrics") or {}
    factors = candidate.get("factors") or {}
    best = (evidence or {}).get("best_evidence") or {}
    points = []
    if candidate.get("opportunity_score") is not None:
        points.append(f"综合机会分 {candidate['opportunity_score']:.2f}，已进入主动雷达前列。")
    if metrics.get("breakout_20d"):
        points.append("价格突破近20日高点，趋势开始从观察变成可验证信号。")
    if metrics.get("volume_ratio_20d"):
        points.append(f"量能为近20日均值 {metrics['volume_ratio_20d']:.2f} 倍，异动具备资金参与痕迹。")
    if factors.get("trend_strength") is not None:
        points.append(f"趋势强度 {factors['trend_strength']}，可与已有研究观点交叉验证。")
    if best.get("evidence_label") == "ready_for_paper_watch":
        points.append(
            f"轻量回测最优策略 {best.get('strategy_id')} 达到纸面观察门槛，"
            f"胜率 {render_pct(best.get('win_rate'))}，平均收益 {render_pct(best.get('avg_return'))}。"
        )
    if candidate.get("latest_event_title"):
        points.append(f"最新事件锚点：{candidate.get('latest_event_title')}。")
    return points[:5] or ["当前支持项主要来自合成信号，仍需补强一手材料和历史证据。"]


def attack_points(candidate, evidence, guards):
    metrics = candidate.get("metrics") or {}
    factors = candidate.get("factors") or {}
    best = (evidence or {}).get("best_evidence") or {}
    points = []
    rsi = safe_float(factors.get("rsi_14"))
    overheat_rsi = safe_float(guards.get("overheat_rsi"), 78) or 78
    chase_pct = safe_float(guards.get("single_day_chase_pct"), 9.5) or 9.5
    latest_pct = safe_float(metrics.get("latest_pct_chg"), 0.0) or 0.0
    if rsi is not None and rsi >= overheat_rsi:
        points.append(f"RSI {rsi:.1f} 已偏热，价格异动可能已经透支短线买盘。")
    if latest_pct >= chase_pct:
        points.append(f"单日涨幅 {latest_pct:+.2f}% 过大，不能把突破直接当作低风险买点。")
    if best.get("evidence_label") in {"thin_sample", "negative_evidence"}:
        points.append(f"历史证据标签为 {best.get('evidence_label')}，样本或收益质量不足。")
    if not candidate.get("latest_event_title"):
        points.append("缺少新事件锚点，可能只是技术性波动或小样本资金行为。")
    if not candidate.get("research_decision"):
        points.append("没有结构化研究决策支撑，不能直接升级为高确定性 thesis。")
    if not points:
        points.append("主要攻击点是信号延续性：若次日量能回落且价格跌回突破位，机会等级应下调。")
    return points[:5]


def kill_triggers(candidate, evidence):
    metrics = candidate.get("metrics") or {}
    best = (evidence or {}).get("best_evidence") or {}
    triggers = [
        "次日或未来两日量能回落到20日均量附近，同时价格跌回20日突破位或20日均线下方。",
        "后续公告/研报/电话会无法解释本轮异动，且事件层没有新证据补强。",
    ]
    if metrics.get("latest_close") and metrics.get("drawdown_60d_high_pct") is not None:
        triggers.append("若跌破本轮异动启动价并重新接近60日高点回撤区间，撤回纸面观察。")
    if best.get("evidence_label") == "negative_evidence":
        triggers.append("策略证据继续为负时，不再进入纸面组合，只保留普通监控。")
    return triggers[:4]


def verdict(candidate, evidence):
    score = safe_float(candidate.get("opportunity_score"), 0.0) or 0.0
    best = (evidence or {}).get("best_evidence") or {}
    label = best.get("evidence_label")
    if score >= 14 and label == "ready_for_paper_watch":
        return {
            "verdict": "paper_watch_ready",
            "summary": "信号、研究池和历史证据可以支持进入纸面观察，但仍不触发真实交易。",
        }
    if score >= 11 and label in {"ready_for_paper_watch", "mixed_evidence"}:
        return {
            "verdict": "watch_with_evidence",
            "summary": "可以进入重点观察，等待事件证据或二次确认后再升级。",
        }
    if label in {"thin_sample", "negative_evidence"}:
        return {
            "verdict": "research_first",
            "summary": "先补研究和数据证据，不进入纸面组合。",
        }
    return {
        "verdict": "monitor_only",
        "summary": "保留在主动雷达中继续观察，暂不升级。",
    }


def build_case(candidate, evidence, guards):
    case_verdict = verdict(candidate, evidence)
    return {
        "ts_code": candidate.get("ts_code"),
        "name": candidate.get("name") or candidate.get("ts_code"),
        "market": candidate.get("market"),
        "sector": candidate.get("sector"),
        "opportunity_score": candidate.get("opportunity_score"),
        "radar_bucket": candidate.get("radar_bucket"),
        "signal_tags": candidate.get("signal_tags") or [],
        "evidence_label": ((evidence or {}).get("best_evidence") or {}).get("evidence_label"),
        "best_strategy": ((evidence or {}).get("best_evidence") or {}).get("strategy_id"),
        "verdict": case_verdict["verdict"],
        "verdict_summary": case_verdict["summary"],
        "defense_points": defense_points(candidate, evidence),
        "attack_points": attack_points(candidate, evidence, guards),
        "kill_triggers": kill_triggers(candidate, evidence),
        "next_checks": candidate.get("next_checks") or [],
    }


def overview_lines(cases):
    ready = [item for item in cases if item.get("verdict") == "paper_watch_ready"]
    watch = [item for item in cases if item.get("verdict") == "watch_with_evidence"]
    research_first = [item for item in cases if item.get("verdict") == "research_first"]
    lines = [
        f"本轮攻防覆盖 {len(cases)} 个主动雷达候选，纸面观察就绪 {len(ready)} 个，带证据观察 {len(watch)} 个。",
        f"需要先补研究/数据的候选 {len(research_first)} 个；这些不应进入组合动作。",
    ]
    if ready:
        names = ", ".join(f"{item['name']}({item['ts_code']})" for item in ready[:3])
        lines.append(f"优先纸面观察：{names}。")
    return lines


def write_markdown(path, payload):
    lines = [
        "# 机会攻防推演快照",
        "",
        f"- generated_at: {payload.get('generated_at')}",
        f"- batch_date: {payload.get('batch_date')}",
        f"- source_radar_entry_id: {payload.get('source_radar_entry_id')}",
        f"- source_evidence_entry_id: {payload.get('source_evidence_entry_id')}",
        "- mode: paper_only / attack-defense review.",
        "",
        "## 核心结论",
        "",
    ]
    for line in payload.get("overview_lines") or []:
        lines.append(f"- {line}")
    for item in payload.get("cases") or []:
        lines.extend(
            [
                "",
                f"## {item.get('name')} / {item.get('ts_code')}",
                "",
                f"- verdict: {item.get('verdict')}",
                f"- summary: {item.get('verdict_summary')}",
                f"- opportunity_score: {item.get('opportunity_score')}",
                f"- evidence_label: {item.get('evidence_label') or '-'}",
                f"- best_strategy: {item.get('best_strategy') or '-'}",
                "",
                "### Defense",
                "",
            ]
        )
        lines.extend(f"- {point}" for point in item.get("defense_points") or [])
        lines.extend(["", "### Attack", ""])
        lines.extend(f"- {point}" for point in item.get("attack_points") or [])
        lines.extend(["", "### Kill Triggers", ""])
        lines.extend(f"- {point}" for point in item.get("kill_triggers") or [])
        lines.extend(["", "### Next Checks", ""])
        lines.extend(f"- {point}" for point in item.get("next_checks") or [])
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Build opportunity attack-defense snapshot")
    parser.add_argument("--date", help="Snapshot date; defaults to latest radar/evidence")
    parser.add_argument("--limit", type=int, default=12)
    args = parser.parse_args()

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    batch_date = generated_at[:10]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{batch_date}_thesis_attack_defense_snapshot.md"

    conn = sqlite3.connect(DB_PATH)
    try:
        radar_snapshot = latest_registry_snapshot(conn, "opportunity_radar_snapshot", args.date)
        evidence_snapshot = latest_registry_snapshot(conn, "strategy_evidence_snapshot", args.date)
        if not radar_snapshot:
            raise SystemExit("No opportunity_radar_snapshot found.")
        if not evidence_snapshot:
            raise SystemExit("No strategy_evidence_snapshot found.")
        evidence_map = evidence_by_symbol(evidence_snapshot)
        guards = guard_thresholds()
        candidates = flatten_radar_candidates(radar_snapshot, args.limit)
        cases = [
            build_case(candidate, evidence_map.get(candidate.get("ts_code")), guards)
            for candidate in candidates
        ]
        payload = {
            "generated_at": generated_at,
            "batch_date": batch_date,
            "source_radar_entry_id": radar_snapshot["id"],
            "source_radar_entity_id": radar_snapshot["entity_id"],
            "source_evidence_entry_id": evidence_snapshot["id"],
            "source_evidence_entity_id": evidence_snapshot["entity_id"],
            "case_count": len(cases),
            "paper_watch_ready_count": sum(1 for item in cases if item.get("verdict") == "paper_watch_ready"),
            "watch_with_evidence_count": sum(1 for item in cases if item.get("verdict") == "watch_with_evidence"),
            "research_first_count": sum(1 for item in cases if item.get("verdict") == "research_first"),
            "cases": cases,
            "policy_rel_path": relative_to_project(POLICY_PATH),
        }
        payload["overview_lines"] = overview_lines(cases)
        write_markdown(output_path, payload)
        registry_entry = register_snapshot(
            conn,
            entity_type="thesis_attack_defense_snapshot",
            entity_id=batch_date,
            status="generated" if cases else "empty",
            source=SCRIPT_NAME,
            relationships={
                "summary_rel_path": relative_to_project(output_path),
                "source_radar_entry_id": radar_snapshot["id"],
                "source_evidence_entry_id": evidence_snapshot["id"],
            },
            payload={**payload, "summary_rel_path": relative_to_project(output_path)},
            created_at=generated_at,
        )
        handoff_result = ensure_auto_handoff(
            conn,
            registry_entry,
            note="机会攻防推演已生成，自动转交研究代理沉淀 defense/attack/kill trigger。",
            created_by=SCRIPT_NAME,
        )
        conn.commit()
    finally:
        conn.close()

    log_run(
        SCRIPT_NAME,
        "success",
        "thesis attack-defense snapshot built",
        {
            "registry_entry_id": registry_entry["id"],
            "summary_rel_path": relative_to_project(output_path),
            "case_count": payload["case_count"],
            "paper_watch_ready_count": payload["paper_watch_ready_count"],
            "handoff_result": handoff_result["reason"],
            "handoff_id": handoff_result["handoff"]["handoff_id"] if handoff_result["handoff"] else None,
        },
    )
    print(f"Thesis attack-defense snapshot: {relative_to_project(output_path)}")
    print(f"  case_count={payload['case_count']}")
    print(f"  paper_watch_ready_count={payload['paper_watch_ready_count']}")


if __name__ == "__main__":
    main()
