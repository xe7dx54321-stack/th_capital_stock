#!/usr/bin/env python3
"""Human-readable digest helpers for capital-flow and event facts."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

CALENDAR_EVENT_TYPES = {
    "board_meeting_notice",
    "annual_results_announcement",
    "interim_results_announcement",
    "quarterly_report",
    "earnings_preannouncement",
    "dividend_notice",
    "equity_movement",
    "monthly_return",
}

UPCOMING_CALENDAR_EVENT_TYPES = {
    "earnings_calendar_item",
    "corp_action_calendar_item",
}

IMPORTANCE_RANK = {
    "high": 3,
    "medium": 2,
    "low": 1,
}

IMPORTANCE_LABELS = {
    "high": "高",
    "medium": "中",
    "low": "低",
}

FREQUENCY_LABELS = {
    "daily": "日频",
    "quarterly": "季频",
}

EXCHANGE_LABELS = {
    "SSE": "上交所",
    "SZSE": "深交所",
}

ROUTE_LABELS = {
    "northbound_sh": "沪股通",
    "northbound_sz": "深股通",
    "southbound_sh": "港股通(沪)",
    "southbound_sz": "港股通(深)",
}

MARGIN_EXCHANGE_ORDER = ["SSE", "SZSE"]
STOCK_CONNECT_ROUTE_ORDER = ["northbound_sh", "northbound_sz", "southbound_sh", "southbound_sz"]

CALENDAR_KIND_LABELS = {
    "earnings_release": "业绩披露",
    "earnings_call": "业绩电话会",
    "conference_presentation": "管理层公开路演",
    "annual_meeting": "股东会",
    "dividend_payable": "分红到账",
}


def safe_float(value):
    if value in (None, "", "None", "nan", "-", "--"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def ordered_unique(values):
    seen = set()
    rows = []
    for value in values:
        if value in (None, ""):
            continue
        if value in seen:
            continue
        seen.add(value)
        rows.append(value)
    return rows


def parse_date_value(value):
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y%m%d"):
        try:
            return datetime.strptime(text[:19], fmt)
        except ValueError:
            continue
    return None


def safe_json_load(value):
    if value in (None, ""):
        return {}
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return {}


def days_since(value, now=None):
    dt = parse_date_value(value)
    if dt is None:
        return None
    anchor = now or datetime.now()
    return (anchor.date() - dt.date()).days


def short_title(value, limit=38):
    text = str(value or "").strip().replace("\n", " ")
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def amount_to_yi(value):
    number = safe_float(value)
    if number is None:
        return None
    return round(number / 100000000, 2)


def compact_quantity(value):
    number = safe_float(value)
    if number is None:
        return "-"
    absolute = abs(number)
    if absolute >= 100000000:
        return f"{number / 100000000:.2f}亿"
    if absolute >= 10000:
        return f"{number / 10000:.2f}万"
    return f"{number:.0f}"


def code_label(value, mapping):
    text = str(value or "").strip()
    if not text:
        return "-"
    return mapping.get(text, text)


def ordered_mapping_items(mapping, preferred_keys=None, label_map=None):
    rows = mapping or {}
    seen = set()
    items = []
    for key in preferred_keys or []:
        if key not in rows:
            continue
        seen.add(key)
        items.append((code_label(key, label_map or {}), rows.get(key)))
    for key in sorted(rows):
        if key in seen:
            continue
        items.append((code_label(key, label_map or {}), rows.get(key)))
    return [(label, value) for label, value in items if value not in (None, "")]


def mapping_dates_text(mapping, preferred_keys=None, label_map=None):
    items = ordered_mapping_items(mapping, preferred_keys=preferred_keys, label_map=label_map)
    if not items:
        return "-"
    return " / ".join(f"{label} {value}" for label, value in items)


def latest_registry_payload(conn, entity_type):
    row = conn.execute(
        """
        SELECT entity_id, status, created_at, payload_json
        FROM task_registry_entity_latest
        WHERE entity_type=?
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """,
        (entity_type,),
    ).fetchone()
    if not row:
        return {}
    return {
        "entity_id": row[0],
        "status": row[1],
        "created_at": row[2],
        "payload": safe_json_load(row[3]),
    }


def build_capital_flow_fact_sheet_from_payloads(margin_payload=None, stock_connect_payload=None):
    margin_payload = margin_payload or {}
    stock_connect_payload = stock_connect_payload or {}

    margin_requested_trade_date = margin_payload.get("requested_anchor_trade_date")
    margin_fact_trade_date = margin_payload.get("anchor_trade_date")
    margin_exchange_dates = margin_payload.get("resolved_trade_dates") or margin_payload.get("exchange_trade_dates") or {}
    margin_exchange_dates_text = mapping_dates_text(
        margin_exchange_dates,
        preferred_keys=MARGIN_EXCHANGE_ORDER,
        label_map=EXCHANGE_LABELS,
    )
    if margin_fact_trade_date:
        if margin_requested_trade_date and margin_requested_trade_date != margin_fact_trade_date:
            margin_summary_line = (
                f"两融今天先按 {margin_requested_trade_date} 实时试探，当前最新事实日是 {margin_fact_trade_date}；"
                f"各交易所实际日期为 {margin_exchange_dates_text}。"
            )
        else:
            margin_summary_line = (
                f"两融今天已拿到 {margin_fact_trade_date} 的官方事实；"
                f"各交易所实际日期为 {margin_exchange_dates_text}。"
            )
    else:
        margin_summary_line = "两融当前还没有拿到可用的官方事实日期。"
    margin_metric_note = (
        f"请求 {margin_requested_trade_date or '-'} / 实际 {margin_exchange_dates_text}"
        if margin_requested_trade_date
        else margin_exchange_dates_text
    )

    stock_requested_trade_date = stock_connect_payload.get("requested_anchor_trade_date")
    stock_fact_trade_date = stock_connect_payload.get("anchor_trade_date")
    stock_market_trade_dates = stock_connect_payload.get("market_trade_dates") or {}
    stock_holding_trade_dates = stock_connect_payload.get("holding_trade_dates") or {}
    stock_market_dates_text = mapping_dates_text(
        stock_market_trade_dates,
        preferred_keys=STOCK_CONNECT_ROUTE_ORDER,
        label_map=ROUTE_LABELS,
    )
    stock_holding_dates_text = mapping_dates_text(
        stock_holding_trade_dates,
        preferred_keys=STOCK_CONNECT_ROUTE_ORDER,
        label_map=ROUTE_LABELS,
    )
    if stock_fact_trade_date:
        if stock_requested_trade_date and stock_requested_trade_date != stock_fact_trade_date:
            stock_summary_line = (
                f"互联互通今天先按 {stock_requested_trade_date} 实时试探，四条日频路线当前最新事实日是 {stock_fact_trade_date}；"
                f"路线实际日期为 {stock_market_dates_text}。"
            )
        else:
            stock_summary_line = (
                f"互联互通四条日频路线今天已更新到 {stock_fact_trade_date}；"
                f"路线实际日期为 {stock_market_dates_text}。"
            )
    else:
        stock_summary_line = "互联互通当前还没有拿到可用的日频路线事实日期。"
    stock_holding_line = (
        f"互联互通持股口径仍按官方可得频率分别展示，当前实际日期为 {stock_holding_dates_text}。"
        if stock_holding_trade_dates
        else "互联互通当前还没有拿到可用的官方持股快照。"
    )
    stock_metric_note = (
        f"日频 {stock_market_dates_text}；持股 {stock_holding_dates_text}"
        if stock_market_trade_dates or stock_holding_trade_dates
        else "当前没有可用的互联互通事实说明。"
    )
    northbound_estimate_summary = stock_connect_payload.get("northbound_estimate_summary") or []
    northbound_probe_dates = ordered_unique(
        row.get("probe_trade_date")
        for row in northbound_estimate_summary
        if row.get("route_key") in {"northbound_sh", "northbound_sz"}
    )
    northbound_estimated_count = sum(1 for row in northbound_estimate_summary if row.get("estimated"))
    stock_probe_line = None
    stock_estimate_line = None
    if northbound_estimate_summary:
        probe_dates_text = " / ".join(northbound_probe_dates) if northbound_probe_dates else "-"
        if northbound_estimated_count > 0:
            stock_probe_line = (
                f"北向实时试探当前也在单独跟踪，最新试探日期为 {probe_dates_text}；"
                f"本轮已有 {northbound_estimated_count} 条路线在试探日期与官方事实日对齐后完成买卖额估算。"
            )
        else:
            stock_probe_line = (
                f"北向实时试探当前也在单独跟踪，最新试探日期为 {probe_dates_text}；"
                "但本轮试探日期和官方事实日没有完全对齐，或实时源没给足净额/成交额，所以没有跨日回填历史买卖额。"
            )
        stock_estimate_line = (
            "北向买入 / 卖出只在同日实时试探和官方事实日对齐时，按官方总成交额 + 实时净买额反推估算；"
            "不对错位日期做跨日补数。"
        )

    return {
        "margin_balance": {
            "requested_trade_date": margin_requested_trade_date,
            "fact_trade_date": margin_fact_trade_date,
            "exchange_trade_dates": margin_exchange_dates,
            "exchange_trade_dates_text": margin_exchange_dates_text,
            "summary_line": margin_summary_line,
            "metric_note": margin_metric_note,
        },
        "stock_connect": {
            "requested_trade_date": stock_requested_trade_date,
            "fact_trade_date": stock_fact_trade_date,
            "market_trade_dates": stock_market_trade_dates,
            "holding_trade_dates": stock_holding_trade_dates,
            "market_trade_dates_text": stock_market_dates_text,
            "holding_trade_dates_text": stock_holding_dates_text,
            "summary_line": stock_summary_line,
            "holding_line": stock_holding_line,
            "probe_line": stock_probe_line,
            "estimate_line": stock_estimate_line,
            "metric_note": stock_metric_note,
        },
        "report_lines": [line for line in [margin_summary_line, stock_summary_line, stock_holding_line, stock_probe_line, stock_estimate_line] if line],
    }


def latest_capital_flow_fact_sheet(conn):
    margin_snapshot = latest_registry_payload(conn, "margin_balance_snapshot")
    stock_connect_snapshot = latest_registry_payload(conn, "stock_connect_flow_snapshot")
    return build_capital_flow_fact_sheet_from_payloads(
        (margin_snapshot.get("payload") or {}),
        (stock_connect_snapshot.get("payload") or {}),
    )
    return f"{number:.0f}"


def importance_rank(value):
    return IMPORTANCE_RANK.get(str(value or "").lower(), 0)


def importance_label(value):
    return IMPORTANCE_LABELS.get(str(value or "").lower(), str(value or "-"))


def frequency_label(value):
    return FREQUENCY_LABELS.get(str(value or "").lower(), str(value or "-"))


def latest_margin_hit(conn, ts_code):
    row = conn.execute(
        """
        WITH ranked AS (
            SELECT
                trade_date,
                exchange,
                COALESCE(security_name, ts_code) AS security_name,
                financing_balance,
                financing_buy_amount,
                margin_total_balance,
                securities_lending_balance_volume,
                ROW_NUMBER() OVER (
                    PARTITION BY ts_code
                    ORDER BY trade_date DESC, updated_at DESC
                ) AS rn
            FROM margin_security_detail
            WHERE ts_code=?
        )
        SELECT
            trade_date,
            exchange,
            security_name,
            financing_balance,
            financing_buy_amount,
            margin_total_balance,
            securities_lending_balance_volume
        FROM ranked
        WHERE rn=1
        LIMIT 1
        """,
        (ts_code,),
    ).fetchone()
    if not row:
        return None
    return {
        "ts_code": ts_code,
        "trade_date": row[0],
        "exchange": row[1],
        "security_name": row[2],
        "financing_balance": safe_float(row[3]),
        "financing_buy_amount": safe_float(row[4]),
        "margin_total_balance": safe_float(row[5]),
        "securities_lending_balance_volume": safe_float(row[6]),
    }


def latest_stock_connect_hits(conn, ts_code):
    rows = conn.execute(
        """
        WITH ranked AS (
            SELECT
                trade_date,
                route_key,
                route_name,
                direction,
                frequency,
                COALESCE(security_name, ts_code) AS security_name,
                holding_quantity,
                ROW_NUMBER() OVER (
                    PARTITION BY ts_code, route_key
                    ORDER BY trade_date DESC, updated_at DESC
                ) AS rn
            FROM stock_connect_security_holding
            WHERE ts_code=?
        )
        SELECT
            trade_date,
            route_key,
            route_name,
            direction,
            frequency,
            security_name,
            holding_quantity
        FROM ranked
        WHERE rn=1
        ORDER BY COALESCE(holding_quantity, 0) DESC, route_key
        """,
        (ts_code,),
    ).fetchall()
    return [
        {
            "ts_code": ts_code,
            "trade_date": row[0],
            "route_key": row[1],
            "route_name": row[2],
            "direction": row[3],
            "frequency": row[4],
            "security_name": row[5],
            "holding_quantity": safe_float(row[6]),
        }
        for row in rows
    ]


def recent_symbol_events(conn, ts_code, days_back=30, limit=6):
    cutoff = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    rows = conn.execute(
        """
        SELECT
            event_date,
            event_family,
            event_type,
            title,
            importance,
            source_key,
            source_rel_path,
            publish_time,
            created_at
        FROM market_event_latest
        WHERE entity_type='stock'
          AND entity_id=?
          AND COALESCE(event_date, substr(COALESCE(publish_time, created_at), 1, 10), '1900-01-01') >= ?
        ORDER BY datetime(COALESCE(publish_time, created_at)) DESC, event_id DESC
        LIMIT ?
        """,
        (ts_code, cutoff, limit),
    ).fetchall()
    return [
        {
            "ts_code": ts_code,
            "event_date": row[0],
            "event_family": row[1],
            "event_type": row[2],
            "title": row[3],
            "importance": row[4],
            "source_key": row[5],
            "source_rel_path": row[6],
            "publish_time": row[7] or row[8],
        }
        for row in rows
    ]


def recent_symbol_calendar_events(conn, ts_code, days_back=60, limit=4):
    placeholders = ",".join("?" for _ in CALENDAR_EVENT_TYPES)
    cutoff = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    rows = conn.execute(
        f"""
        SELECT
            event_date,
            event_family,
            event_type,
            title,
            importance,
            source_key,
            source_rel_path,
            publish_time,
            created_at
        FROM market_event_latest
        WHERE entity_type='stock'
          AND entity_id=?
          AND event_type IN ({placeholders})
          AND COALESCE(event_date, substr(COALESCE(publish_time, created_at), 1, 10), '1900-01-01') >= ?
        ORDER BY datetime(COALESCE(publish_time, created_at)) DESC, event_id DESC
        LIMIT ?
        """,
        (ts_code, *sorted(CALENDAR_EVENT_TYPES), cutoff, limit),
    ).fetchall()
    return [
        {
            "ts_code": ts_code,
            "event_date": row[0],
            "event_family": row[1],
            "event_type": row[2],
            "title": row[3],
            "importance": row[4],
            "source_key": row[5],
            "source_rel_path": row[6],
            "publish_time": row[7] or row[8],
        }
        for row in rows
    ]


def upcoming_symbol_calendar_events(conn, ts_code, days_forward=90, limit=4):
    today = datetime.now().strftime("%Y-%m-%d")
    cutoff = (datetime.now() + timedelta(days=days_forward)).strftime("%Y-%m-%d")
    placeholders = ",".join("?" for _ in UPCOMING_CALENDAR_EVENT_TYPES)
    rows = conn.execute(
        f"""
        SELECT
            event_date,
            event_family,
            event_type,
            title,
            importance,
            source_key,
            source_rel_path,
            publish_time,
            created_at,
            payload_json
        FROM market_event
        WHERE entity_type='stock'
          AND entity_id=?
          AND event_type IN ({placeholders})
          AND COALESCE(event_date, '9999-12-31') >= ?
          AND COALESCE(event_date, '9999-12-31') <= ?
        ORDER BY
            event_date ASC,
            CASE importance
                WHEN 'high' THEN 3
                WHEN 'medium' THEN 2
                ELSE 1
            END DESC,
            datetime(COALESCE(publish_time, created_at)) DESC,
            event_id DESC
        LIMIT ?
        """,
        (ts_code, *sorted(UPCOMING_CALENDAR_EVENT_TYPES), today, cutoff, limit),
    ).fetchall()
    items = []
    for row in rows:
        payload = safe_json_load(row[9])
        items.append(
            {
                "ts_code": ts_code,
                "event_date": row[0],
                "event_family": row[1],
                "event_type": row[2],
                "title": row[3],
                "importance": row[4],
                "source_key": row[5],
                "source_rel_path": row[6],
                "publish_time": row[7] or row[8],
                "calendar_kind": payload.get("calendar_kind"),
                "event_time_text": payload.get("event_time_text"),
                "record_date": payload.get("record_date"),
                "summary": payload.get("summary"),
            }
        )
    return items


def latest_margin_market_summaries(conn):
    rows = conn.execute(
        """
        WITH ranked AS (
            SELECT
                trade_date,
                exchange,
                exchange_name,
                financing_balance,
                margin_total_balance,
                ROW_NUMBER() OVER (
                    PARTITION BY exchange
                    ORDER BY trade_date DESC, updated_at DESC
                ) AS rn
            FROM margin_market_summary
        )
        SELECT
            trade_date,
            exchange,
            exchange_name,
            financing_balance,
            margin_total_balance
        FROM ranked
        WHERE rn=1
        ORDER BY exchange_name
        """
    ).fetchall()
    return [
        {
            "trade_date": row[0],
            "exchange": row[1],
            "exchange_name": row[2],
            "financing_balance": safe_float(row[3]),
            "margin_total_balance": safe_float(row[4]),
        }
        for row in rows
    ]


def latest_stock_connect_market_summaries(conn):
    rows = conn.execute(
        """
        WITH ranked AS (
            SELECT
                trade_date,
                route_key,
                route_name,
                direction,
                currency,
                total_amount,
                buy_amount,
                sell_amount,
                payload_json,
                ROW_NUMBER() OVER (
                    PARTITION BY route_key
                    ORDER BY trade_date DESC, updated_at DESC
                ) AS rn
            FROM stock_connect_market_summary
        )
        SELECT
            trade_date,
            route_key,
            route_name,
            direction,
            currency,
            total_amount,
            buy_amount,
            sell_amount,
            payload_json
        FROM ranked
        WHERE rn=1
        ORDER BY COALESCE(total_amount, 0) DESC, route_key
        """
    ).fetchall()
    items = []
    for row in rows:
        payload = safe_json_load(row[8])
        items.append(
            {
                "trade_date": row[0],
                "route_key": row[1],
                "route_name": row[2],
                "direction": row[3],
                "currency": row[4],
                "total_amount": safe_float(row[5]),
                "buy_amount": safe_float(row[6]),
                "sell_amount": safe_float(row[7]),
                "buy_sell_estimated": bool(payload.get("buy_sell_estimated")),
                "estimate_unavailable_reason": payload.get("estimate_unavailable_reason"),
            }
        )
    return items


def recent_focus_events(conn, ts_codes, days_back=21, limit=8):
    codes = ordered_unique(ts_codes or [])
    if not codes:
        return []
    placeholders = ",".join("?" for _ in codes)
    cutoff = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    rows = conn.execute(
        f"""
        SELECT
            entity_id,
            event_date,
            event_family,
            event_type,
            title,
            importance,
            source_rel_path,
            publish_time,
            created_at
        FROM market_event_latest
        WHERE entity_type='stock'
          AND entity_id IN ({placeholders})
          AND COALESCE(event_date, substr(COALESCE(publish_time, created_at), 1, 10), '1900-01-01') >= ?
        ORDER BY
            CASE importance
                WHEN 'high' THEN 3
                WHEN 'medium' THEN 2
                ELSE 1
            END DESC,
            datetime(COALESCE(publish_time, created_at)) DESC,
            event_id DESC
        LIMIT ?
        """,
        (*codes, cutoff, limit),
    ).fetchall()
    return [
        {
            "ts_code": row[0],
            "event_date": row[1],
            "event_family": row[2],
            "event_type": row[3],
            "title": row[4],
            "importance": row[5],
            "source_rel_path": row[6],
            "publish_time": row[7] or row[8],
        }
        for row in rows
    ]


def calendar_kind_label(value):
    return CALENDAR_KIND_LABELS.get(str(value or "").lower(), str(value or "日历事件"))


def summarize_upcoming_event(event):
    if not event:
        return None
    event_date = event.get("event_date") or "-"
    kind_text = calendar_kind_label(event.get("calendar_kind"))
    title = short_title(event.get("title"))
    record_date = event.get("record_date")
    event_time_text = event.get("event_time_text")
    if record_date:
        return f"接下来最近的明确催化是 {event_date} 的{kind_text}，登记日是 {record_date}。"
    if event_time_text:
        return f"接下来最近的明确催化是 {event_date} 的{kind_text}，时间提示是 {event_time_text}。"
    if title and title not in {"Webcast", "-"}:
        return f"接下来最近的明确催化是 {event_date} 的{kind_text}，对应材料是“{title}”。"
    return f"接下来最近的明确催化是 {event_date} 的{kind_text}。"


def summarize_margin_balance(hit):
    if not hit:
        return {
            "available": False,
            "attention_label": "missing",
            "summary": "当前没有命中官方两融明细。",
        }

    financing_balance_yi = amount_to_yi(hit.get("financing_balance"))
    financing_buy_yi = amount_to_yi(hit.get("financing_buy_amount"))
    margin_total_balance_yi = amount_to_yi(hit.get("margin_total_balance"))

    attention_label = "low"
    if (financing_balance_yi or 0) >= 80 or (financing_buy_yi or 0) >= 8:
        attention_label = "high"
    elif (financing_balance_yi or 0) >= 20 or (financing_buy_yi or 0) >= 2:
        attention_label = "medium"

    if attention_label == "high":
        summary = (
            f"两融参与度偏高，最新融资余额约 {financing_balance_yi or 0:.2f} 亿元，"
            f"单日融资买入约 {financing_buy_yi or 0:.2f} 亿元，对应官方事实日 {hit.get('trade_date') or '-'}。"
        )
    elif attention_label == "medium":
        summary = (
            f"两融参与度中等，最新融资余额约 {financing_balance_yi or 0:.2f} 亿元，"
            f"可以继续盯资金是否继续放大，对应官方事实日 {hit.get('trade_date') or '-'}。"
        )
    else:
        summary = f"两融口径有跟踪，最新融资余额约 {financing_balance_yi or 0:.2f} 亿元，对应官方事实日 {hit.get('trade_date') or '-'}。"

    return {
        "available": True,
        "trade_date": hit.get("trade_date"),
        "exchange": hit.get("exchange"),
        "security_name": hit.get("security_name"),
        "financing_balance": hit.get("financing_balance"),
        "financing_buy_amount": hit.get("financing_buy_amount"),
        "margin_total_balance": hit.get("margin_total_balance"),
        "securities_lending_balance_volume": hit.get("securities_lending_balance_volume"),
        "financing_balance_yi": financing_balance_yi,
        "financing_buy_amount_yi": financing_buy_yi,
        "margin_total_balance_yi": margin_total_balance_yi,
        "attention_label": attention_label,
        "summary": summary,
    }


def summarize_stock_connect(hits):
    if not hits:
        return {
            "available": False,
            "freshness_label": "missing",
            "summary": "当前没有命中官方互联互通持有数量。",
        }

    latest_trade_date = max((row.get("trade_date") or "") for row in hits)
    frequencies = ordered_unique(row.get("frequency") for row in hits)
    route_names = ordered_unique(row.get("route_name") for row in hits)
    total_holding_quantity = sum((row.get("holding_quantity") or 0.0) for row in hits)
    latest_age_days = days_since(latest_trade_date)

    freshness_label = "fresh"
    if latest_age_days is None:
        freshness_label = "unknown"
    elif latest_age_days > 20:
        freshness_label = "stale"
    elif latest_age_days > 7:
        freshness_label = "usable"

    frequency_text = "/".join(frequency_label(value) for value in frequencies) if frequencies else "-"
    routes_text = " / ".join(route_names) if route_names else "-"
    grouped_dates = {}
    for row in hits:
        frequency = row.get("frequency") or "unknown"
        grouped_dates.setdefault(frequency, {})
        grouped_dates[frequency][row.get("route_name") or row.get("route_key") or "-"] = row.get("trade_date")
    daily_dates_text = mapping_dates_text(grouped_dates.get("daily") or {})
    quarterly_dates_text = mapping_dates_text(grouped_dates.get("quarterly") or {})
    if "daily" in frequencies and "quarterly" in frequencies:
        summary = (
            f"互联互通持股口径当前还是混合频率：日频路线最新是 {daily_dates_text}，"
            f"合计约 {compact_quantity(total_holding_quantity)}股/份；"
            f"沪深北向这部分仍有季频口径，最新是 {quarterly_dates_text}。"
        )
    elif "daily" in frequencies:
        summary = (
            f"互联互通日频持股有跟踪，最新事实日是 {latest_trade_date}，"
            f"合计约 {compact_quantity(total_holding_quantity)}股/份，来自 {routes_text}。"
        )
    else:
        summary = (
            f"互联互通当前更多是 {frequency_text} 快照，最近一次 {latest_trade_date} 官方持有数量约 "
            f"{compact_quantity(total_holding_quantity)}股/份，不能把它直接当日内资金表态。"
        )

    return {
        "available": True,
        "latest_trade_date": latest_trade_date,
        "frequencies": frequencies,
        "route_names": route_names,
        "holding_quantity": total_holding_quantity,
        "holding_quantity_display": compact_quantity(total_holding_quantity),
        "freshness_label": freshness_label,
        "summary": summary,
        "items": hits,
    }


def summarize_events(events, calendar_events, upcoming_events):
    if upcoming_events:
        upcoming = upcoming_events[0]
        upcoming_summary = summarize_upcoming_event(upcoming) or "接下来有明确催化日历。"
        days_to_event = days_since(upcoming.get("event_date"))
        signal_label = "watch"
        signal_score = 1.1
        if days_to_event is not None:
            days_until = -days_to_event
            if days_until <= 7:
                signal_label = "high"
                signal_score = 1.8
            elif days_until <= 21:
                signal_label = "active"
                signal_score = 1.4
        summary = upcoming_summary
        if events:
            latest_event = events[0]
            headline = short_title(latest_event.get("title"))
            summary += f" 最近还出现了“{headline}”这类跟踪线索。"
        return {
            "summary": summary,
            "signal_label": signal_label,
            "signal_score": round(signal_score, 2),
        }

    if not events:
        return {
            "summary": "最近没有抓到新的事件信号。",
            "signal_label": "quiet",
            "signal_score": 0.0,
        }

    latest_event = events[0]
    high_events = [item for item in events if item.get("importance") == "high"]
    recent_event_days = days_since(latest_event.get("event_date") or latest_event.get("publish_time"))
    latest_family = latest_event.get("event_family")

    signal_label = "watch"
    signal_score = 0.6
    if high_events:
        signal_label = "high"
        signal_score = 1.5
        headline = short_title(high_events[0].get("title"))
        summary = f"最近有高重要性事件，最新重点是 {high_events[0].get('event_date') or '-'} 的“{headline}”。"
    elif recent_event_days is not None and recent_event_days <= 7:
        signal_label = "active"
        signal_score = 1.0
        headline = short_title(latest_event.get("title"))
        summary = f"最近事件密度不低，最新是 {latest_event.get('event_date') or '-'} 的“{headline}”。"
    elif latest_family == "news":
        headline = short_title(latest_event.get("title"))
        summary = f"最近更多是新闻和二手解读，最新线索是“{headline}”，硬公告还不算多。"
    else:
        headline = short_title(latest_event.get("title"))
        summary = f"最近有持续跟踪，最新线索是“{headline}”。"

    if calendar_events:
        calendar = calendar_events[0]
        summary += (
            f" 日历侧最近还出现了 {calendar.get('event_date') or '-'} 的"
            f"{calendar.get('event_type') or '-'}。"
        )
        signal_score += 0.3

    return {
        "summary": summary,
        "signal_label": signal_label,
        "signal_score": round(signal_score, 2),
    }


def build_symbol_flow_event_digest(conn, ts_code):
    margin_hit = latest_margin_hit(conn, ts_code)
    stock_connect_hits = latest_stock_connect_hits(conn, ts_code)
    events = recent_symbol_events(conn, ts_code)
    calendar_events = recent_symbol_calendar_events(conn, ts_code)
    upcoming_events = upcoming_symbol_calendar_events(conn, ts_code)

    margin_summary = summarize_margin_balance(margin_hit)
    stock_connect_summary = summarize_stock_connect(stock_connect_hits)
    event_summary = summarize_events(events, calendar_events, upcoming_events)

    capital_flow_lines = []
    capital_flow_score = 0.0
    if margin_summary.get("available"):
        capital_flow_lines.append(margin_summary.get("summary"))
        capital_flow_score += {"high": 1.3, "medium": 0.8, "low": 0.4}.get(
            margin_summary.get("attention_label"), 0.0
        )
    if stock_connect_summary.get("available"):
        capital_flow_lines.append(stock_connect_summary.get("summary"))
        capital_flow_score += {"fresh": 0.8, "usable": 0.5, "stale": 0.2}.get(
            stock_connect_summary.get("freshness_label"), 0.0
        )

    watchpoints = []
    if margin_summary.get("attention_label") == "high":
        watchpoints.append("这只票的两融参与度偏高，后续波动可能会被杠杆资金放大。")
    if stock_connect_summary.get("available") and "quarterly" in set(stock_connect_summary.get("frequencies") or []):
        watchpoints.append("互联互通持仓这里主要还是季频快照，不能把它直接当成日内资金表态。")
    if event_summary.get("signal_label") == "high":
        watchpoints.append("最近出现了高重要性事件，最好回到原始公告或材料核对。")
    elif event_summary.get("signal_label") == "watch":
        watchpoints.append("最近事件更多是常规跟踪，先分清楚是硬催化还是噪音。")
    if upcoming_events:
        next_event = upcoming_events[0]
        event_date = next_event.get("event_date")
        if event_date:
            dt = parse_date_value(event_date)
            if dt is not None:
                days_until = (dt.date() - datetime.now().date()).days
                if days_until <= 14:
                    watchpoints.append(f"这只票在未来 {days_until} 天内有明确催化，最好提前安排一次原文复核。")

    return {
        "ts_code": ts_code,
        "margin_balance": margin_summary,
        "stock_connect": stock_connect_summary,
        "stock_connect_hits": stock_connect_hits,
        "recent_events": events,
        "event_calendar": calendar_events,
        "upcoming_event_calendar": upcoming_events,
        "capital_flow_summary": " ".join(capital_flow_lines).strip() or "当前缺少更强的官方资金流跟踪。",
        "event_summary": event_summary.get("summary"),
        "capital_flow_signal_score": round(capital_flow_score, 2),
        "event_signal_score": event_summary.get("signal_score") or 0.0,
        "watchpoints": ordered_unique(watchpoints),
    }


def build_market_context_digest(conn, focus_items=None):
    focus_items = focus_items or []
    focus_pairs = []
    for item in focus_items:
        ts_code = item.get("ts_code")
        if not ts_code:
            continue
        focus_pairs.append((ts_code, item.get("name") or ts_code))

    margin_market = latest_margin_market_summaries(conn)
    connect_market = latest_stock_connect_market_summaries(conn)
    focus_digests = []
    for ts_code, name in ordered_unique(focus_pairs):
        digest = build_symbol_flow_event_digest(conn, ts_code)
        digest["name"] = name
        focus_digests.append(digest)

    capital_flow_fact_sheet = latest_capital_flow_fact_sheet(conn)
    capital_flow_lines = list(capital_flow_fact_sheet.get("report_lines") or [])
    if margin_market:
        parts = []
        latest_margin_fact_date = max((row.get("trade_date") or "") for row in margin_market)
        for row in margin_market:
            total_balance_yi = amount_to_yi(row.get("margin_total_balance"))
            if total_balance_yi is None:
                continue
            parts.append(f"{row.get('exchange_name')}{total_balance_yi:.2f} 亿元")
        if parts:
            capital_flow_lines.append(
                f"全市场两融余额口径仍高，最新事实日 {latest_margin_fact_date or '-'}，大盘面上大致是 {' / '.join(parts)}。"
            )

    northbound = [row for row in connect_market if row.get("direction") == "northbound"]
    southbound = [row for row in connect_market if row.get("direction") == "southbound"]
    if northbound:
        pieces = []
        northbound_fact_date = max((row.get("trade_date") or "") for row in northbound)
        for row in northbound[:2]:
            total_amount_yi = amount_to_yi(row.get("total_amount"))
            if total_amount_yi is None:
                continue
            pieces.append(f"{row.get('route_name')}{total_amount_yi:.2f} 亿元")
        if pieces:
            capital_flow_lines.append(
                f"北向成交仍活跃，最新事实日 {northbound_fact_date or '-'}，大致是 {' / '.join(pieces)}。"
            )
        if not any(row.get("buy_sell_estimated") for row in northbound):
            capital_flow_lines.append(
                "北向买卖额拆分当前仍按“同日实时试探才回填”的口径处理；如果实时探针日期和事实日错位，就只展示试探结果，不跨日反推。"
            )
    if southbound:
        pieces = []
        southbound_fact_date = max((row.get("trade_date") or "") for row in southbound)
        for row in southbound[:2]:
            total_amount_yi = amount_to_yi(row.get("total_amount"))
            if total_amount_yi is None:
                continue
            currency = "港元" if row.get("currency") == "HKD" else (row.get("currency") or "")
            pieces.append(f"{row.get('route_name')}{total_amount_yi:.2f} 亿{currency}")
        if pieces:
            capital_flow_lines.append(
                f"南向成交维持活跃，最新事实日 {southbound_fact_date or '-'}，大致是 {' / '.join(pieces)}。"
            )

    for digest in sorted(focus_digests, key=lambda item: -item.get("capital_flow_signal_score", 0))[:2]:
        if digest.get("capital_flow_signal_score", 0) <= 0:
            continue
        capital_flow_lines.append(f"{digest.get('name') or digest.get('ts_code')}：{digest.get('capital_flow_summary')}")

    event_lines = []
    upcoming_focus = [
        digest
        for digest in focus_digests
        if (digest.get("upcoming_event_calendar") or [])
    ]
    upcoming_focus.sort(
        key=lambda item: (
            ((item.get("upcoming_event_calendar") or [{}])[0].get("event_date") or "9999-12-31"),
            -(item.get("event_signal_score") or 0),
        )
    )
    for digest in upcoming_focus[:3]:
        event_lines.append(f"{digest.get('name') or digest.get('ts_code')}：{digest.get('event_summary')}")

    if not event_lines:
        focus_events = recent_focus_events(conn, [item[0] for item in focus_pairs])
        seen_codes = set()
        for event in focus_events:
            ts_code = event.get("ts_code")
            if ts_code in seen_codes:
                continue
            seen_codes.add(ts_code)
            name = next((pair[1] for pair in focus_pairs if pair[0] == ts_code), ts_code)
            title = short_title(event.get("title"))
            event_lines.append(
                f"{name}：{event.get('event_date') or '-'} 出现{importance_label(event.get('importance'))}重要性事件，“{title}”。"
            )
            if len(event_lines) >= 3:
                break

    if not event_lines:
        for digest in sorted(focus_digests, key=lambda item: -item.get("event_signal_score", 0))[:3]:
            if (digest.get("event_signal_score") or 0) <= 0:
                continue
            event_lines.append(f"{digest.get('name') or digest.get('ts_code')}：{digest.get('event_summary')}")

    return {
        "capital_flow_lines": ordered_unique(capital_flow_lines)[:6],
        "capital_flow_fact_sheet": capital_flow_fact_sheet,
        "event_lines": ordered_unique(event_lines)[:4],
        "focus_symbol_digests": focus_digests,
        "margin_market": margin_market,
        "stock_connect_market": connect_market,
    }
