#!/usr/bin/env python3
"""Evaluate paper-only opportunity tickets against subsequent market data."""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
import sys
from collections import Counter
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
OUTPUT_DIR = env_or_project_path("SMR_PAPER_PERFORMANCE_DIR", "04_portfolio", "paper")
SCRIPT_NAME = "build_paper_watch_performance_snapshot.py"


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


def render_pct(value):
    number = safe_float(value)
    if number is None:
        return "-"
    return f"{number:+.2%}"


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


def recent_paper_watchlists(conn, limit=20):
    rows = conn.execute(
        """
        SELECT id, entity_type, entity_id, status, source, relationships_json, payload_json, created_at
        FROM task_registry_entity_latest
        WHERE entity_type='paper_trade_watchlist_snapshot'
        ORDER BY entity_id DESC, datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [registry_row_to_entry(row) for row in rows]


def ticket_date_from_id(ticket, snapshot):
    value = ticket.get("reference_trade_date")
    if value:
        return str(value)[:10]
    ticket_id = str(ticket.get("ticket_id") or "")
    maybe = ticket_id.rsplit("__", 1)[-1]
    if len(maybe) == 8 and maybe.isdigit():
        return f"{maybe[:4]}-{maybe[4:6]}-{maybe[6:]}"
    return str(snapshot.get("entity_id") or "")[:10]


def collect_tickets(snapshots):
    rows = {}
    for snapshot in snapshots:
        for ticket in (snapshot.get("payload") or {}).get("tickets") or []:
            ticket_id = ticket.get("ticket_id") or f"paper__{ticket.get('ts_code')}__{snapshot.get('entity_id')}"
            normalized = dict(ticket)
            normalized["ticket_id"] = ticket_id
            normalized["ticket_snapshot_date"] = snapshot.get("entity_id")
            normalized["ticket_snapshot_entry_id"] = snapshot.get("id")
            normalized["reference_trade_date"] = ticket_date_from_id(ticket, snapshot)
            rows[ticket_id] = normalized
    return list(rows.values())


def load_history(conn, ts_code, market):
    if market == "US" or "." not in str(ts_code):
        rows = conn.execute(
            """
            SELECT trade_date, open, high, low, close, pct_chg, vol, amount
            FROM us_daily_bar
            WHERE symbol=?
            ORDER BY trade_date
            """,
            (ts_code,),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT trade_date, open, high, low, close, pct_chg, vol, amount
            FROM daily_bar
            WHERE ts_code=?
            ORDER BY trade_date
            """,
            (ts_code,),
        ).fetchall()
    return [dict(row) for row in rows]


def first_hit(rows, threshold, mode):
    if threshold is None:
        return None
    for row in rows:
        high = safe_float(row.get("high"))
        low = safe_float(row.get("low"))
        close = safe_float(row.get("close"))
        if mode == "observe" and max([value for value in (high, close) if value is not None], default=-math.inf) >= threshold:
            return row
        if mode == "invalidate" and min([value for value in (low, close) if value is not None], default=math.inf) <= threshold:
            return row
    return None


def evaluate_ticket(conn, ticket):
    ts_code = ticket.get("ts_code")
    market = ticket.get("market") or ("US" if "." not in str(ts_code) else "A")
    levels = ticket.get("reference_levels") or {}
    reference_price = safe_float(levels.get("paper_reference_price"))
    observe_above = safe_float(levels.get("observe_above"))
    invalidate_below = safe_float(levels.get("invalidate_below"))
    reference_trade_date = ticket.get("reference_trade_date")
    history = load_history(conn, ts_code, market)
    post_rows = [
        row for row in history if str(row.get("trade_date") or "") > str(reference_trade_date or "")
    ]
    latest_row = post_rows[-1] if post_rows else (history[-1] if history else {})
    if not post_rows or not reference_price:
        status = "awaiting_market_data"
        result_label = "pending"
        action = "等待参考日之后的新行情，不提前评价纸面观察效果。"
    else:
        observe_hit = first_hit(post_rows, observe_above, "observe")
        invalidate_hit = first_hit(post_rows, invalidate_below, "invalidate")
        if invalidate_hit and (not observe_hit or str(invalidate_hit.get("trade_date")) <= str(observe_hit.get("trade_date"))):
            status = "invalidated"
            result_label = "failed_validation"
            action = "从纸面观察单移出，回到研究复盘或普通监控。"
        elif observe_hit:
            status = "trigger_confirmed"
            result_label = "positive_validation"
            action = "纸面触发成立，交给研究和风控代理复核是否具备升级条件。"
        else:
            status = "working"
            result_label = "pending"
            action = "继续纸面观察，重点看量能和失效价带。"

    highs = [value for value in (safe_float(row.get("high")) for row in post_rows) if value is not None]
    lows = [value for value in (safe_float(row.get("low")) for row in post_rows) if value is not None]
    latest_close = safe_float(latest_row.get("close"))
    best_return = None
    worst_return = None
    latest_return = None
    if reference_price and post_rows:
        if highs:
            best_return = max(highs) / reference_price - 1.0
        if lows:
            worst_return = min(lows) / reference_price - 1.0
        if latest_close is not None:
            latest_return = latest_close / reference_price - 1.0
    observe_hit = first_hit(post_rows, observe_above, "observe")
    invalidate_hit = first_hit(post_rows, invalidate_below, "invalidate")
    return {
        "ticket_id": ticket.get("ticket_id"),
        "ts_code": ts_code,
        "name": ticket.get("name") or ts_code,
        "market": market,
        "sector": ticket.get("sector") or "",
        "ticket_snapshot_date": ticket.get("ticket_snapshot_date"),
        "reference_trade_date": reference_trade_date,
        "reference_price": reference_price,
        "observe_above": observe_above,
        "invalidate_below": invalidate_below,
        "latest_trade_date": latest_row.get("trade_date"),
        "latest_close": latest_close,
        "days_tracked": len(post_rows),
        "latest_return": round(latest_return, 4) if latest_return is not None else None,
        "best_return": round(best_return, 4) if best_return is not None else None,
        "worst_return": round(worst_return, 4) if worst_return is not None else None,
        "status": status,
        "result_label": result_label,
        "observe_hit_date": (observe_hit or {}).get("trade_date"),
        "invalidate_hit_date": (invalidate_hit or {}).get("trade_date"),
        "source_verdict": ticket.get("verdict"),
        "evidence_label": ticket.get("evidence_label"),
        "action": action,
    }


def item_sort_key(item):
    rank = {
        "trigger_confirmed": 4,
        "working": 3,
        "awaiting_market_data": 2,
        "invalidated": 1,
    }.get(item.get("status"), 0)
    return (
        -rank,
        -(safe_float(item.get("latest_return"), -99.0) or -99.0),
        item.get("ts_code") or "",
    )


def overview_lines(items):
    counts = Counter(item.get("status") for item in items)
    lines = [
        f"本轮复盘 {len(items)} 张纸面观察单。",
        (
            f"已触发验证 {counts.get('trigger_confirmed', 0)} 张，"
            f"仍在观察 {counts.get('working', 0)} 张，"
            f"等待新行情 {counts.get('awaiting_market_data', 0)} 张，"
            f"已失效 {counts.get('invalidated', 0)} 张。"
        ),
    ]
    confirmed = [item for item in items if item.get("status") == "trigger_confirmed"]
    if confirmed:
        leaders = ", ".join(f"{item['name']}({item['ts_code']})" for item in confirmed[:4])
        lines.append(f"纸面触发成立：{leaders}。")
    return lines


def write_markdown(path, payload):
    lines = [
        "# 纸面观察表现复盘",
        "",
        f"- generated_at: {payload.get('generated_at')}",
        f"- batch_date: {payload.get('batch_date')}",
        "- mode: paper_only performance review.",
        "",
        "## 核心结论",
        "",
    ]
    lines.extend(f"- {line}" for line in payload.get("overview_lines") or [])
    lines.extend(
        [
            "",
            "## 观察单表现",
            "",
            "| 标的 | 状态 | 跟踪日 | 最新收益 | 最好/最差 | 触发日 | 失效日 | 下一步 |",
            "| --- | --- | ---: | ---: | --- | --- | --- | --- |",
        ]
    )
    for item in payload.get("items") or []:
        lines.append(
            "| {subject} | {status} | {days} | {latest} | {best} / {worst} | {hit} | {invalid} | {action} |".format(
                subject=f"{item.get('name')} / {item.get('ts_code')}",
                status=item.get("status") or "-",
                days=item.get("days_tracked") or 0,
                latest=render_pct(item.get("latest_return")),
                best=render_pct(item.get("best_return")),
                worst=render_pct(item.get("worst_return")),
                hit=item.get("observe_hit_date") or "-",
                invalid=item.get("invalidate_hit_date") or "-",
                action=compact_text(item.get("action"), 74),
            )
        )
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Build paper watch performance snapshot")
    parser.add_argument("--date", help="Paper watchlist entity date; defaults to latest")
    parser.add_argument("--history-limit", type=int, default=20, help="How many paper watchlist dates to evaluate")
    args = parser.parse_args()

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    batch_date = generated_at[:10]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{batch_date}_paper_watch_performance.md"

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        if args.date:
            snapshot = latest_registry_snapshot(conn, "paper_trade_watchlist_snapshot", args.date)
            watchlists = [snapshot] if snapshot else []
        else:
            watchlists = recent_paper_watchlists(conn, args.history_limit)
        if not watchlists:
            raise SystemExit("No paper_trade_watchlist_snapshot found.")
        tickets = collect_tickets(watchlists)
        items = [evaluate_ticket(conn, ticket) for ticket in tickets]
        items.sort(key=item_sort_key)
        status_counts = dict(Counter(item.get("status") for item in items))
        payload = {
            "generated_at": generated_at,
            "batch_date": batch_date,
            "evaluated_ticket_count": len(items),
            "status_counts": status_counts,
            "source_watchlist_entry_ids": [snapshot.get("id") for snapshot in watchlists],
            "items": items,
        }
        payload["overview_lines"] = overview_lines(items)
        write_markdown(output_path, payload)
        registry_entry = register_snapshot(
            conn,
            entity_type="paper_watch_performance_snapshot",
            entity_id=batch_date,
            status="generated" if items else "empty",
            source=SCRIPT_NAME,
            relationships={
                "summary_rel_path": relative_to_project(output_path),
                "source_watchlist_entry_ids": [snapshot.get("id") for snapshot in watchlists],
            },
            payload={**payload, "summary_rel_path": relative_to_project(output_path)},
            created_at=generated_at,
        )
        handoff_result = ensure_auto_handoff(
            conn,
            registry_entry,
            note="纸面观察表现复盘已生成，自动转交研究代理沉淀触发、失效和学习反馈。",
            created_by=SCRIPT_NAME,
        )
        conn.commit()
    finally:
        conn.close()

    log_run(
        SCRIPT_NAME,
        "success",
        "paper watch performance snapshot built",
        {
            "registry_entry_id": registry_entry["id"],
            "summary_rel_path": relative_to_project(output_path),
            "evaluated_ticket_count": len(items),
            "status_counts": status_counts,
            "handoff_result": handoff_result["reason"],
            "handoff_id": handoff_result["handoff"]["handoff_id"] if handoff_result["handoff"] else None,
        },
    )
    print(f"Paper watch performance snapshot: {relative_to_project(output_path)}")
    print(f"  evaluated_ticket_count={len(items)}")
    print(f"  status_counts={status_counts}")


if __name__ == "__main__":
    main()
