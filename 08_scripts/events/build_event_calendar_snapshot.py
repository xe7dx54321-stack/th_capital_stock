#!/usr/bin/env python3
"""Build a market-event calendar snapshot for the active SMR equity universe."""

import argparse
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_events import EVENT_OUTPUT_DIR
from smr_paths import project_path, relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_universe import load_active_equity_universe
from smr_wiki import loads_json, now_ts

DB_PATH = project_path("01_data", "db", "smr.db")
CALENDAR_TYPES = {
    "board_meeting_notice",
    "annual_results_announcement",
    "interim_results_announcement",
    "quarterly_report",
    "earnings_preannouncement",
    "dividend_notice",
    "equity_movement",
    "monthly_return",
}
UPCOMING_CALENDAR_TYPES = {
    "earnings_calendar_item",
    "corp_action_calendar_item",
}


def fetch_rows(conn, ts_codes, cutoff_date):
    placeholders = ",".join("?" for _ in ts_codes)
    params = [*ts_codes, cutoff_date]
    return conn.execute(
        f"""
        SELECT
            entity_id,
            event_family,
            event_type,
            title,
            event_date,
            publish_time,
            market_effective_time,
            importance,
            source_key,
            source_rel_path,
            payload_json
        FROM market_event
        WHERE entity_type='stock'
          AND entity_id IN ({placeholders})
          AND COALESCE(event_date, substr(publish_time, 1, 10), '1900-01-01') >= ?
        ORDER BY datetime(COALESCE(publish_time, created_at)) DESC, event_date DESC, event_id DESC
        """,
        params,
    ).fetchall()


def render_event_block(lines, event):
    payload = loads_json(event["payload_json"], {})
    summary = payload.get("summary") or "-"
    lines.extend(
        [
            f"### {event['name']} / {event['entity_id']}",
            "",
            f"- family/type: `{event['event_family']}` / `{event['event_type']}`",
            f"- event_date: `{event.get('event_date') or '-'}`",
            f"- publish_time: `{event.get('publish_time') or '-'}`",
            f"- market_effective_time: `{event.get('market_effective_time') or '-'}`",
            f"- importance: `{event['importance']}`",
            f"- source_key: `{event['source_key']}`",
            f"- source_rel_path: `{event.get('source_rel_path') or '-'}`",
            f"- summary: {summary}",
            "",
        ]
    )


def write_snapshot(path, created_at, universe, rows, days_back):
    counts_by_family = defaultdict(int)
    counts_by_type = defaultdict(int)
    calendar_rows = []
    upcoming_rows = []
    grouped = defaultdict(list)
    upcoming_by_symbol = defaultdict(list)
    snapshot_date = created_at[:10]

    for row in rows:
        counts_by_family[row["event_family"]] += 1
        counts_by_type[row["event_type"]] += 1
        grouped[row["entity_id"]].append(row)
        if row["event_type"] in CALENDAR_TYPES:
            calendar_rows.append(row)
        if row["event_type"] in UPCOMING_CALENDAR_TYPES and (row.get("event_date") or "") >= snapshot_date:
            upcoming_rows.append(row)
            upcoming_by_symbol[row["entity_id"]].append(row)

    lines = [
        "# SMR 事件日历快照",
        "",
        f"- created_at: {created_at}",
        f"- lookback_days: {days_back}",
        f"- tracked_symbol_count: {len(universe)}",
        f"- event_count: {len(rows)}",
        f"- counts_by_family: {dict(counts_by_family)}",
        f"- counts_by_type: {dict(counts_by_type)}",
        "",
        "## 使用边界",
        "",
        "- 当前这份日历快照还是“事件时间线”口径，不等于完整的未来事件预告系统。",
        "- 它优先汇总当前股票池和持仓参照层最近窗口内已经抓到的公告、研报、新闻事件。",
        "- 这版已经补进了从官方材料正文和部分官方 IR 入口页抽出来的近端催化日历，但仍然不是全量交易日历。",
        "",
        "## Upcoming Catalyst Calendar",
        "",
    ]

    if not upcoming_rows:
        lines.append("- 当前窗口内没有识别到明确的未来催化日历。")
        lines.append("")
    else:
        for row in upcoming_rows[:20]:
            render_event_block(lines, row)

    lines.extend(["## Recent Calendar-like Events", ""])
    if not calendar_rows:
        lines.append("- 当前窗口内没有识别到标准 calendar-like 事件。")
        lines.append("")
    else:
        for row in calendar_rows[:20]:
            render_event_block(lines, row)

    lines.extend(["## By Symbol", ""])
    for ts_code in sorted(grouped):
        meta = universe.get(ts_code, {})
        name = meta.get("name") or ts_code
        pool_types = ",".join(meta.get("source_pool_types") or [])
        sector = meta.get("sector") or "-"
        lines.extend(
            [
                f"### {name} / {ts_code}",
                "",
                f"- sector: `{sector}`",
                f"- source_pool_types: `{pool_types or '-'}`",
                f"- recent_event_count: `{len(grouped[ts_code])}`",
                f"- upcoming_event_count: `{len(upcoming_by_symbol.get(ts_code) or [])}`",
                "",
            ]
        )
        for row in (upcoming_by_symbol.get(ts_code) or [])[:2]:
            lines.append(
                "- upcoming / `{event_date}` / `{event_type}` / `{importance}` / {title}".format(
                    event_date=row.get("event_date") or "-",
                    event_type=row["event_type"],
                    importance=row["importance"],
                    title=row["title"],
                )
            )
        for row in grouped[ts_code][:4]:
            lines.append(
                "- `{event_date}` / `{event_family}` / `{event_type}` / `{importance}` / {title}".format(
                    event_date=row.get("event_date") or "-",
                    event_family=row["event_family"],
                    event_type=row["event_type"],
                    importance=row["importance"],
                    title=row["title"],
                )
            )
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "upcoming_event_count": len(upcoming_rows),
        "upcoming_events_by_symbol": {key: len(value) for key, value in upcoming_by_symbol.items()},
    }


def main():
    parser = argparse.ArgumentParser(description="Build event-calendar snapshot for the active SMR equity universe")
    parser.add_argument("--days-back", type=int, default=45, help="Lookback window for market_event rows")
    args = parser.parse_args()

    created_at = now_ts()
    snapshot_date = created_at[:10]
    cutoff_date = (datetime.now() - timedelta(days=args.days_back)).strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB_PATH)
    universe = load_active_equity_universe(conn, include_seed=True)
    ts_codes = sorted(universe)
    if not ts_codes:
        raise SystemExit("No active equity universe available")

    raw_rows = fetch_rows(conn, ts_codes, cutoff_date)
    if not raw_rows:
        raise SystemExit("No market_event rows found for active universe; run normalize_market_events.py first")

    rows = []
    for row in raw_rows:
        event = {
            "entity_id": row[0],
            "event_family": row[1],
            "event_type": row[2],
            "title": row[3],
            "event_date": row[4],
            "publish_time": row[5],
            "market_effective_time": row[6],
            "importance": row[7],
            "source_key": row[8],
            "source_rel_path": row[9],
            "payload_json": row[10],
            "name": universe.get(row[0], {}).get("name") or row[0],
        }
        rows.append(event)

    EVENT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = EVENT_OUTPUT_DIR / f"{snapshot_date}_event_calendar_snapshot.md"
    snapshot_stats = write_snapshot(output_path, created_at, universe, rows, args.days_back)

    entry = register_snapshot(
        conn,
        entity_type="event_calendar_snapshot",
        entity_id=snapshot_date,
        status="compiled",
        source="build_event_calendar_snapshot.py",
        relationships={
            "summary_rel_path": relative_to_project(output_path),
        },
        payload={
            "tracked_symbol_count": len(universe),
            "event_count": len(rows),
            "upcoming_event_count": snapshot_stats["upcoming_event_count"],
            "upcoming_events_by_symbol": snapshot_stats["upcoming_events_by_symbol"],
            "lookback_days": args.days_back,
            "summary_rel_path": relative_to_project(output_path),
        },
    )
    conn.commit()
    conn.close()

    log_run(
        "build_event_calendar_snapshot.py",
        "success",
        "event calendar snapshot built",
        {
            "entity_id": snapshot_date,
            "tracked_symbol_count": len(universe),
            "event_count": len(rows),
            "upcoming_event_count": snapshot_stats["upcoming_event_count"],
            "lookback_days": args.days_back,
            "summary_rel_path": relative_to_project(output_path),
            "registry_entry_id": entry["id"],
        },
    )
    print(f"Event calendar snapshot registered: {snapshot_date}")
    print(f"Summary file: {output_path}")
    print(f"Tracked symbols: {len(universe)}")
    print(f"Event count: {len(rows)}")
    print(f"Upcoming catalyst count: {snapshot_stats['upcoming_event_count']}")


if __name__ == "__main__":
    main()
