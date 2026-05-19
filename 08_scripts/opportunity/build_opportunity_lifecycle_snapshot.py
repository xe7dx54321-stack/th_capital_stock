#!/usr/bin/env python3
"""Track opportunity candidates across radar runs and classify lifecycle changes."""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import ensure_auto_handoff
from smr_paths import env_or_project_path, relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run

DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")
OUTPUT_DIR = env_or_project_path("SMR_OPPORTUNITY_LIFECYCLE_DIR", "02_research", "opportunity_lifecycle")
SCRIPT_NAME = "build_opportunity_lifecycle_snapshot.py"

BUCKET_RANK = {
    "monitor_only": 0,
    "watch_only": 0,
    "radar_candidate": 1,
    "paper_watch_candidate": 2,
    "high_conviction_watch": 3,
}


def safe_float(value, default=None):
    if value in (None, "", "None", "nan", "-", "--"):
        return default
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(number) or math.isinf(number):
        return default
    return number


def pct_text(value):
    number = safe_float(value)
    if number is None:
        return "-"
    return f"{number:+.2f}%"


def score_text(value):
    number = safe_float(value)
    if number is None:
        return "-"
    return f"{number:.2f}"


def compact_text(value, limit=86):
    text = str(value or "").strip().replace("\n", " ")
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "..."


def registry_row_to_entry(row):
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
        ORDER BY entity_id DESC, datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """,
        params,
    ).fetchone()
    return registry_row_to_entry(row) if row else None


def recent_snapshots(conn, entity_type, limit=30):
    rows = conn.execute(
        """
        SELECT id, entity_type, entity_id, status, source, relationships_json, payload_json, created_at
        FROM task_registry_entity_latest
        WHERE entity_type=?
        ORDER BY entity_id DESC, datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT ?
        """,
        (entity_type, limit),
    ).fetchall()
    return [registry_row_to_entry(row) for row in rows]


def flatten_radar_candidates(snapshot):
    payload = (snapshot or {}).get("payload") or {}
    rows = list(payload.get("candidate_items") or [])
    if not rows:
        for market_items in (payload.get("markets") or {}).values():
            rows.extend(market_items or [])
    if not rows:
        rows = payload.get("top_candidates") or []
    result = {}
    for item in rows:
        ts_code = item.get("ts_code")
        if not ts_code:
            continue
        current = result.get(ts_code)
        if current is None or (safe_float(item.get("opportunity_score"), 0.0) or 0.0) > (
            safe_float(current.get("opportunity_score"), 0.0) or 0.0
        ):
            result[ts_code] = item
    return result


def paper_ticket_map(snapshot):
    payload = (snapshot or {}).get("payload") or {}
    return {item.get("ts_code"): item for item in payload.get("tickets") or [] if item.get("ts_code")}


def evidence_map(snapshot):
    payload = (snapshot or {}).get("payload") or {}
    return {item.get("ts_code"): item for item in payload.get("items") or [] if item.get("ts_code")}


def attack_map(snapshot):
    payload = (snapshot or {}).get("payload") or {}
    return {item.get("ts_code"): item for item in payload.get("cases") or [] if item.get("ts_code")}


def symbol_history(recent_radar_snapshots):
    dates_by_symbol = defaultdict(list)
    scores_by_symbol = defaultdict(list)
    for snapshot in reversed(recent_radar_snapshots):
        entity_id = snapshot.get("entity_id")
        for ts_code, item in flatten_radar_candidates(snapshot).items():
            dates_by_symbol[ts_code].append(entity_id)
            scores_by_symbol[ts_code].append(safe_float(item.get("opportunity_score")))
    return dates_by_symbol, scores_by_symbol


def classify_transition(current, previous, ticket):
    if current and ticket:
        return "paper_watch_active"
    if current and not previous:
        return "new_candidate"
    if previous and not current:
        return "dropped_from_radar"
    if not current:
        return "monitor_only"
    current_score = safe_float(current.get("opportunity_score"), 0.0) or 0.0
    previous_score = safe_float(previous.get("opportunity_score"), 0.0) if previous else None
    delta = current_score - (previous_score or 0.0)
    current_rank = BUCKET_RANK.get(current.get("radar_bucket"), 0)
    previous_rank = BUCKET_RANK.get((previous or {}).get("radar_bucket"), 0)
    if current_rank > previous_rank:
        return "promoted"
    if current_rank < previous_rank:
        return "demoted"
    if delta >= 2.5:
        return "strengthening"
    if delta <= -2.5:
        return "cooling"
    return "persistent_watch"


def action_for_state(state, item, evidence, attack_case):
    best = (evidence or {}).get("best_evidence") or {}
    verdict = (attack_case or {}).get("verdict")
    if state == "new_candidate":
        return "先补事件和研究锚点，避免把首次异动直接升级。"
    if state in {"promoted", "strengthening"}:
        if best.get("evidence_label") == "ready_for_paper_watch" or verdict in {"paper_watch_ready", "watch_with_evidence"}:
            return "允许进入纸面观察复核，仍不触发真实交易。"
        return "优先补策略证据和攻防推演。"
    if state == "paper_watch_active":
        return "进入纸面表现复盘，观察触发和失效条件。"
    if state in {"cooling", "demoted"}:
        return "降级观察，若事件证据无法补强则移出重点跟踪。"
    if state == "dropped_from_radar":
        return "从主动雷达退出，只保留普通覆盖或等待新催化。"
    return "继续观察下一交易日量价是否延续。"


def build_row(ts_code, current, previous, ticket, evidence, attack_case, dates_by_symbol, scores_by_symbol):
    source = current or previous or {}
    current_score = safe_float((current or {}).get("opportunity_score"))
    previous_score = safe_float((previous or {}).get("opportunity_score"))
    score_delta = None
    if current_score is not None and previous_score is not None:
        score_delta = round(current_score - previous_score, 2)
    state = classify_transition(current, previous, ticket)
    dates = dates_by_symbol.get(ts_code) or []
    score_series = [value for value in scores_by_symbol.get(ts_code, []) if value is not None]
    best = (evidence or {}).get("best_evidence") or {}
    return {
        "ts_code": ts_code,
        "name": source.get("name") or ts_code,
        "market": source.get("market"),
        "sector": source.get("sector") or "",
        "lifecycle_state": state,
        "current_bucket": (current or {}).get("radar_bucket"),
        "previous_bucket": (previous or {}).get("radar_bucket"),
        "current_score": current_score,
        "previous_score": previous_score,
        "score_delta": score_delta,
        "latest_pct_chg": ((current or {}).get("metrics") or {}).get("latest_pct_chg"),
        "volume_ratio_20d": ((current or {}).get("metrics") or {}).get("volume_ratio_20d"),
        "first_seen_date": dates[0] if dates else None,
        "last_seen_date": dates[-1] if dates else None,
        "seen_snapshot_count": len(dates),
        "max_score_30r": round(max(score_series), 2) if score_series else None,
        "min_score_30r": round(min(score_series), 2) if score_series else None,
        "evidence_label": best.get("evidence_label"),
        "attack_verdict": (attack_case or {}).get("verdict"),
        "paper_ticket_id": (ticket or {}).get("ticket_id"),
        "next_action": action_for_state(state, current or previous, evidence, attack_case),
    }


def row_sort_key(item):
    state_rank = {
        "paper_watch_active": 5,
        "promoted": 4,
        "strengthening": 3,
        "new_candidate": 2,
        "persistent_watch": 1,
        "cooling": 0,
        "demoted": -1,
        "dropped_from_radar": -2,
    }.get(item.get("lifecycle_state"), 0)
    return (
        -state_rank,
        -(safe_float(item.get("current_score"), safe_float(item.get("previous_score"), 0.0)) or 0.0),
        item.get("ts_code") or "",
    )


def overview_lines(rows, current_count, previous_count):
    counts = Counter(row.get("lifecycle_state") for row in rows)
    lines = [
        f"本轮雷达候选 {current_count} 个，上轮可比候选 {previous_count} 个。",
        (
            f"新进 {counts.get('new_candidate', 0)} 个，强化/晋级 "
            f"{counts.get('strengthening', 0) + counts.get('promoted', 0)} 个，"
            f"降温/降级 {counts.get('cooling', 0) + counts.get('demoted', 0)} 个，"
            f"退出雷达 {counts.get('dropped_from_radar', 0)} 个。"
        ),
        f"当前处于纸面观察的机会 {counts.get('paper_watch_active', 0)} 个，这些进入后续纸面表现复盘。",
    ]
    leaders = [row for row in rows if row.get("lifecycle_state") in {"paper_watch_active", "promoted", "strengthening", "new_candidate"}]
    if leaders:
        names = ", ".join(f"{row['name']}({row['ts_code']})" for row in leaders[:4])
        lines.append(f"优先跟踪：{names}。")
    return lines


def write_markdown(path, payload):
    lines = [
        "# 机会生命周期快照",
        "",
        f"- generated_at: {payload.get('generated_at')}",
        f"- batch_date: {payload.get('batch_date')}",
        f"- source_radar_entry_id: {payload.get('source_radar_entry_id')}",
        f"- previous_radar_entry_id: {payload.get('previous_radar_entry_id') or '-'}",
        "- mode: research lifecycle / paper-only boundary.",
        "",
        "## 核心结论",
        "",
    ]
    lines.extend(f"- {line}" for line in payload.get("overview_lines") or [])
    lines.extend(
        [
            "",
            "## 生命周期明细",
            "",
            "| 标的 | 状态 | 当前分 | 分数变化 | 当前桶 | 证据 | 攻防 | 观察次数 | 下一步 |",
            "| --- | --- | ---: | ---: | --- | --- | --- | ---: | --- |",
        ]
    )
    for row in payload.get("items") or []:
        lines.append(
            "| {subject} | {state} | {score} | {delta} | {bucket} | {evidence} | {attack} | {seen} | {action} |".format(
                subject=f"{row.get('name')} / {row.get('ts_code')}",
                state=row.get("lifecycle_state") or "-",
                score=score_text(row.get("current_score")),
                delta=score_text(row.get("score_delta")),
                bucket=row.get("current_bucket") or "-",
                evidence=row.get("evidence_label") or "-",
                attack=row.get("attack_verdict") or "-",
                seen=row.get("seen_snapshot_count") or 0,
                action=compact_text(row.get("next_action"), 72),
            )
        )
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Build opportunity lifecycle snapshot")
    parser.add_argument("--date", help="Radar entity date; defaults to latest radar snapshot")
    parser.add_argument("--history-limit", type=int, default=30)
    args = parser.parse_args()

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    batch_date = generated_at[:10]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{batch_date}_opportunity_lifecycle_snapshot.md"

    conn = sqlite3.connect(DB_PATH)
    try:
        radar_snapshot = latest_registry_snapshot(conn, "opportunity_radar_snapshot", args.date)
        if not radar_snapshot:
            raise SystemExit("No opportunity_radar_snapshot found.")
        recent_radar = recent_snapshots(conn, "opportunity_radar_snapshot", args.history_limit)
        comparable = [snapshot for snapshot in recent_radar if snapshot.get("entity_id") != radar_snapshot.get("entity_id")]
        previous_radar = comparable[0] if comparable else None
        paper_snapshot = latest_registry_snapshot(conn, "paper_trade_watchlist_snapshot", radar_snapshot["entity_id"])
        evidence_snapshot = latest_registry_snapshot(conn, "strategy_evidence_snapshot", radar_snapshot["entity_id"])
        attack_snapshot = latest_registry_snapshot(conn, "thesis_attack_defense_snapshot", radar_snapshot["entity_id"])

        current = flatten_radar_candidates(radar_snapshot)
        previous = flatten_radar_candidates(previous_radar)
        tickets = paper_ticket_map(paper_snapshot)
        evidences = evidence_map(evidence_snapshot)
        attacks = attack_map(attack_snapshot)
        dates_by_symbol, scores_by_symbol = symbol_history(recent_radar)
        symbols = sorted(set(current) | set(previous))
        rows = [
            build_row(
                ts_code,
                current.get(ts_code),
                previous.get(ts_code),
                tickets.get(ts_code),
                evidences.get(ts_code),
                attacks.get(ts_code),
                dates_by_symbol,
                scores_by_symbol,
            )
            for ts_code in symbols
        ]
        rows.sort(key=row_sort_key)
        state_counts = dict(Counter(row.get("lifecycle_state") for row in rows))
        payload = {
            "generated_at": generated_at,
            "batch_date": batch_date,
            "source_radar_entry_id": radar_snapshot["id"],
            "source_radar_entity_id": radar_snapshot["entity_id"],
            "previous_radar_entry_id": (previous_radar or {}).get("id"),
            "previous_radar_entity_id": (previous_radar or {}).get("entity_id"),
            "current_candidate_count": len(current),
            "previous_candidate_count": len(previous),
            "state_counts": state_counts,
            "items": rows,
        }
        payload["overview_lines"] = overview_lines(rows, len(current), len(previous))
        write_markdown(output_path, payload)
        registry_entry = register_snapshot(
            conn,
            entity_type="opportunity_lifecycle_snapshot",
            entity_id=batch_date,
            status="generated" if rows else "empty",
            source=SCRIPT_NAME,
            relationships={
                "summary_rel_path": relative_to_project(output_path),
                "source_radar_entry_id": radar_snapshot["id"],
                "previous_radar_entry_id": (previous_radar or {}).get("id"),
            },
            payload={**payload, "summary_rel_path": relative_to_project(output_path)},
            created_at=generated_at,
        )
        handoff_result = ensure_auto_handoff(
            conn,
            registry_entry,
            note="机会生命周期快照已生成，自动转交研究代理识别新进、强化、降温和退出。",
            created_by=SCRIPT_NAME,
        )
        conn.commit()
    finally:
        conn.close()

    log_run(
        SCRIPT_NAME,
        "success",
        "opportunity lifecycle snapshot built",
        {
            "registry_entry_id": registry_entry["id"],
            "summary_rel_path": relative_to_project(output_path),
            "item_count": len(rows),
            "state_counts": state_counts,
            "handoff_result": handoff_result["reason"],
            "handoff_id": handoff_result["handoff"]["handoff_id"] if handoff_result["handoff"] else None,
        },
    )
    print(f"Opportunity lifecycle snapshot: {relative_to_project(output_path)}")
    print(f"  item_count={len(rows)}")
    print(f"  state_counts={state_counts}")


if __name__ == "__main__":
    main()
