#!/usr/bin/env python3
"""Build a paper-only watchlist from opportunity attack-defense results."""

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
from smr_data_health import check_freshness_gate, gate_to_dict
from smr_decision import record_agent_run
from smr_registry import register_snapshot
from smr_runlog import log_run

DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")
OUTPUT_DIR = env_or_project_path("SMR_PAPER_WATCHLIST_DIR", "04_portfolio", "paper")
POLICY_PATH = project_path("00_control", "opportunity_engine_policy.json")
SCRIPT_NAME = "build_paper_trade_watchlist.py"


def load_policy() -> dict:
    if not POLICY_PATH.exists():
        return {}
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def safe_float(value, default=None):
    if value in (None, "", "None", "nan", "-", "--"):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


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


def radar_map(radar_snapshot):
    payload = (radar_snapshot or {}).get("payload") or {}
    rows = []
    for market_items in (payload.get("markets") or {}).values():
        rows.extend(market_items or [])
    rows.extend(payload.get("top_candidates") or [])
    result = {}
    for item in rows:
        ts_code = item.get("ts_code")
        if ts_code and ts_code not in result:
            result[ts_code] = item
    return result


def ticket_rank(case):
    verdict_rank = {
        "paper_watch_ready": 3,
        "watch_with_evidence": 2,
        "research_first": 1,
        "monitor_only": 0,
    }.get(case.get("verdict"), 0)
    return (
        verdict_rank,
        safe_float(case.get("opportunity_score"), 0.0) or 0.0,
        case.get("ts_code") or "",
    )


def reference_levels(case, radar_item):
    metrics = (radar_item or {}).get("metrics") or {}
    latest_close = safe_float(metrics.get("latest_close"))
    if latest_close is None:
        return {
            "paper_reference_price": None,
            "observe_above": None,
            "invalidate_below": None,
            "review_band_note": "缺少最新价格，不能生成纸面观察价格带。",
        }
    observe_above = latest_close * 1.015
    invalidate_below = latest_close * 0.94
    if "breakout_with_volume" in (case.get("signal_tags") or []):
        invalidate_below = latest_close * 0.955
    if case.get("verdict") == "watch_with_evidence":
        observe_above = latest_close * 1.025
    return {
        "paper_reference_price": round(latest_close, 4),
        "observe_above": round(observe_above, 4),
        "invalidate_below": round(invalidate_below, 4),
        "review_band_note": "只作为纸面观察带，不代表真实委托价、止损价或交易指令。",
    }


def build_ticket(case, radar_item):
    levels = reference_levels(case, radar_item)
    metrics = (radar_item or {}).get("metrics") or {}
    return {
        "ticket_id": f"paper__{case.get('ts_code')}__{datetime.now().strftime('%Y%m%d')}",
        "ts_code": case.get("ts_code"),
        "name": case.get("name") or case.get("ts_code"),
        "market": case.get("market"),
        "sector": case.get("sector"),
        "verdict": case.get("verdict"),
        "opportunity_score": case.get("opportunity_score"),
        "evidence_label": case.get("evidence_label"),
        "best_strategy": case.get("best_strategy"),
        "signal_tags": case.get("signal_tags") or [],
        "latest_pct_chg": metrics.get("latest_pct_chg"),
        "volume_ratio_20d": metrics.get("volume_ratio_20d"),
        "reference_trade_date": metrics.get("latest_trade_date"),
        "paper_status": "paper_watch_active",
        "paper_only": True,
        "execution_disabled": True,
        "reference_levels": levels,
        "paper_trigger": (
            "继续观察，不真实交易；若下一交易日仍在 observe_above 上方且量能不塌，再交给研究/风险代理复核。"
        ),
        "paper_invalidation": "触发任一 kill trigger 或跌破 invalidate_below 时，从纸面观察单移出。",
        "defense_points": case.get("defense_points") or [],
        "attack_points": case.get("attack_points") or [],
        "kill_triggers": case.get("kill_triggers") or [],
        "next_checks": case.get("next_checks") or [],
    }


def overview_lines(tickets, cases):
    ready = [ticket for ticket in tickets if ticket.get("verdict") == "paper_watch_ready"]
    watch = [ticket for ticket in tickets if ticket.get("verdict") == "watch_with_evidence"]
    lines = [
        f"本轮从 {len(cases)} 个攻防案例中生成 {len(tickets)} 张纸面观察单。",
        f"其中 paper_watch_ready {len(ready)} 张，watch_with_evidence {len(watch)} 张。",
        "所有 ticket 均为 paper_only，不包含真实交易指令、委托价格或券商接口调用。",
    ]
    if tickets:
        names = ", ".join(f"{ticket['name']}({ticket['ts_code']})" for ticket in tickets[:4])
        lines.append(f"优先跟踪：{names}。")
    return lines


def write_markdown(path, payload):
    lines = [
        "# 纸面机会观察单",
        "",
        f"- generated_at: {payload.get('generated_at')}",
        f"- batch_date: {payload.get('batch_date')}",
        "- mode: paper_only",
        "- live_trading_enabled: false",
        "- hard_boundary: 这里没有真实下单，也没有 broker 指令。",
        "",
        "## 核心结论",
        "",
    ]
    for line in payload.get("overview_lines") or []:
        lines.append(f"- {line}")
    lines.extend(
        [
            "",
            "## Paper Tickets",
            "",
            "| 标的 | 状态 | 分数 | 观察上沿 | 失效下沿 | 证据 | 下一步 |",
            "| --- | --- | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for ticket in payload.get("tickets") or []:
        levels = ticket.get("reference_levels") or {}
        next_check = (ticket.get("next_checks") or ["-"])[0]
        lines.append(
            "| {subject} | {status} | {score} | {above} | {below} | {evidence} | {next_check} |".format(
                subject=f"{ticket.get('name')} / {ticket.get('ts_code')}",
                status=ticket.get("verdict") or "-",
                score=f"{safe_float(ticket.get('opportunity_score'), 0.0):.2f}",
                above=levels.get("observe_above") or "-",
                below=levels.get("invalidate_below") or "-",
                evidence=ticket.get("evidence_label") or "-",
                next_check=next_check,
            )
        )
    for ticket in payload.get("tickets") or []:
        lines.extend(
            [
                "",
                f"## {ticket.get('name')} / {ticket.get('ts_code')}",
                "",
                f"- ticket_id: {ticket.get('ticket_id')}",
                f"- paper_trigger: {ticket.get('paper_trigger')}",
                f"- paper_invalidation: {ticket.get('paper_invalidation')}",
                f"- review_band_note: {(ticket.get('reference_levels') or {}).get('review_band_note')}",
                "",
                "### Kill Triggers",
                "",
            ]
        )
        lines.extend(f"- {item}" for item in ticket.get("kill_triggers") or [])
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Build paper-only opportunity watchlist")
    parser.add_argument("--date", help="Snapshot date; defaults to latest")
    parser.add_argument("--limit", type=int, help="Max paper tickets")
    args = parser.parse_args()

    policy = load_policy()
    limit = args.limit or int((policy.get("candidate_thresholds") or {}).get("max_paper_watch_tickets") or 8)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    batch_date = generated_at[:10]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{batch_date}_paper_trade_watchlist.md"

    conn = sqlite3.connect(DB_PATH)
    try:
        gate = check_freshness_gate(
            conn,
            module_name="paper_watch",
            required_data_types=["daily_bar"],
            allow_degraded=False,
        )
        if gate.status == "block":
            payload = {
                "generated_at": generated_at,
                "batch_date": batch_date,
                "mode": "paper_only",
                "live_trading_enabled": False,
                "blocked_by_data": True,
                "ticket_count": 0,
                "tickets": [],
                "policy_rel_path": relative_to_project(POLICY_PATH),
                "freshness_gate_result": gate_to_dict(gate),
                "data_health_snapshot": gate.data_health_snapshot,
                "overview_lines": [
                    "Freshness Gate 已阻断纸面观察单生成：行情数据过期时不能生成观察价格带、观察上沿或失效下沿。",
                    *gate.reasons[:4],
                ],
            }
            write_markdown(output_path, payload)
            registry_entry = register_snapshot(
                conn,
                entity_type="paper_trade_watchlist_snapshot",
                entity_id=batch_date,
                status="blocked_by_data",
                source=SCRIPT_NAME,
                relationships={"summary_rel_path": relative_to_project(output_path)},
                payload={**payload, "summary_rel_path": relative_to_project(output_path)},
                created_at=generated_at,
            )
            record_agent_run(
                conn,
                agent_or_script=SCRIPT_NAME,
                status="blocked",
                entity_type="paper_trade_watchlist_snapshot",
                entity_id=batch_date,
                data_health_snapshot=gate.data_health_snapshot,
                freshness_gate_result=gate_to_dict(gate),
                output_status="blocked_by_data",
                block_reasons=gate.reasons,
            )
            conn.commit()
            handoff_result = {"reason": "freshness_gate_block", "handoff": None}
            log_run(
                SCRIPT_NAME,
                "success",
                "paper trade watchlist blocked by freshness gate",
                {
                    "registry_entry_id": registry_entry["id"],
                    "summary_rel_path": relative_to_project(output_path),
                    "ticket_count": 0,
                    "freshness_gate_status": gate.status,
                    "block_reasons": gate.reasons,
                },
            )
            print(f"Paper trade watchlist: {relative_to_project(output_path)}")
            print("  status=blocked_by_data")
            return
        radar_snapshot = latest_registry_snapshot(conn, "opportunity_radar_snapshot", args.date)
        attack_snapshot = latest_registry_snapshot(conn, "thesis_attack_defense_snapshot", args.date)
        if not radar_snapshot:
            raise SystemExit("No opportunity_radar_snapshot found.")
        if not attack_snapshot:
            raise SystemExit("No thesis_attack_defense_snapshot found.")
        radar_by_symbol = radar_map(radar_snapshot)
        cases = (attack_snapshot.get("payload") or {}).get("cases") or []
        eligible = [
            case
            for case in cases
            if case.get("verdict") in {"paper_watch_ready", "watch_with_evidence"}
        ]
        eligible.sort(key=ticket_rank, reverse=True)
        tickets = [
            build_ticket(case, radar_by_symbol.get(case.get("ts_code")))
            for case in eligible[:limit]
        ]
        payload = {
            "generated_at": generated_at,
            "batch_date": batch_date,
            "mode": "paper_only",
            "live_trading_enabled": False,
            "source_radar_entry_id": radar_snapshot["id"],
            "source_attack_defense_entry_id": attack_snapshot["id"],
            "ticket_count": len(tickets),
            "tickets": tickets,
            "policy_rel_path": relative_to_project(POLICY_PATH),
            "freshness_gate_result": gate_to_dict(gate),
            "data_health_snapshot": gate.data_health_snapshot,
        }
        payload["overview_lines"] = overview_lines(tickets, cases)
        write_markdown(output_path, payload)
        registry_entry = register_snapshot(
            conn,
            entity_type="paper_trade_watchlist_snapshot",
            entity_id=batch_date,
            status="generated" if tickets else "empty",
            source=SCRIPT_NAME,
            relationships={
                "summary_rel_path": relative_to_project(output_path),
                "source_radar_entry_id": radar_snapshot["id"],
                "source_attack_defense_entry_id": attack_snapshot["id"],
            },
            payload={**payload, "summary_rel_path": relative_to_project(output_path)},
            created_at=generated_at,
        )
        handoff_result = ensure_auto_handoff(
            conn,
            registry_entry,
            note="纸面机会观察单已生成，自动转交研究代理同步到调度候选。",
            created_by=SCRIPT_NAME,
        )
        record_agent_run(
            conn,
            agent_or_script=SCRIPT_NAME,
            status="success",
            entity_type="paper_trade_watchlist_snapshot",
            entity_id=batch_date,
            data_health_snapshot=gate.data_health_snapshot,
            freshness_gate_result=gate_to_dict(gate),
            output_status=registry_entry["status"],
        )
        conn.commit()
    finally:
        conn.close()

    log_run(
        SCRIPT_NAME,
        "success",
        "paper trade watchlist built",
        {
            "registry_entry_id": registry_entry["id"],
            "summary_rel_path": relative_to_project(output_path),
            "ticket_count": payload["ticket_count"],
            "mode": "paper_only",
            "handoff_result": handoff_result["reason"],
            "handoff_id": handoff_result["handoff"]["handoff_id"] if handoff_result["handoff"] else None,
        },
    )
    print(f"Paper trade watchlist: {relative_to_project(output_path)}")
    print(f"  ticket_count={payload['ticket_count']}")


if __name__ == "__main__":
    main()
