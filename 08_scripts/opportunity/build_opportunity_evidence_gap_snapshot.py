#!/usr/bin/env python3
"""Build and optionally fill evidence gaps for active opportunity candidates."""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import ensure_auto_handoff
from smr_paths import env_or_project_path, project_path, relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run

DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")
OUTPUT_DIR = env_or_project_path("SMR_OPPORTUNITY_EVIDENCE_GAP_DIR", "02_research", "opportunity_evidence")
SCRIPT_NAME = "build_opportunity_evidence_gap_snapshot.py"
PYTHON = sys.executable
PROJECT_ROOT = project_path()


def safe_float(value, default=None):
    if value in (None, "", "None", "nan", "-", "--"):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


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
    return registry_row_to_entry(row)


def radar_candidates(radar_snapshot):
    payload = (radar_snapshot or {}).get("payload") or {}
    rows = []
    seen = set()
    for ticket in payload.get("top_candidates") or []:
        ts_code = ticket.get("ts_code")
        if ts_code and ts_code not in seen:
            rows.append(ticket)
            seen.add(ts_code)
    for market_items in (payload.get("markets") or {}).values():
        for item in market_items or []:
            ts_code = item.get("ts_code")
            if ts_code and ts_code not in seen:
                rows.append(item)
                seen.add(ts_code)
    rows.sort(key=lambda item: (safe_float(item.get("opportunity_score"), 0.0) or 0.0), reverse=True)
    return rows


def paper_watch_candidates(watch_snapshot):
    payload = (watch_snapshot or {}).get("payload") or {}
    rows = []
    for ticket in payload.get("tickets") or []:
        item = {
            "ts_code": ticket.get("ts_code"),
            "name": ticket.get("name"),
            "market": ticket.get("market"),
            "sector": ticket.get("sector"),
            "opportunity_score": ticket.get("opportunity_score"),
            "signal_tags": ticket.get("signal_tags") or [],
            "radar_bucket": "paper_watch_active",
            "verdict": ticket.get("verdict"),
        }
        if item["ts_code"]:
            rows.append(item)
    return rows


def merged_candidates(radar_snapshot, watch_snapshot, limit):
    rows = []
    seen = set()
    for item in [*paper_watch_candidates(watch_snapshot), *radar_candidates(radar_snapshot)]:
        ts_code = item.get("ts_code")
        if not ts_code or ts_code in seen:
            continue
        rows.append(item)
        seen.add(ts_code)
        if len(rows) >= limit:
            break
    return rows


def source_stats(conn, ts_code, today):
    if not relation_exists(conn, "source_manifest"):
        return {"recent_source_count": 0, "source_count": 0}
    candidates = [ts_code, str(ts_code or "").lower(), str(ts_code or "").upper()]
    placeholders = ",".join("?" for _ in candidates)
    rows = conn.execute(
        f"""
        SELECT title, source_type, source_rel_path, updated_at, tags
        FROM source_manifest
        WHERE entity_type='stock'
          AND entity_id IN ({placeholders})
          AND status='active'
        ORDER BY datetime(updated_at) DESC
        LIMIT 12
        """,
        candidates,
    ).fetchall()
    latest_updated = rows[0][3] if rows else None
    latest_day = parse_date(latest_updated)
    age = business_day_age(latest_day, today)
    recent = [row for row in rows if business_day_age(parse_date(row[3]), today) is not None and business_day_age(parse_date(row[3]), today) <= 3]
    return {
        "source_count": len(rows),
        "recent_source_count": len(recent),
        "latest_source_updated_at": latest_updated,
        "latest_source_age_bd": age,
        "latest_sources": [
            {
                "title": row[0],
                "source_type": row[1],
                "source_rel_path": row[2],
                "updated_at": row[3],
                "tags": json.loads(row[4] or "[]"),
            }
            for row in rows[:5]
        ],
    }


def latest_event(conn, ts_code, today):
    if not relation_exists(conn, "market_event_latest"):
        return {}
    row = conn.execute(
        """
        SELECT title, event_type, event_date, publish_time, importance, source_rel_path
        FROM market_event_latest
        WHERE entity_type='stock' AND entity_id=?
        ORDER BY datetime(COALESCE(publish_time, event_date, created_at)) DESC
        LIMIT 1
        """,
        (ts_code,),
    ).fetchone()
    if not row:
        return {}
    event_day = parse_date(row[3] or row[2])
    return {
        "title": row[0],
        "event_type": row[1],
        "event_date": row[2],
        "publish_time": row[3],
        "age_business_days": business_day_age(event_day, today),
        "importance": row[4],
        "source_rel_path": row[5],
    }


def classify_evidence(item, stats, event):
    tags = item.get("signal_tags") or []
    event_age = event.get("age_business_days")
    event_is_fresh = event_age is not None and event_age <= 3
    if stats.get("recent_source_count", 0) > 0 or event_is_fresh:
        state = "event_backed"
    elif stats.get("source_count", 0) > 0 or event:
        state = "stale_evidence"
    else:
        state = "price_only"
    if "overheat_watch" in tags and state != "event_backed":
        state = "overheated_without_fresh_evidence"
    return state


def recommended_action(item, evidence_state):
    market = item.get("market") or ("US" if "." not in str(item.get("ts_code")) else "A")
    if evidence_state == "event_backed":
        return "进入攻防和纸面观察复核，重点看事件是否能解释价格。"
    if evidence_state == "stale_evidence":
        return "补抓最近公告/新闻/研报摘要，确认旧 thesis 是否仍成立。"
    if evidence_state == "overheated_without_fresh_evidence":
        return "先不升级，优先补来源；若补不到事件支撑，只保留过热监控。"
    if market == "A":
        return "自动补抓东方财富资讯搜索和正文，补齐事件锚点。"
    return "列为人工/后续适配器补证据对象。"


def build_rows(conn, candidates, today):
    rows = []
    for item in candidates:
        ts_code = item.get("ts_code")
        stats = source_stats(conn, ts_code, today)
        event = latest_event(conn, ts_code, today)
        evidence_state = classify_evidence(item, stats, event)
        row = {
            "ts_code": ts_code,
            "name": item.get("name") or ts_code,
            "market": item.get("market") or ("US" if "." not in str(ts_code) else "A"),
            "sector": item.get("sector") or "",
            "opportunity_score": item.get("opportunity_score"),
            "radar_bucket": item.get("radar_bucket") or "",
            "verdict": item.get("verdict") or "",
            "signal_tags": item.get("signal_tags") or [],
            "evidence_state": evidence_state,
            "recommended_action": recommended_action(item, evidence_state),
            "latest_event": event,
            **stats,
        }
        rows.append(row)
    return rows


def fetch_targets(rows, limit):
    targets = []
    for row in rows:
        if row.get("market") != "A":
            continue
        if row.get("evidence_state") not in {"price_only", "stale_evidence", "overheated_without_fresh_evidence"}:
            continue
        ts_code = row.get("ts_code")
        if ts_code and ts_code not in targets:
            targets.append(ts_code)
        if len(targets) >= limit:
            break
    return targets


def run_command(command, dry_run):
    if dry_run:
        return {
            "command": subprocess.list2cmdline(command),
            "returncode": 0,
            "dry_run": True,
            "output_tail": "(dry-run)",
        }
    completed = subprocess.run(command, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    output = ((completed.stdout or "") + (completed.stderr or "")).strip()
    return {
        "command": subprocess.list2cmdline(command),
        "returncode": completed.returncode,
        "dry_run": False,
        "output_tail": output[-1200:],
    }


def run_a_share_evidence_fetch(targets, args):
    if not targets:
        return []
    base = [PYTHON]
    commands = [
        [
            *base,
            str(project_path("08_scripts", "wiki", "fetch_eastmoney_news_search.py")),
            *sum([["--ts-code", code] for code in targets], []),
            "--sort",
            "time",
            "--per-symbol-limit",
            str(args.per_symbol_limit),
        ],
        [
            *base,
            str(project_path("08_scripts", "wiki", "fetch_eastmoney_news_articles.py")),
            *sum([["--ts-code", code] for code in targets], []),
            "--article-limit",
            str(args.article_limit),
            "--fetch-mode",
            "auto",
        ],
        [
            *base,
            str(project_path("08_scripts", "wiki", "build_source_manifest.py")),
        ],
    ]
    results = []
    for command in commands:
        result = run_command(command, args.dry_run)
        results.append(result)
        if result["returncode"] != 0 and not args.continue_on_error:
            break
    return results


def compact_text(value, limit=74):
    text = str(value or "").strip().replace("\n", " ")
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "..."


def write_markdown(path, payload):
    lines = [
        "# 机会证据缺口快照",
        "",
        f"- generated_at: {payload['generated_at']}",
        f"- batch_date: {payload['batch_date']}",
        f"- mode: evidence_gap_and_optional_fetch",
        f"- fetch_a_share_news: `{payload['fetch_a_share_news']}`",
        "",
        "## 核心结论",
        "",
    ]
    for line in payload["overview_lines"]:
        lines.append(f"- {line}")
    lines.extend(
        [
            "",
            "## 证据状态",
            "",
            "| 标的 | 分数 | 状态 | 最近来源 | 最近事件 | 下一步 |",
            "| --- | ---: | --- | --- | --- | --- |",
        ]
    )
    for row in payload["items"]:
        event_title = compact_text((row.get("latest_event") or {}).get("title"), 42) or "-"
        lines.append(
            "| {subject} | {score} | {state} | {source} | {event} | {action} |".format(
                subject=f"{row.get('name')} / {row.get('ts_code')}",
                score=f"{safe_float(row.get('opportunity_score'), 0.0):.2f}",
                state=row.get("evidence_state") or "-",
                source=row.get("latest_source_updated_at") or "-",
                event=event_title,
                action=compact_text(row.get("recommended_action"), 58),
            )
        )
    if payload["fetch_results"]:
        lines.extend(["", "## 自动补抓执行", ""])
        for result in payload["fetch_results"]:
            lines.append(f"- returncode={result['returncode']} command=`{result['command']}`")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Build opportunity evidence gap snapshot")
    parser.add_argument("--date", help="Snapshot date; defaults to latest")
    parser.add_argument("--limit", type=int, default=10, help="Candidate count to inspect")
    parser.add_argument("--fetch-limit", type=int, default=5, help="Max A-share symbols to fetch when enabled")
    parser.add_argument("--per-symbol-limit", type=int, default=3)
    parser.add_argument("--article-limit", type=int, default=2)
    parser.add_argument("--fetch-a-share-news", action="store_true", help="Fetch Eastmoney news for A-share evidence gaps")
    parser.add_argument("--continue-on-error", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    batch_date = generated_at[:10]
    today = datetime.now().date()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{batch_date}_opportunity_evidence_gap_snapshot.md"

    conn = sqlite3.connect(DB_PATH)
    try:
        radar_snapshot = latest_registry_snapshot(conn, "opportunity_radar_snapshot", args.date)
        watch_snapshot = latest_registry_snapshot(conn, "paper_trade_watchlist_snapshot", args.date)
        if not radar_snapshot:
            raise SystemExit("No opportunity_radar_snapshot found.")
        candidates = merged_candidates(radar_snapshot, watch_snapshot, args.limit)
        initial_rows = build_rows(conn, candidates, today)
        targets = fetch_targets(initial_rows, args.fetch_limit)
    finally:
        conn.close()

    fetch_results = []
    if args.fetch_a_share_news and targets:
        fetch_results = run_a_share_evidence_fetch(targets, args)

    conn = sqlite3.connect(DB_PATH)
    try:
        rows = build_rows(conn, candidates, today)
        state_counts = dict(Counter(row["evidence_state"] for row in rows))
        gap_count = sum(
            1
            for row in rows
            if row["evidence_state"] in {"price_only", "stale_evidence", "overheated_without_fresh_evidence"}
        )
        payload = {
            "generated_at": generated_at,
            "batch_date": batch_date,
            "source_radar_entry_id": radar_snapshot.get("id"),
            "source_paper_watchlist_entry_id": (watch_snapshot or {}).get("id"),
            "candidate_count": len(rows),
            "gap_count": gap_count,
            "state_counts": state_counts,
            "fetch_a_share_news": bool(args.fetch_a_share_news),
            "fetch_targets": targets if args.fetch_a_share_news else [],
            "fetch_results": fetch_results,
            "items": rows,
            "overview_lines": [
                f"本轮检查 {len(rows)} 个高分/纸面观察机会，证据状态分布：{state_counts}。",
                f"仍有 {gap_count} 个机会缺少新鲜事件证据或证据偏旧。",
                "价格信号只有在补齐事件、公告、研报或 IR 证据后，才允许进入更高层级判断。",
            ],
        }
        write_markdown(output_path, payload)
        failed_fetches = [item for item in fetch_results if item["returncode"] != 0]
        registry_entry = register_snapshot(
            conn,
            entity_type="opportunity_evidence_gap_snapshot",
            entity_id=batch_date,
            status="partial_failure" if failed_fetches else ("needs_evidence" if gap_count else "event_backed"),
            source=SCRIPT_NAME,
            relationships={
                "summary_rel_path": relative_to_project(output_path),
                "source_radar_entry_id": radar_snapshot.get("id"),
                "source_paper_watchlist_entry_id": (watch_snapshot or {}).get("id"),
            },
            payload={**payload, "summary_rel_path": relative_to_project(output_path)},
            created_at=generated_at,
        )
        handoff_result = ensure_auto_handoff(
            conn,
            registry_entry,
            note="机会证据缺口快照已生成，请研究代理把价格信号和事件证据差距同步到当前状态面。",
            created_by=SCRIPT_NAME,
        )
        conn.commit()
    finally:
        conn.close()

    log_run(
        SCRIPT_NAME,
        "success" if not failed_fetches else "partial_failure",
        "opportunity evidence gap snapshot built",
        {
            "registry_entry_id": registry_entry["id"],
            "summary_rel_path": relative_to_project(output_path),
            "candidate_count": len(rows),
            "gap_count": gap_count,
            "state_counts": state_counts,
            "fetch_targets": targets if args.fetch_a_share_news else [],
            "failed_fetch_count": len(failed_fetches),
            "handoff_result": handoff_result["reason"],
            "handoff_id": handoff_result["handoff"]["handoff_id"] if handoff_result["handoff"] else None,
        },
    )
    print(f"Opportunity evidence gap snapshot: {relative_to_project(output_path)}")
    print(f"  candidate_count={len(rows)}")
    print(f"  gap_count={gap_count}")
    print(f"  state_counts={state_counts}")


if __name__ == "__main__":
    main()
