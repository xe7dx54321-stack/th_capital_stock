#!/usr/bin/env python3
"""Build a cross-market flow anomaly snapshot for the current covered universe."""

from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_flow_event_digest import latest_margin_hit, ordered_unique, parse_date_value
from smr_paths import env_or_project_path, relative_to_project
from smr_data_health import blocked_payload_for_gate, check_freshness_gate, gate_to_dict
from smr_decision import record_agent_run
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_universe import combined_name_map

DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")
OUTPUT_DIR = env_or_project_path("SMR_MARKET_FLOW_REPORT_DIR", "06_reports", "adhoc", "market_flow")
SCRIPT_NAME = "build_market_flow_anomaly_snapshot.py"

MARKET_LABELS = {
    "A": "A股",
    "H": "港股",
    "US": "美股",
}

MARKET_CODE_ORDER = ("A", "H", "US")
MARKET_LIMITS = {
    "A": 10,
    "H": 10,
    "US": 10,
}


def safe_float(value):
    if value in (None, "", "None", "nan", "-", "--"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def compact_text(value, limit=88):
    text = str(value or "").strip().replace("\n", " ")
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def amount_text(value, market):
    number = safe_float(value)
    if number is None:
        return "-"
    currency = {"A": "元", "H": "港元", "US": "美元"}.get(market, "")
    if abs(number) >= 100000000:
        return f"{number / 100000000:.2f} 亿{currency}"
    if abs(number) >= 10000:
        return f"{number / 10000:.2f} 万{currency}"
    return f"{number:.0f}{currency}"


def avg(values):
    rows = [safe_float(value) for value in values if safe_float(value) is not None]
    if not rows:
        return None
    return sum(rows) / len(rows)


def latest_event_by_symbol(conn):
    rows = conn.execute(
        """
        SELECT
            entity_id,
            title,
            event_family,
            event_type,
            event_date,
            publish_time,
            importance,
            source_rel_path,
            payload_json
        FROM market_event_latest
        WHERE entity_type='stock'
        ORDER BY datetime(COALESCE(publish_time, created_at)) DESC, event_id DESC
        """
    ).fetchall()
    latest = {}
    for row in rows:
        symbol = row[0]
        if not symbol or symbol in latest:
            continue
        payload = {}
        try:
            payload = json.loads(row[8] or "{}")
        except json.JSONDecodeError:
            payload = {}
        latest[symbol] = {
            "title": row[1],
            "event_family": row[2],
            "event_type": row[3],
            "event_date": row[4],
            "publish_time": row[5],
            "importance": row[6],
            "source_rel_path": row[7],
            "payload": payload,
        }
    return latest


def load_pool_types(conn):
    rows = conn.execute(
        """
        SELECT ts_code, GROUP_CONCAT(DISTINCT pool_type)
        FROM stock_pool_current
        GROUP BY ts_code
        """
    ).fetchall()
    return {
        row[0]: ordered_unique((row[1] or "").split(","))
        for row in rows
        if row[0]
    }


def load_a_h_rows(conn):
    rows = conn.execute(
        """
        WITH latest_trade AS (
            SELECT market, MAX(trade_date) AS latest_trade_date
            FROM daily_bar
            GROUP BY market
        )
        SELECT
            d.ts_code,
            d.market,
            d.trade_date,
            d.close,
            d.pct_chg,
            d.vol,
            d.amount
        FROM daily_bar d
        JOIN latest_trade lt
          ON lt.market = d.market
         AND lt.latest_trade_date = d.trade_date
        ORDER BY d.market, d.amount DESC, d.ts_code
        """
    ).fetchall()
    return [dict(row) for row in rows]


def load_us_rows(conn):
    rows = conn.execute(
        """
        WITH latest_trade AS (
            SELECT MAX(trade_date) AS latest_trade_date
            FROM us_daily_bar
        )
        SELECT
            symbol,
            trade_date,
            close,
            pct_chg,
            vol,
            amount
        FROM us_daily_bar, latest_trade
        WHERE trade_date = latest_trade.latest_trade_date
        ORDER BY vol DESC, symbol
        """
    ).fetchall()
    return [dict(row) for row in rows]


def load_recent_windows(conn, symbol, market, limit=21):
    if market == "US":
        rows = conn.execute(
            """
            SELECT trade_date, close, pct_chg, vol, amount
            FROM us_daily_bar
            WHERE symbol=?
            ORDER BY trade_date DESC
            LIMIT ?
            """,
            (symbol, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT trade_date, close, pct_chg, vol, amount
            FROM daily_bar
            WHERE ts_code=?
            ORDER BY trade_date DESC
            LIMIT ?
            """,
            (symbol, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def compute_flow_score(latest_row, trailing_rows, market, margin_hit=None):
    latest_pct_chg = abs(safe_float(latest_row.get("pct_chg")) or 0.0)
    latest_vol = safe_float(latest_row.get("vol")) or 0.0
    latest_amount = safe_float(latest_row.get("amount")) or 0.0
    base_rows = trailing_rows[1:] if len(trailing_rows) > 1 else []
    avg_vol_20d = avg(row.get("vol") for row in base_rows)
    avg_amount_20d = avg(row.get("amount") for row in base_rows)
    volume_ratio = round(latest_vol / avg_vol_20d, 2) if avg_vol_20d and avg_vol_20d > 0 else None
    amount_ratio = round(latest_amount / avg_amount_20d, 2) if avg_amount_20d and avg_amount_20d > 0 else None

    score = latest_pct_chg * 0.65
    if volume_ratio is not None:
        score += min(volume_ratio, 6.0) * 1.7
    if amount_ratio is not None and market in {"A", "H"}:
        score += min(amount_ratio, 6.0) * 1.2
    if market == "US" and volume_ratio is not None:
        score += min(volume_ratio, 6.0) * 0.9

    margin_boost = 0.0
    if margin_hit:
        financing_buy = safe_float(margin_hit.get("financing_buy_amount")) or 0.0
        financing_balance = safe_float(margin_hit.get("financing_balance")) or 0.0
        if financing_buy >= 300000000:
            margin_boost += 1.3
        elif financing_buy >= 100000000:
            margin_boost += 0.8
        if financing_balance >= 5000000000:
            margin_boost += 0.7
    score += margin_boost
    return {
        "flow_signal_score": round(score, 2),
        "volume_ratio_20d": volume_ratio,
        "amount_ratio_20d": amount_ratio,
        "avg_vol_20d": avg_vol_20d,
        "avg_amount_20d": avg_amount_20d,
        "margin_boost": round(margin_boost, 2),
    }


def event_summary_line(event):
    if not event:
        return "当前还没有在事件库里拿到足够新的公开资讯。"
    payload = event.get("payload") or {}
    title = compact_text(event.get("title"), 60)
    summary = compact_text(payload.get("summary"), 72)
    source_kind = payload.get("source_kind")
    if summary and summary != title:
        return f"{title}。{summary}"
    if source_kind:
        return f"{title}。来源类型：{source_kind}。"
    return title or "当前还没有在事件库里拿到足够新的公开资讯。"


def summarize_reason(item, market):
    parts = []
    pct = safe_float(item.get("pct_chg"))
    if pct is not None:
        parts.append(f"最新日涨跌 {pct:+.2f}%")
    if item.get("volume_ratio_20d") is not None:
        parts.append(f"量能是近20日均值的 {item['volume_ratio_20d']:.2f} 倍")
    if market in {"A", "H"} and item.get("amount_ratio_20d") is not None:
        parts.append(f"成交额是近20日均值的 {item['amount_ratio_20d']:.2f} 倍")
    if item.get("margin_boost"):
        parts.append("两融参与度也在抬升")
    return "，".join(parts) or "当前只看到价格侧有明显异动。"


def build_market_items(conn, market, rows, name_map, pool_types_map, event_map):
    items = []
    for row in rows:
        symbol = row["symbol"] if market == "US" else row["ts_code"]
        recent_rows = load_recent_windows(conn, symbol, market)
        if not recent_rows:
            continue
        event = event_map.get(symbol)
        margin_hit = latest_margin_hit(conn, symbol) if market == "A" else None
        metrics = compute_flow_score(recent_rows[0], recent_rows, market, margin_hit=margin_hit)
        latest_dt = parse_date_value((event or {}).get("publish_time") or (event or {}).get("event_date"))
        item = {
            "market": market,
            "market_label": MARKET_LABELS.get(market, market),
            "symbol": symbol,
            "ts_code": symbol,
            "name": name_map.get(symbol, symbol),
            "trade_date": recent_rows[0].get("trade_date"),
            "close": safe_float(recent_rows[0].get("close")),
            "pct_chg": safe_float(recent_rows[0].get("pct_chg")),
            "vol": safe_float(recent_rows[0].get("vol")),
            "amount": safe_float(recent_rows[0].get("amount")),
            "pool_types": pool_types_map.get(symbol) or [],
            "latest_event_title": (event or {}).get("title"),
            "latest_event_time": (event or {}).get("publish_time") or (event or {}).get("event_date"),
            "latest_event_family": (event or {}).get("event_family"),
            "latest_event_type": (event or {}).get("event_type"),
            "latest_event_rel_path": (event or {}).get("source_rel_path"),
            "latest_event_age_days": None if latest_dt is None else (datetime.now().date() - latest_dt.date()).days,
            "latest_event_importance": (event or {}).get("importance"),
            "news_summary": event_summary_line(event),
            "amount_text": amount_text(recent_rows[0].get("amount"), market),
            **metrics,
        }
        item["reason_summary"] = summarize_reason(item, market)
        items.append(item)

    items.sort(
        key=lambda row: (
            -(row.get("flow_signal_score") or 0.0),
            -(abs(row.get("pct_chg") or 0.0)),
            -(row.get("amount") or row.get("vol") or 0.0),
            row.get("symbol") or "",
        )
    )
    return items[: MARKET_LIMITS.get(market, 10)]


def coverage_summary(conn):
    a_count = conn.execute("SELECT COUNT(DISTINCT ts_code) FROM daily_bar WHERE market='A'").fetchone()[0]
    h_count = conn.execute("SELECT COUNT(DISTINCT ts_code) FROM daily_bar WHERE market='H'").fetchone()[0]
    us_count = conn.execute("SELECT COUNT(DISTINCT symbol) FROM us_daily_bar").fetchone()[0]
    a_trade = conn.execute("SELECT MAX(trade_date) FROM daily_bar WHERE market='A'").fetchone()[0]
    h_trade = conn.execute("SELECT MAX(trade_date) FROM daily_bar WHERE market='H'").fetchone()[0]
    us_trade = conn.execute("SELECT MAX(trade_date) FROM us_daily_bar").fetchone()[0]
    return {
        "scope_label": "当前系统已覆盖库实时扫描",
        "scope_note": "这不是三地交易所全量股票，而是当前已经纳入系统数据库覆盖的 A股 / 港股 / 美股标的集合。",
        "a_share_count": a_count or 0,
        "hk_count": h_count or 0,
        "us_count": us_count or 0,
        "a_share_trade_date": a_trade,
        "hk_trade_date": h_trade,
        "us_trade_date": us_trade,
    }


def overview_lines(payload):
    coverage = payload["coverage_summary"]
    lines = [
        (
            f"本轮先按当前系统已覆盖库扫描：A股 {coverage['a_share_count']} 只，"
            f"港股 {coverage['hk_count']} 只，美股 {coverage['us_count']} 只。"
        ),
    ]
    for market in MARKET_CODE_ORDER:
        items = payload["markets"].get(market) or []
        if not items:
            continue
        top = items[0]
        lines.append(
            f"{MARKET_LABELS.get(market)}当前最强异动是 {top.get('name') or top.get('symbol')}，"
            f"{top.get('reason_summary')}。"
        )
    return lines


def render_market_section(label, items):
    lines = [f"## {label}资金异动", ""]
    if not items:
        lines.extend(["- 当前没有可展示的异动标的。", ""])
        return lines
    lines.extend(
        [
            "| 标的 | 交易日 | 日涨跌 | 量能倍数 | 成交额/成交量 | 异动原因 | 最新资讯 |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in items:
        ratio = item.get("volume_ratio_20d")
        if ratio is None:
            ratio_text = "-"
        else:
            ratio_text = f"{ratio:.2f}x"
        latest_info = compact_text(item.get("news_summary"), 68)
        trade_metric = item.get("amount_text")
        if item.get("market") == "US":
            trade_metric = f"{item.get('vol') or 0:.0f} 股"
        lines.append(
            "| {subject} | {trade_date} | {pct} | {ratio} | {trade_metric} | {reason} | {news} |".format(
                subject=f"{item.get('name') or '-'} / {item.get('symbol') or '-'}",
                trade_date=item.get("trade_date") or "-",
                pct=f"{(item.get('pct_chg') or 0.0):+.2f}%",
                ratio=ratio_text,
                trade_metric=trade_metric or "-",
                reason=compact_text(item.get("reason_summary"), 60),
                news=latest_info or "-",
            )
        )
    lines.append("")
    return lines


def write_markdown(output_path, payload):
    coverage = payload["coverage_summary"]
    lines = [
        "# 全覆盖库资金异动快照",
        "",
        f"- generated_at: {payload.get('generated_at') or '-'}",
        f"- batch_date: {payload.get('batch_date') or '-'}",
        f"- scan_scope: {coverage.get('scope_label') or '-'}",
        f"- scan_note: {coverage.get('scope_note') or '-'}",
        (
            f"- coverage_counts: A股 {coverage.get('a_share_count', 0)} / 港股 {coverage.get('hk_count', 0)} / "
            f"美股 {coverage.get('us_count', 0)}"
        ),
        (
            f"- latest_trade_dates: A股 {coverage.get('a_share_trade_date') or '-'} / "
            f"港股 {coverage.get('hk_trade_date') or '-'} / 美股 {coverage.get('us_trade_date') or '-'}"
        ),
        "",
        "## 核心结论",
        "",
    ]
    for line in payload.get("overview_lines") or []:
        lines.append(f"- {line}")
    if payload.get("blocked_by_data"):
        gate = payload.get("freshness_gate_result") or {}
        lines.extend(["", "## Data Health Gate", ""])
        lines.append(f"- gate_status: `{gate.get('status') or '-'}`")
        for reason in gate.get("reasons") or []:
            lines.append(f"- {reason}")
        output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        return
    lines.append("")
    for market in MARKET_CODE_ORDER:
        lines.extend(render_market_section(MARKET_LABELS.get(market, market), payload["markets"].get(market) or []))
    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    batch_date = generated_at[:10]

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        gate = check_freshness_gate(
            conn,
            module_name="market_signal",
            required_data_types=["daily_bar"],
            allow_degraded=False,
        )
        if gate.status == "block":
            payload = blocked_payload_for_gate("market_signal", gate)
            payload.update(
                {
                    "batch_date": batch_date,
                    "coverage_summary": {
                        "scope_label": "当前系统已覆盖库实时扫描",
                        "scope_note": "行情数据过期，资金异动扫描已阻断。",
                        "a_share_count": 0,
                        "hk_count": 0,
                        "us_count": 0,
                        "a_share_trade_date": None,
                        "hk_trade_date": None,
                        "us_trade_date": None,
                    },
                    "markets": {market: [] for market in MARKET_CODE_ORDER},
                    "freshness_gate_result": gate_to_dict(gate),
                    "data_health_snapshot": gate.data_health_snapshot,
                }
            )
            output_path = OUTPUT_DIR / f"{batch_date}_market_flow_anomaly_snapshot.md"
            write_markdown(output_path, payload)
            registry_entry = register_snapshot(
                conn,
                entity_type="market_flow_anomaly_snapshot",
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
                entity_type="market_flow_anomaly_snapshot",
                entity_id=batch_date,
                data_health_snapshot=gate.data_health_snapshot,
                freshness_gate_result=gate_to_dict(gate),
                output_status="blocked_by_data",
                block_reasons=gate.reasons,
            )
            conn.commit()
            log_run(
                SCRIPT_NAME,
                "success",
                "market flow anomaly blocked by freshness gate",
                {
                    "registry_entry_id": registry_entry["id"],
                    "summary_rel_path": relative_to_project(output_path),
                    "freshness_gate_status": gate.status,
                    "block_reasons": gate.reasons,
                },
            )
            print(f"Market flow anomaly snapshot: {relative_to_project(output_path)}")
            print("  status=blocked_by_data")
            return
        name_map = combined_name_map(conn)
        pool_types_map = load_pool_types(conn)
        event_map = latest_event_by_symbol(conn)
        payload = {
            "generated_at": generated_at,
            "batch_date": batch_date,
            "coverage_summary": coverage_summary(conn),
            "freshness_gate_result": gate_to_dict(gate),
            "data_health_snapshot": gate.data_health_snapshot,
            "markets": {
                "A": build_market_items(conn, "A", load_a_h_rows(conn), name_map, pool_types_map, event_map),
                "H": build_market_items(
                    conn,
                    "H",
                    [row for row in load_a_h_rows(conn) if row.get("market") == "H"],
                    name_map,
                    pool_types_map,
                    event_map,
                ),
                "US": build_market_items(conn, "US", load_us_rows(conn), name_map, pool_types_map, event_map),
            },
        }
        payload["markets"]["A"] = build_market_items(
            conn,
            "A",
            [row for row in load_a_h_rows(conn) if row.get("market") == "A"],
            name_map,
            pool_types_map,
            event_map,
        )
        payload["overview_lines"] = overview_lines(payload)

        output_path = OUTPUT_DIR / f"{batch_date}_market_flow_anomaly_snapshot.md"
        write_markdown(output_path, payload)

        registry_entry = register_snapshot(
            conn,
            entity_type="market_flow_anomaly_snapshot",
            entity_id=batch_date,
            status="generated",
            source=SCRIPT_NAME,
            relationships={"summary_rel_path": relative_to_project(output_path)},
            payload={**payload, "summary_rel_path": relative_to_project(output_path)},
            created_at=generated_at,
        )
        record_agent_run(
            conn,
            agent_or_script=SCRIPT_NAME,
            status="success",
            entity_type="market_flow_anomaly_snapshot",
            entity_id=batch_date,
            data_health_snapshot=gate.data_health_snapshot,
            freshness_gate_result=gate_to_dict(gate),
            output_status="generated",
        )
        conn.commit()
    finally:
        conn.close()

    log_run(
        SCRIPT_NAME,
        "success",
        "market flow anomaly snapshot built",
        {
            "registry_entry_id": registry_entry["id"],
            "summary_rel_path": relative_to_project(output_path),
            "a_share_count": len(payload["markets"].get("A") or []),
            "hk_count": len(payload["markets"].get("H") or []),
            "us_count": len(payload["markets"].get("US") or []),
        },
    )
    print(f"Market flow anomaly snapshot: {relative_to_project(output_path)}")


if __name__ == "__main__":
    main()
