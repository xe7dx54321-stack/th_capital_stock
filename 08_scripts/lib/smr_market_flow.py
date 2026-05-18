#!/usr/bin/env python3
"""Shared helpers for SMR market-flow facts such as margin balance and stock connect."""

from datetime import datetime, timedelta
from io import BytesIO

import pandas as pd
import requests

from smr_paths import project_path
from smr_wiki import dumps_json, now_ts

CAPITAL_FLOW_OUTPUT_DIR = project_path("01_data", "capital_flow")
MARGIN_SOURCE_KEY = "margin_balance"
MARGIN_PROVIDER = "exchange_margin"
STOCK_CONNECT_SOURCE_KEY = "stock_connect_flow"
STOCK_CONNECT_PROVIDER = "hkex_connect"

SSE_MARGIN_URL = "https://query.sse.com.cn/marketdata/tradedata/queryMargin.do"
SSE_COMMON_QUERY_URL = "https://query.sse.com.cn/commonSoaQuery.do"
SSE_STOCK_CONNECT_QUERY_URL = "https://query.sse.com.cn/sseQuery/commonSoaQuery.do"
SSE_GGT_QUOTE_URL = "https://query.sse.com.cn/ggt/getQuatationInfo.do"
SZSE_MARGIN_DATA_URL = "https://www.szse.cn/api/report/ShowReport/data"
SZSE_MARGIN_XLSX_URL = "https://www.szse.cn/api/report/ShowReport"
EASTMONEY_KAMT_URL = "https://push2.eastmoney.com/api/qt/kamt/get"
EASTMONEY_KAMT_REFERER = "https://data.eastmoney.com/hsgt/hsgtV2.html"
EASTMONEY_DATACENTER_URL = "https://datacenter-web.eastmoney.com/api/data/v1/get"
EASTMONEY_KAMT_ROUTE_KEYS = {
    "northbound_sh": "hk2sh",
    "southbound_sh": "sh2hk",
    "northbound_sz": "hk2sz",
    "southbound_sz": "sz2hk",
}
EASTMONEY_KAMT_STATUS_LABELS = {
    1: "盘后更新",
    2: "盘后更新",
    3: "实时可用",
    4: "休市",
}

SSE_HEADERS = {
    "Referer": "https://www.sse.com.cn/market/dealingdata/overview/margin/",
    "User-Agent": "Mozilla/5.0",
}

SZSE_HEADERS = {
    "Referer": "https://www.szse.cn/disclosure/margin/margin/index.html",
    "User-Agent": "Mozilla/5.0",
}


def parse_number(value):
    text = str(value or "").strip()
    if not text or text.lower() in {"none", "nan", "null", "-", "--"}:
        return None
    text = text.replace(",", "")
    try:
        return float(text)
    except ValueError:
        return None


def compact_date(value):
    text = str(value or "").strip()
    if not text:
        return ""
    if len(text) == 8 and text.isdigit():
        return text
    text = text.replace("/", "-").replace(".", "-")
    return datetime.strptime(text, "%Y-%m-%d").strftime("%Y%m%d")


def iso_date(value):
    text = compact_date(value)
    if not text:
        return ""
    return f"{text[:4]}-{text[4:6]}-{text[6:]}"


def _payload_rows(payload):
    if not isinstance(payload, dict):
        return []
    rows = payload.get("pageHelp", {}).get("data") or payload.get("result") or []
    return [row for row in (rows or []) if isinstance(row, dict)]


def _first_payload_row(payload):
    rows = _payload_rows(payload)
    return rows[0] if rows else None


def backfill_date_candidates(anchor_date, lookback_days):
    start = datetime.strptime(iso_date(anchor_date), "%Y-%m-%d")
    for offset in range(max(0, lookback_days) + 1):
        yield (start - timedelta(days=offset)).strftime("%Y-%m-%d")


def ts_code_for_exchange(code, exchange):
    raw = str(code or "").strip()
    if not raw:
        return ""
    if raw.isdigit():
        raw = raw.zfill(6)
    suffix = "SH" if str(exchange).upper() == "SSE" else "SZ"
    return f"{raw}.{suffix}"


def hk_ts_code(code):
    raw = str(code or "").strip()
    if not raw:
        return ""
    if raw.isdigit():
        raw = raw.zfill(5)
    return f"{raw}.HK"


def money_yi(value):
    number = parse_number(value)
    if number is None:
        return None
    return number / 100000000


def volume_yi(value):
    number = parse_number(value)
    if number is None:
        return None
    return number / 100000000


def money_wan(value):
    number = parse_number(value)
    if number is None:
        return None
    return number / 10000


def volume_wan(value):
    number = parse_number(value)
    if number is None:
        return None
    return number / 10000


def format_metric(value, digits=2, empty="-"):
    if value is None:
        return empty
    return f"{value:,.{digits}f}"


def _eastmoney_amount_wan_to_yuan(value):
    number = parse_number(value)
    if number is None:
        return None
    return number * 10000


def _eastmoney_amount_million_to_yuan(value):
    number = parse_number(value)
    if number is None:
        return None
    return number * 1000000


def _eastmoney_buy_sell_date(value):
    text = str(value or "").strip()
    if not text or text in {"0", "None", "null"}:
        return None
    return iso_date(text)


def _eastmoney_status_label(value):
    number = parse_number(value)
    if number is None:
        return "未知"
    return EASTMONEY_KAMT_STATUS_LABELS.get(int(number), f"状态{int(number)}")


def fetch_eastmoney_stock_connect_realtime_probe():
    params = {
        "fltt": "2",
        "fields1": "f1,f2,f3,f4",
        "fields2": "f51,f52,f53,f54,f56,f60,f61,f62,f63,f65,f66",
        "ut": "fa5fd1943c7b386f172d6893dbfba10b",
    }
    headers = {
        "Referer": EASTMONEY_KAMT_REFERER,
        "User-Agent": "Mozilla/5.0",
    }
    response = requests.get(EASTMONEY_KAMT_URL, params=params, headers=headers, timeout=20)
    response.raise_for_status()
    payload = response.json()
    raw_data = payload.get("data") or {}
    results = {}
    for route_key, eastmoney_key in EASTMONEY_KAMT_ROUTE_KEYS.items():
        route_payload = raw_data.get(eastmoney_key)
        if not isinstance(route_payload, dict):
            continue
        trade_date = iso_date(route_payload.get("date2"))
        buy_sell_amount_date = _eastmoney_buy_sell_date(route_payload.get("buySellAmtDate"))
        results[route_key] = {
            "route_key": route_key,
            "provider": "eastmoney_kamt",
            "trade_date": trade_date or None,
            "status": int(parse_number(route_payload.get("status")) or 0),
            "status_label": _eastmoney_status_label(route_payload.get("status")),
            "amt_status": int(parse_number(route_payload.get("amtStatus")) or 0),
            "quota_balance": _eastmoney_amount_wan_to_yuan(route_payload.get("dayAmtRemain")),
            "quota_threshold": _eastmoney_amount_wan_to_yuan(route_payload.get("dayAmtThreshold")),
            "net_buy_amount": _eastmoney_amount_wan_to_yuan(route_payload.get("netBuyAmt")),
            "buy_sell_amount": _eastmoney_amount_wan_to_yuan(route_payload.get("buySellAmt")),
            "buy_amount": _eastmoney_amount_wan_to_yuan(route_payload.get("buyAmt")),
            "sell_amount": _eastmoney_amount_wan_to_yuan(route_payload.get("sellAmt")),
            "buy_sell_amount_date": buy_sell_amount_date,
            "trade_date_matches_buy_sell_amount_date": bool(trade_date and buy_sell_amount_date and trade_date == buy_sell_amount_date),
            "payload": {
                "raw": route_payload,
                "request": {"url": EASTMONEY_KAMT_URL, "params": params},
            },
        }
    return results


def _eastmoney_datacenter_request(report_name, filter_text, page_size=10):
    params = {
        "reportName": report_name,
        "columns": "ALL",
        "filter": filter_text,
        "pageNumber": "1",
        "pageSize": str(page_size),
        "sortColumns": "TRADE_DATE",
        "sortTypes": "-1",
        "source": "WEB",
        "client": "WEB",
    }
    headers = {
        "Referer": EASTMONEY_KAMT_REFERER,
        "User-Agent": "Mozilla/5.0",
    }
    response = requests.get(EASTMONEY_DATACENTER_URL, params=params, headers=headers, timeout=20)
    response.raise_for_status()
    payload = response.json()
    rows = ((payload or {}).get("result") or {}).get("data") or []
    return rows, params


def attach_stock_connect_realtime_probe(row, probe_by_route):
    enriched = dict(row or {})
    payload = dict(enriched.get("payload") or {})
    route_key = enriched.get("route_key")
    probe = dict((probe_by_route or {}).get(route_key) or {})
    if probe:
        payload["realtime_probe"] = probe
    if enriched.get("direction") != "northbound":
        payload["buy_sell_display_basis"] = "official"
        enriched["payload"] = payload
        return enriched

    estimate_reason = None
    trade_date = iso_date(enriched.get("trade_date"))
    probe_trade_date = iso_date(probe.get("trade_date")) if probe else None
    probe_buy_sell_amount = parse_number(probe.get("buy_sell_amount")) if probe else None
    probe_net_buy_amount = parse_number(probe.get("net_buy_amount")) if probe else None
    if not probe:
        estimate_reason = "probe_missing"
    elif probe_trade_date != trade_date:
        estimate_reason = "probe_trade_date_mismatch"
    elif probe_buy_sell_amount in (None, 0.0):
        estimate_reason = "probe_missing_total_amount"
    elif probe_net_buy_amount is None:
        estimate_reason = "probe_missing_net_buy_amount"
    else:
        official_total_amount = parse_number(enriched.get("total_amount"))
        estimate_total_amount = official_total_amount if official_total_amount is not None else probe_buy_sell_amount
        estimated_buy_amount = max((estimate_total_amount + probe_net_buy_amount) / 2, 0.0)
        estimated_sell_amount = max((estimate_total_amount - probe_net_buy_amount) / 2, 0.0)
        enriched["buy_amount"] = estimated_buy_amount
        enriched["sell_amount"] = estimated_sell_amount
        payload.update(
            {
                "buy_sell_estimated": True,
                "buy_sell_display_basis": "official_plus_estimate",
                "estimate_source": "eastmoney_kamt",
                "estimate_method": "buy=(official_total+net_buy)/2;sell=(official_total-net_buy)/2",
                "estimate_trade_date_match": True,
                "estimate_total_amount_source": "official_total_amount" if official_total_amount is not None else "eastmoney_buy_sell_amount",
                "estimate_total_amount_raw": probe_buy_sell_amount,
                "estimate_total_amount_used": estimate_total_amount,
                "estimate_total_amount_gap": (
                    None if official_total_amount is None else round(probe_buy_sell_amount - official_total_amount, 2)
                ),
                "estimate_net_buy_amount": probe_net_buy_amount,
            }
        )
    if estimate_reason:
        payload.update(
            {
                "buy_sell_estimated": False,
                "buy_sell_display_basis": "official_missing_buy_sell",
                "estimate_source": "eastmoney_kamt",
                "estimate_trade_date_match": bool(probe_trade_date and probe_trade_date == trade_date),
                "estimate_unavailable_reason": estimate_reason,
            }
        )
    enriched["payload"] = payload
    return enriched


def ensure_margin_tables(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS margin_market_summary (
            trade_date TEXT NOT NULL,
            exchange TEXT NOT NULL,
            exchange_name TEXT NOT NULL,
            source_key TEXT NOT NULL,
            provider TEXT NOT NULL,
            financing_buy_amount REAL,
            financing_repayment_amount REAL,
            financing_balance REAL,
            securities_lending_sell_volume REAL,
            securities_lending_repayment_volume REAL,
            securities_lending_balance_volume REAL,
            securities_lending_balance_amount REAL,
            margin_total_balance REAL,
            payload_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (trade_date, exchange)
        );

        CREATE INDEX IF NOT EXISTS idx_margin_market_summary_exchange_date
        ON margin_market_summary(exchange, trade_date DESC);

        CREATE TABLE IF NOT EXISTS margin_security_detail (
            trade_date TEXT NOT NULL,
            exchange TEXT NOT NULL,
            security_code TEXT NOT NULL,
            ts_code TEXT NOT NULL,
            security_name TEXT,
            source_key TEXT NOT NULL,
            provider TEXT NOT NULL,
            financing_buy_amount REAL,
            financing_repayment_amount REAL,
            financing_balance REAL,
            securities_lending_sell_volume REAL,
            securities_lending_repayment_volume REAL,
            securities_lending_balance_volume REAL,
            securities_lending_balance_amount REAL,
            margin_total_balance REAL,
            payload_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (trade_date, exchange, ts_code)
        );

        CREATE INDEX IF NOT EXISTS idx_margin_security_detail_ts_date
        ON margin_security_detail(ts_code, trade_date DESC);

        CREATE INDEX IF NOT EXISTS idx_margin_security_detail_exchange_date
        ON margin_security_detail(exchange, trade_date DESC, financing_balance DESC);
        """
    )


def ensure_stock_connect_tables(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS stock_connect_market_summary (
            trade_date TEXT NOT NULL,
            route_key TEXT NOT NULL,
            route_name TEXT NOT NULL,
            direction TEXT NOT NULL,
            exchange TEXT NOT NULL,
            currency TEXT NOT NULL,
            buy_amount REAL,
            sell_amount REAL,
            total_amount REAL,
            buy_volume REAL,
            sell_volume REAL,
            total_volume REAL,
            etf_total_amount REAL,
            quota_amount REAL,
            quota_status TEXT,
            source_key TEXT NOT NULL,
            provider TEXT NOT NULL,
            payload_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (trade_date, route_key)
        );

        CREATE INDEX IF NOT EXISTS idx_stock_connect_market_summary_route_date
        ON stock_connect_market_summary(route_key, trade_date DESC);

        CREATE TABLE IF NOT EXISTS stock_connect_security_holding (
            trade_date TEXT NOT NULL,
            route_key TEXT NOT NULL,
            route_name TEXT NOT NULL,
            direction TEXT NOT NULL,
            frequency TEXT NOT NULL,
            security_code TEXT NOT NULL,
            ts_code TEXT NOT NULL,
            security_name TEXT,
            holding_quantity REAL,
            source_key TEXT NOT NULL,
            provider TEXT NOT NULL,
            payload_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (trade_date, route_key, ts_code)
        );

        CREATE INDEX IF NOT EXISTS idx_stock_connect_security_holding_ts_date
        ON stock_connect_security_holding(ts_code, trade_date DESC);

        CREATE INDEX IF NOT EXISTS idx_stock_connect_security_holding_route_date
        ON stock_connect_security_holding(route_key, trade_date DESC, holding_quantity DESC);
        """
    )


def upsert_margin_market_summary(conn, rows):
    ensure_margin_tables(conn)
    timestamp = now_ts()
    for row in rows:
        existing = conn.execute(
            """
            SELECT created_at
            FROM margin_market_summary
            WHERE trade_date=? AND exchange=?
            """,
            (row["trade_date"], row["exchange"]),
        ).fetchone()
        created_at = existing[0] if existing else timestamp
        conn.execute(
            """
            INSERT OR REPLACE INTO margin_market_summary (
                trade_date,
                exchange,
                exchange_name,
                source_key,
                provider,
                financing_buy_amount,
                financing_repayment_amount,
                financing_balance,
                securities_lending_sell_volume,
                securities_lending_repayment_volume,
                securities_lending_balance_volume,
                securities_lending_balance_amount,
                margin_total_balance,
                payload_json,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["trade_date"],
                row["exchange"],
                row["exchange_name"],
                row.get("source_key", MARGIN_SOURCE_KEY),
                row.get("provider", MARGIN_PROVIDER),
                row.get("financing_buy_amount"),
                row.get("financing_repayment_amount"),
                row.get("financing_balance"),
                row.get("securities_lending_sell_volume"),
                row.get("securities_lending_repayment_volume"),
                row.get("securities_lending_balance_volume"),
                row.get("securities_lending_balance_amount"),
                row.get("margin_total_balance"),
                dumps_json(row.get("payload") or {}),
                created_at,
                timestamp,
            ),
        )


def upsert_margin_security_detail(conn, rows):
    ensure_margin_tables(conn)
    timestamp = now_ts()
    for row in rows:
        existing = conn.execute(
            """
            SELECT created_at
            FROM margin_security_detail
            WHERE trade_date=? AND exchange=? AND ts_code=?
            """,
            (row["trade_date"], row["exchange"], row["ts_code"]),
        ).fetchone()
        created_at = existing[0] if existing else timestamp
        conn.execute(
            """
            INSERT OR REPLACE INTO margin_security_detail (
                trade_date,
                exchange,
                security_code,
                ts_code,
                security_name,
                source_key,
                provider,
                financing_buy_amount,
                financing_repayment_amount,
                financing_balance,
                securities_lending_sell_volume,
                securities_lending_repayment_volume,
                securities_lending_balance_volume,
                securities_lending_balance_amount,
                margin_total_balance,
                payload_json,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["trade_date"],
                row["exchange"],
                row["security_code"],
                row["ts_code"],
                row.get("security_name"),
                row.get("source_key", MARGIN_SOURCE_KEY),
                row.get("provider", MARGIN_PROVIDER),
                row.get("financing_buy_amount"),
                row.get("financing_repayment_amount"),
                row.get("financing_balance"),
                row.get("securities_lending_sell_volume"),
                row.get("securities_lending_repayment_volume"),
                row.get("securities_lending_balance_volume"),
                row.get("securities_lending_balance_amount"),
                row.get("margin_total_balance"),
                dumps_json(row.get("payload") or {}),
                created_at,
                timestamp,
            ),
        )


def upsert_stock_connect_market_summary(conn, rows):
    ensure_stock_connect_tables(conn)
    timestamp = now_ts()
    for row in rows:
        existing = conn.execute(
            """
            SELECT created_at
            FROM stock_connect_market_summary
            WHERE trade_date=? AND route_key=?
            """,
            (row["trade_date"], row["route_key"]),
        ).fetchone()
        created_at = existing[0] if existing else timestamp
        conn.execute(
            """
            INSERT OR REPLACE INTO stock_connect_market_summary (
                trade_date,
                route_key,
                route_name,
                direction,
                exchange,
                currency,
                buy_amount,
                sell_amount,
                total_amount,
                buy_volume,
                sell_volume,
                total_volume,
                etf_total_amount,
                quota_amount,
                quota_status,
                source_key,
                provider,
                payload_json,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["trade_date"],
                row["route_key"],
                row["route_name"],
                row["direction"],
                row["exchange"],
                row["currency"],
                row.get("buy_amount"),
                row.get("sell_amount"),
                row.get("total_amount"),
                row.get("buy_volume"),
                row.get("sell_volume"),
                row.get("total_volume"),
                row.get("etf_total_amount"),
                row.get("quota_amount"),
                row.get("quota_status"),
                row.get("source_key", STOCK_CONNECT_SOURCE_KEY),
                row.get("provider", STOCK_CONNECT_PROVIDER),
                dumps_json(row.get("payload") or {}),
                created_at,
                timestamp,
            ),
        )


def upsert_stock_connect_security_holding(conn, rows):
    ensure_stock_connect_tables(conn)
    timestamp = now_ts()
    for row in rows:
        existing = conn.execute(
            """
            SELECT created_at
            FROM stock_connect_security_holding
            WHERE trade_date=? AND route_key=? AND ts_code=?
            """,
            (row["trade_date"], row["route_key"], row["ts_code"]),
        ).fetchone()
        created_at = existing[0] if existing else timestamp
        conn.execute(
            """
            INSERT OR REPLACE INTO stock_connect_security_holding (
                trade_date,
                route_key,
                route_name,
                direction,
                frequency,
                security_code,
                ts_code,
                security_name,
                holding_quantity,
                source_key,
                provider,
                payload_json,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["trade_date"],
                row["route_key"],
                row["route_name"],
                row["direction"],
                row["frequency"],
                row["security_code"],
                row["ts_code"],
                row.get("security_name"),
                row.get("holding_quantity"),
                row.get("source_key", STOCK_CONNECT_SOURCE_KEY),
                row.get("provider", STOCK_CONNECT_PROVIDER),
                dumps_json(row.get("payload") or {}),
                created_at,
                timestamp,
            ),
        )


def _sse_request(params):
    response = requests.get(SSE_MARGIN_URL, params=params, headers=SSE_HEADERS, timeout=20)
    response.raise_for_status()
    return response.json()


def fetch_sse_margin_summary(trade_date):
    compact = compact_date(trade_date)
    params = {
        "isPagination": "true",
        "beginDate": compact,
        "endDate": compact,
        "tabType": "",
        "stockCode": "",
        "pageHelp.pageSize": "5000",
        "pageHelp.pageNo": "1",
        "pageHelp.beginPage": "1",
        "pageHelp.endPage": "1",
    }
    payload = _sse_request(params)
    raw = _first_payload_row(payload)
    if raw is None:
        return None
    financing_balance = parse_number(raw.get("rzye"))
    lending_balance = parse_number(raw.get("rqylje"))
    total_balance = parse_number(raw.get("rzrqjyzl"))
    if total_balance is None and financing_balance is not None and lending_balance is not None:
        total_balance = financing_balance + lending_balance
    return {
        "trade_date": iso_date(raw.get("opDate") or compact),
        "exchange": "SSE",
        "exchange_name": "上交所",
        "source_key": MARGIN_SOURCE_KEY,
        "provider": MARGIN_PROVIDER,
        "financing_buy_amount": parse_number(raw.get("rzmre")),
        "financing_repayment_amount": parse_number(raw.get("rzche")),
        "financing_balance": financing_balance,
        "securities_lending_sell_volume": parse_number(raw.get("rqmcl")),
        "securities_lending_repayment_volume": parse_number(raw.get("rqchl")),
        "securities_lending_balance_volume": parse_number(raw.get("rqyl")),
        "securities_lending_balance_amount": lending_balance,
        "margin_total_balance": total_balance,
        "payload": {
            "exchange": "SSE",
            "request": {"url": SSE_MARGIN_URL, "params": params},
            "raw": raw,
        },
    }


def fetch_sse_margin_detail(trade_date):
    compact = compact_date(trade_date)
    params = {
        "isPagination": "true",
        "tabType": "mxtype",
        "detailsDate": compact,
        "stockCode": "",
        "beginDate": "",
        "endDate": "",
        "pageHelp.pageSize": "5000",
        "pageHelp.pageNo": "1",
        "pageHelp.beginPage": "1",
        "pageHelp.endPage": "1",
    }
    payload = _sse_request(params)
    rows = _payload_rows(payload)
    results = []
    for raw in rows:
        code = str(raw.get("stockCode") or "").strip()
        if not code:
            continue
        financing_balance = parse_number(raw.get("rzye"))
        lending_balance = parse_number(raw.get("rqylje"))
        total_balance = parse_number(raw.get("rzrqjyzl"))
        if total_balance is None and financing_balance is not None and lending_balance is not None:
            total_balance = financing_balance + lending_balance
        results.append(
            {
                "trade_date": iso_date(raw.get("opDate") or compact),
                "exchange": "SSE",
                "security_code": code.zfill(6) if code.isdigit() else code,
                "ts_code": ts_code_for_exchange(code, "SSE"),
                "security_name": str(raw.get("securityAbbr") or "").strip() or None,
                "source_key": MARGIN_SOURCE_KEY,
                "provider": MARGIN_PROVIDER,
                "financing_buy_amount": parse_number(raw.get("rzmre")),
                "financing_repayment_amount": parse_number(raw.get("rzche")),
                "financing_balance": financing_balance,
                "securities_lending_sell_volume": parse_number(raw.get("rqmcl")),
                "securities_lending_repayment_volume": parse_number(raw.get("rqchl")),
                "securities_lending_balance_volume": parse_number(raw.get("rqyl")),
                "securities_lending_balance_amount": lending_balance,
                "margin_total_balance": total_balance,
                "payload": {
                    "exchange": "SSE",
                    "raw": raw,
                },
            }
        )
    return results


def _szse_request_json(trade_date):
    date_text = iso_date(trade_date)
    params = {
        "SHOWTYPE": "JSON",
        "CATALOGID": "1837_xxpl",
        "txtDate": date_text,
        "tab1PAGENO": "1",
        "tab2PAGENO": "1",
        "random": "0.6180339887498948",
    }
    response = requests.get(SZSE_MARGIN_DATA_URL, params=params, headers=SZSE_HEADERS, timeout=20)
    response.raise_for_status()
    return response.json(), params


def fetch_szse_margin_summary(trade_date):
    try:
        payload, params = _szse_request_json(trade_date)
        if not payload or not payload[0].get("data"):
            return None
        raw = payload[0]["data"][0]
        financing_balance = parse_number(raw.get("jrrzye"))
        lending_balance = parse_number(raw.get("jrrjye"))
        total_balance = parse_number(raw.get("jrrzrjye"))
        return {
            "trade_date": iso_date(trade_date),
            "exchange": "SZSE",
            "exchange_name": "深交所",
            "source_key": MARGIN_SOURCE_KEY,
            "provider": MARGIN_PROVIDER,
            "financing_buy_amount": parse_number(raw.get("jrrzmr")) * 100000000 if parse_number(raw.get("jrrzmr")) is not None else None,
            "financing_repayment_amount": None,
            "financing_balance": financing_balance * 100000000 if financing_balance is not None else None,
            "securities_lending_sell_volume": parse_number(raw.get("jrrjmc")) * 100000000 if parse_number(raw.get("jrrjmc")) is not None else None,
            "securities_lending_repayment_volume": None,
            "securities_lending_balance_volume": parse_number(raw.get("jrrjyl")) * 100000000 if parse_number(raw.get("jrrjyl")) is not None else None,
            "securities_lending_balance_amount": lending_balance * 100000000 if lending_balance is not None else None,
            "margin_total_balance": total_balance * 100000000 if total_balance is not None else None,
            "payload": {
                "exchange": "SZSE",
                "request": {"url": SZSE_MARGIN_DATA_URL, "params": params},
                "raw": raw,
            },
        }
    except Exception as error:
        return fetch_akshare_szse_margin_summary(trade_date, fallback_error=error)


def fetch_szse_margin_detail(trade_date):
    try:
        date_text = iso_date(trade_date)
        params = {
            "SHOWTYPE": "xlsx",
            "CATALOGID": "1837_xxpl",
            "txtDate": date_text,
            "tab2PAGENO": "1",
            "random": "0.4142135623730951",
            "TABKEY": "tab2",
        }
        response = requests.get(SZSE_MARGIN_XLSX_URL, params=params, headers=SZSE_HEADERS, timeout=20)
        response.raise_for_status()
        dataframe = pd.read_excel(BytesIO(response.content), engine="openpyxl", dtype=str)
        if dataframe.empty:
            return []
        results = []
        for _, row in dataframe.iterrows():
            code = str(row.get("证券代码") or "").strip()
            if not code:
                continue
            code = code.zfill(6) if code.isdigit() else code
            results.append(
                {
                    "trade_date": date_text,
                    "exchange": "SZSE",
                    "security_code": code,
                    "ts_code": ts_code_for_exchange(code, "SZSE"),
                    "security_name": str(row.get("证券简称") or "").strip() or None,
                    "source_key": MARGIN_SOURCE_KEY,
                    "provider": MARGIN_PROVIDER,
                    "financing_buy_amount": parse_number(row.get("融资买入额(元)")),
                    "financing_repayment_amount": None,
                    "financing_balance": parse_number(row.get("融资余额(元)")),
                    "securities_lending_sell_volume": parse_number(row.get("融券卖出量(股/份)")),
                    "securities_lending_repayment_volume": None,
                    "securities_lending_balance_volume": parse_number(row.get("融券余量(股/份)")),
                    "securities_lending_balance_amount": parse_number(row.get("融券余额(元)")),
                    "margin_total_balance": parse_number(row.get("融资融券余额(元)")),
                    "payload": {
                        "exchange": "SZSE",
                        "raw": {
                            "证券代码": code,
                            "证券简称": row.get("证券简称"),
                            "融资买入额(元)": row.get("融资买入额(元)"),
                            "融资余额(元)": row.get("融资余额(元)"),
                            "融券卖出量(股/份)": row.get("融券卖出量(股/份)"),
                            "融券余量(股/份)": row.get("融券余量(股/份)"),
                            "融券余额(元)": row.get("融券余额(元)"),
                            "融资融券余额(元)": row.get("融资融券余额(元)"),
                        },
                    },
                }
            )
        return results
    except Exception as error:
        return fetch_akshare_szse_margin_detail(trade_date, fallback_error=error)


def fetch_akshare_szse_margin_summary(trade_date, fallback_error=None):
    import akshare as ak

    compact = compact_date(trade_date)
    dataframe = ak.stock_margin_szse(date=compact)
    if dataframe is None or dataframe.empty:
        return None
    raw = dataframe.iloc[0].to_dict()
    return {
        "trade_date": iso_date(compact),
        "exchange": "SZSE",
        "exchange_name": "深交所",
        "source_key": MARGIN_SOURCE_KEY,
        "provider": "akshare_margin",
        "financing_buy_amount": parse_number(raw.get("融资买入额")) * 100000000 if parse_number(raw.get("融资买入额")) is not None else None,
        "financing_repayment_amount": None,
        "financing_balance": parse_number(raw.get("融资余额")) * 100000000 if parse_number(raw.get("融资余额")) is not None else None,
        "securities_lending_sell_volume": parse_number(raw.get("融券卖出量")) * 100000000 if parse_number(raw.get("融券卖出量")) is not None else None,
        "securities_lending_repayment_volume": None,
        "securities_lending_balance_volume": parse_number(raw.get("融券余量")) * 100000000 if parse_number(raw.get("融券余量")) is not None else None,
        "securities_lending_balance_amount": parse_number(raw.get("融券余额")) * 100000000 if parse_number(raw.get("融券余额")) is not None else None,
        "margin_total_balance": parse_number(raw.get("融资融券余额")) * 100000000 if parse_number(raw.get("融资融券余额")) is not None else None,
        "payload": {
            "exchange": "SZSE",
            "fallback_source": "akshare.stock_margin_szse",
            "fallback_reason": repr(fallback_error) if fallback_error else None,
            "raw": raw,
        },
    }


def fetch_akshare_szse_margin_detail(trade_date, fallback_error=None):
    import akshare as ak

    compact = compact_date(trade_date)
    date_text = iso_date(compact)
    dataframe = ak.stock_margin_detail_szse(date=compact)
    if dataframe is None or dataframe.empty:
        return []
    results = []
    for _, row in dataframe.iterrows():
        code = str(row.get("证券代码") or "").strip()
        if not code:
            continue
        code = code.zfill(6) if code.isdigit() else code
        results.append(
            {
                "trade_date": date_text,
                "exchange": "SZSE",
                "security_code": code,
                "ts_code": ts_code_for_exchange(code, "SZSE"),
                "security_name": str(row.get("证券简称") or "").strip() or None,
                "source_key": MARGIN_SOURCE_KEY,
                "provider": "akshare_margin",
                "financing_buy_amount": parse_number(row.get("融资买入额")),
                "financing_repayment_amount": None,
                "financing_balance": parse_number(row.get("融资余额")),
                "securities_lending_sell_volume": parse_number(row.get("融券卖出量")),
                "securities_lending_repayment_volume": None,
                "securities_lending_balance_volume": parse_number(row.get("融券余量")),
                "securities_lending_balance_amount": parse_number(row.get("融券余额")),
                "margin_total_balance": parse_number(row.get("融资融券余额")),
                "payload": {
                    "exchange": "SZSE",
                    "fallback_source": "akshare.stock_margin_detail_szse",
                    "fallback_reason": repr(fallback_error) if fallback_error else None,
                    "raw": {
                        "证券代码": code,
                        "证券简称": row.get("证券简称"),
                        "融资买入额": row.get("融资买入额"),
                        "融资余额": row.get("融资余额"),
                        "融券卖出量": row.get("融券卖出量"),
                        "融券余量": row.get("融券余量"),
                        "融券余额": row.get("融券余额"),
                        "融资融券余额": row.get("融资融券余额"),
                    },
                },
            }
        )
    return results


def resolve_latest_margin_bundle(fetch_summary, fetch_detail, anchor_date, lookback_days):
    for candidate in backfill_date_candidates(anchor_date, lookback_days):
        try:
            summary = fetch_summary(candidate)
            detail = fetch_detail(candidate)
        except Exception:
            continue
        if summary and detail:
            return {
                "trade_date": summary["trade_date"],
                "summary": summary,
                "detail": detail,
            }
    return None


def completed_quarter_candidates(anchor_date, lookback_quarters):
    anchor = datetime.strptime(iso_date(anchor_date), "%Y-%m-%d")
    current_quarter = ((anchor.month - 1) // 3) + 1
    quarter = current_quarter - 1
    year = anchor.year
    if quarter == 0:
        quarter = 4
        year -= 1
    for _ in range(max(1, lookback_quarters)):
        yield f"{year}Q{quarter}"
        quarter -= 1
        if quarter == 0:
            quarter = 4
            year -= 1


def quarter_code_to_date(quarter_code):
    text = str(quarter_code or "").strip().upper()
    if not text or "Q" not in text:
        return ""
    year_text, quarter_text = text.split("Q", 1)
    year = int(year_text)
    quarter = int(quarter_text)
    mapping = {
        1: "03-31",
        2: "06-30",
        3: "09-30",
        4: "12-31",
    }
    return f"{year}-{mapping[quarter]}"


def _parse_amount_yi(value):
    number = parse_number(value)
    if number is None:
        return None
    return number * 100000000


def _parse_volume_wan(value):
    number = parse_number(value)
    if number is None:
        return None
    return number * 10000


def _sse_stock_connect_request(params, referer):
    headers = {
        "Referer": referer,
        "User-Agent": "Mozilla/5.0",
    }
    response = requests.get(SSE_COMMON_QUERY_URL, params=params, headers=headers, timeout=20)
    response.raise_for_status()
    return response.json()


def _sse_stock_connect_ssequery_request(params, referer):
    headers = {
        "Referer": referer,
        "User-Agent": "Mozilla/5.0",
    }
    response = requests.get(SSE_STOCK_CONNECT_QUERY_URL, params=params, headers=headers, timeout=20)
    response.raise_for_status()
    return response.json()


def fetch_sse_northbound_sh_summary(trade_date):
    compact = compact_date(trade_date)
    params = {
        "sqlId": "FW_HGTZL_HGTSCSJ_HGTCJGK_MRTJ",
        "tradeDate": compact,
    }
    payload = _sse_stock_connect_request(params, "https://www.sse.com.cn/services/hkexsc/hgtscsj/hgtcjgk/")
    raw = _first_payload_row(payload)
    if raw is None:
        return None
    return {
        "trade_date": iso_date(raw.get("tradeDate") or compact),
        "route_key": "northbound_sh",
        "route_name": "沪股通",
        "direction": "northbound",
        "exchange": "SSE",
        "currency": "CNY",
        "buy_amount": None,
        "sell_amount": None,
        "total_amount": _parse_amount_yi(raw.get("totalAmount")),
        "buy_volume": None,
        "sell_volume": None,
        "total_volume": _parse_volume_wan(raw.get("totalVolume")),
        "etf_total_amount": _parse_amount_yi(raw.get("etfTotalAmount")),
        "quota_amount": None,
        "quota_status": None,
        "source_key": STOCK_CONNECT_SOURCE_KEY,
        "provider": STOCK_CONNECT_PROVIDER,
        "payload": {"raw": raw, "request": {"url": SSE_COMMON_QUERY_URL, "params": params}},
    }


def fetch_sse_southbound_sh_summary(trade_date):
    compact = compact_date(trade_date)
    headers = {
        "Referer": "https://www.sse.com.cn/services/hkexsc/ggtscsj/ggtcjgk/",
        "User-Agent": "Mozilla/5.0",
    }
    params = {"tradeDate": compact}
    response = requests.get(SSE_GGT_QUOTE_URL, params=params, headers=headers, timeout=20)
    response.raise_for_status()
    payload = response.json()
    raw = _first_payload_row(payload)
    if raw is None:
        return None
    return {
        "trade_date": iso_date(raw.get("TRADE_DATE") or compact),
        "route_key": "southbound_sh",
        "route_name": "港股通(沪)",
        "direction": "southbound",
        "exchange": "SSE",
        "currency": "HKD",
        "buy_amount": _parse_amount_yi(raw.get("BUY_AMOUNT")),
        "sell_amount": _parse_amount_yi(raw.get("SELL_AMOUNT")),
        "total_amount": _parse_amount_yi(raw.get("TOTAL_AMOUNT")),
        "buy_volume": _parse_volume_wan(raw.get("BUY_VOLUME")),
        "sell_volume": _parse_volume_wan(raw.get("SELL_VOLUME")),
        "total_volume": _parse_volume_wan(raw.get("TOTAL_VOLUME")),
        "etf_total_amount": _parse_amount_yi(raw.get("ETF_TOTAL_AMOUNT")),
        "quota_amount": None,
        "quota_status": None,
        "source_key": STOCK_CONNECT_SOURCE_KEY,
        "provider": STOCK_CONNECT_PROVIDER,
        "payload": {"raw": raw, "request": {"url": SSE_GGT_QUOTE_URL, "params": params}},
    }


def _szse_report_json(catalog_id, trade_date, referer):
    params = {
        "SHOWTYPE": "JSON",
        "CATALOGID": catalog_id,
        "txtDate": trade_date,
        "random": "0.2718281828459045",
    }
    headers = {
        "Referer": referer,
        "User-Agent": "Mozilla/5.0",
    }
    response = requests.get(SZSE_MARGIN_DATA_URL, params=params, headers=headers, timeout=20)
    response.raise_for_status()
    return response.json(), params


def _szse_report_xlsx(catalog_id, trade_date, referer):
    params = {
        "SHOWTYPE": "xlsx",
        "CATALOGID": catalog_id,
        "txtDate": trade_date,
        "random": "0.3141592653589793",
    }
    headers = {
        "Referer": referer,
        "User-Agent": "Mozilla/5.0",
    }
    response = requests.get(SZSE_MARGIN_XLSX_URL, params=params, headers=headers, timeout=20)
    response.raise_for_status()
    return pd.read_excel(BytesIO(response.content), engine="openpyxl", header=0, dtype=str), params


def _label_value_map(rows):
    result = {}
    for row in rows or []:
        label = str(row.get("label") or "").strip()
        if not label:
            continue
        for key in ("total", "je", "value"):
            if key in row and str(row.get(key) or "").strip():
                result[label] = row.get(key)
                break
    return result


def _eastmoney_stock_connect_dealamt_row(trade_date):
    date_text = iso_date(trade_date)
    rows, params = _eastmoney_datacenter_request(
        "RPT_MUTUAL_DEALAMT",
        f"(TRADE_DATE='{date_text}')",
        page_size=5,
    )
    raw = rows[0] if rows else None
    return raw, params


def _eastmoney_stock_connect_deal_history_row(trade_date, mutual_type):
    date_text = iso_date(trade_date)
    rows, params = _eastmoney_datacenter_request(
        "RPT_MUTUAL_DEAL_HISTORY",
        f'(MUTUAL_TYPE="{mutual_type}")(TRADE_DATE=\'{date_text}\')',
        page_size=5,
    )
    raw = rows[0] if rows else None
    return raw, params


def fetch_eastmoney_northbound_sz_summary(trade_date, fallback_error=None):
    raw, params = _eastmoney_stock_connect_dealamt_row(trade_date)
    if raw is None:
        return None
    return {
        "trade_date": iso_date(raw.get("TRADE_DATE") or trade_date),
        "route_key": "northbound_sz",
        "route_name": "深股通",
        "direction": "northbound",
        "exchange": "SZSE",
        "currency": "CNY",
        "buy_amount": None,
        "sell_amount": None,
        "total_amount": _eastmoney_amount_million_to_yuan(raw.get("ST_DEAL_AMT")),
        "buy_volume": None,
        "sell_volume": None,
        "total_volume": parse_number(raw.get("ST_DEAL_NUM")),
        "etf_total_amount": None,
        "quota_amount": None,
        "quota_status": raw.get("ST_QUOTA_BALANCE"),
        "source_key": STOCK_CONNECT_SOURCE_KEY,
        "provider": "eastmoney_datacenter",
        "payload": {
            "fallback_source": "eastmoney_datacenter.RPT_MUTUAL_DEALAMT",
            "fallback_reason": repr(fallback_error) if fallback_error else None,
            "raw": raw,
            "request": {"url": EASTMONEY_DATACENTER_URL, "params": params},
        },
    }


def fetch_eastmoney_southbound_sz_summary(trade_date, fallback_error=None):
    market_raw, market_params = _eastmoney_stock_connect_dealamt_row(trade_date)
    history_raw, history_params = _eastmoney_stock_connect_deal_history_row(trade_date, "006")
    if market_raw is None and history_raw is None:
        return None
    trade_date_value = iso_date(
        (history_raw or {}).get("TRADE_DATE") or (market_raw or {}).get("TRADE_DATE") or trade_date
    )
    return {
        "trade_date": trade_date_value,
        "route_key": "southbound_sz",
        "route_name": "港股通(深)",
        "direction": "southbound",
        "exchange": "SZSE",
        "currency": "HKD",
        "buy_amount": _eastmoney_amount_million_to_yuan((history_raw or {}).get("BUY_AMT")),
        "sell_amount": _eastmoney_amount_million_to_yuan((history_raw or {}).get("SELL_AMT")),
        "total_amount": _eastmoney_amount_million_to_yuan(
            (history_raw or {}).get("DEAL_AMT") if history_raw else (market_raw or {}).get("ST_DEAL_AMT")
        ),
        "buy_volume": None,
        "sell_volume": None,
        "total_volume": parse_number((history_raw or {}).get("DEAL_NUM") if history_raw else (market_raw or {}).get("ST_DEAL_NUM")),
        "etf_total_amount": None,
        "quota_amount": None,
        "quota_status": (history_raw or {}).get("QUOTA_BALANCE_TEXT") or (market_raw or {}).get("ST_QUOTA_BALANCE"),
        "source_key": STOCK_CONNECT_SOURCE_KEY,
        "provider": "eastmoney_datacenter",
        "payload": {
            "fallback_source": "eastmoney_datacenter.RPT_MUTUAL_DEALAMT+RPT_MUTUAL_DEAL_HISTORY",
            "fallback_reason": repr(fallback_error) if fallback_error else None,
            "market_raw": market_raw,
            "history_raw": history_raw,
            "market_request": {"url": EASTMONEY_DATACENTER_URL, "params": market_params},
            "history_request": {"url": EASTMONEY_DATACENTER_URL, "params": history_params},
        },
    }


def fetch_szse_northbound_sz_summary(trade_date):
    date_text = iso_date(trade_date)
    try:
        payload, params = _szse_report_json(
            "SGT_SGTJYRB",
            date_text,
            "https://www.szse.cn/szhk/szhktradeinfo/szdaily/index.html",
        )
        if not payload:
            return None
        record = payload[0]
        label_map = _label_value_map(record.get("data"))
        if not label_map:
            return None
        return {
            "trade_date": record.get("metadata", {}).get("subname") or date_text,
            "route_key": "northbound_sz",
            "route_name": "深股通",
            "direction": "northbound",
            "exchange": "SZSE",
            "currency": "CNY",
            "buy_amount": None,
            "sell_amount": None,
            "total_amount": _parse_amount_yi(label_map.get("当日交易总额（亿元人民币）")),
            "buy_volume": None,
            "sell_volume": None,
            "total_volume": _parse_volume_wan(label_map.get("当日交易总笔数（万笔）")),
            "etf_total_amount": _parse_amount_yi(label_map.get("当日ETF交易总额（亿元人民币）")),
            "quota_amount": None,
            "quota_status": None,
            "source_key": STOCK_CONNECT_SOURCE_KEY,
            "provider": STOCK_CONNECT_PROVIDER,
            "payload": {"raw": record, "request": {"url": SZSE_MARGIN_DATA_URL, "params": params}},
        }
    except Exception as error:
        return fetch_eastmoney_northbound_sz_summary(trade_date, fallback_error=error)


def fetch_szse_southbound_sz_summary(trade_date):
    date_text = iso_date(trade_date)
    try:
        payload, params = _szse_report_json(
            "SGT_GGTJYRB",
            date_text,
            "https://www.szse.cn/szhk/szhktradeinfo/hkdaily/index.html",
        )
        if not payload:
            return None
        record = payload[0]
        label_map = _label_value_map(record.get("data"))
        if not label_map:
            return None
        return {
            "trade_date": record.get("metadata", {}).get("subname") or date_text,
            "route_key": "southbound_sz",
            "route_name": "港股通(深)",
            "direction": "southbound",
            "exchange": "SZSE",
            "currency": "HKD",
            "buy_amount": _parse_amount_yi(label_map.get("当日买入交易金额（亿元港币）")),
            "sell_amount": _parse_amount_yi(label_map.get("当日卖出交易金额（亿元港币）")),
            "total_amount": _parse_amount_yi(label_map.get("当日交易总额（亿元港币）")),
            "buy_volume": _parse_volume_wan(label_map.get("当日买入交易笔数（万笔）")),
            "sell_volume": _parse_volume_wan(label_map.get("当日卖出交易笔数（万笔）")),
            "total_volume": _parse_volume_wan(label_map.get("当日交易总笔数（万笔）")),
            "etf_total_amount": _parse_amount_yi(label_map.get("当日ETF交易总额（亿元港币）")),
            "quota_amount": None,
            "quota_status": None,
            "source_key": STOCK_CONNECT_SOURCE_KEY,
            "provider": STOCK_CONNECT_PROVIDER,
            "payload": {"raw": record, "request": {"url": SZSE_MARGIN_DATA_URL, "params": params}},
        }
    except Exception as error:
        return fetch_eastmoney_southbound_sz_summary(trade_date, fallback_error=error)


def fetch_sse_northbound_sh_holdings(quarter_end_date):
    compact = compact_date(quarter_end_date)
    params = {
        "sqlId": "FW_HGTZL_HGTSCSJ_HGTZQCYSL_L",
        "secCodeName": "",
        "tradeDate": compact,
        "isPagination": "true",
        "pageHelp.pageSize": "5000",
        "pageHelp.pageNo": "1",
        "pageHelp.beginPage": "1",
        "pageHelp.endPage": "1",
    }
    payload = _sse_stock_connect_ssequery_request(
        params,
        "https://www.sse.com.cn/services/hkexsc/hgtscsj/hgtzjcysl/",
    )
    rows = _payload_rows(payload)
    results = []
    for raw in rows:
        code = str(raw.get("secCode") or "").strip()
        if not code:
            continue
        results.append(
            {
                "trade_date": iso_date(raw.get("tradeDate") or compact),
                "route_key": "northbound_sh",
                "route_name": "沪股通",
                "direction": "northbound",
                "frequency": "quarterly",
                "security_code": code.zfill(6) if code.isdigit() else code,
                "ts_code": ts_code_for_exchange(code, "SSE"),
                "security_name": str(raw.get("secAbbr") or "").strip() or None,
                "holding_quantity": parse_number(raw.get("totalHoldings")),
                "source_key": STOCK_CONNECT_SOURCE_KEY,
                "provider": STOCK_CONNECT_PROVIDER,
                "payload": {"raw": raw},
            }
        )
    return results


def fetch_sse_southbound_sh_holdings(trade_date):
    compact = compact_date(trade_date)
    params = {
        "sqlId": "FW_HGTZL_GGTSCSJ_GGTZQCYSL",
        "tradeDate": compact,
        "secCodeName": "",
        "isPagination": "true",
        "pageHelp.pageSize": "5000",
        "pageHelp.pageNo": "1",
        "pageHelp.beginPage": "1",
        "pageHelp.endPage": "1",
    }
    payload = _sse_stock_connect_ssequery_request(
        params,
        "https://www.sse.com.cn/services/hkexsc/ggtscsj/ggtzqcysl/",
    )
    rows = _payload_rows(payload)
    results = []
    for raw in rows:
        code = str(raw.get("secCode") or "").strip()
        if not code:
            continue
        results.append(
            {
                "trade_date": iso_date(raw.get("tradeDate") or compact),
                "route_key": "southbound_sh",
                "route_name": "港股通(沪)",
                "direction": "southbound",
                "frequency": "daily",
                "security_code": code.zfill(5) if code.isdigit() else code,
                "ts_code": hk_ts_code(code),
                "security_name": str(raw.get("cnAbbr") or raw.get("enAbbr") or "").strip() or None,
                "holding_quantity": parse_number(raw.get("totalHoldings")),
                "source_key": STOCK_CONNECT_SOURCE_KEY,
                "provider": STOCK_CONNECT_PROVIDER,
                "payload": {"raw": raw},
            }
        )
    return results


def fetch_szse_northbound_sz_holdings(quarter_code):
    dataframe, params = _szse_report_xlsx(
        "SGT_SGTCGSL",
        str(quarter_code or "").strip(),
        "https://www.szse.cn/szhk/szhkshareholding/szholdamount/index.html",
    )
    if dataframe.empty:
        return []
    trade_date = quarter_code_to_date(quarter_code)
    results = []
    for _, row in dataframe.iterrows():
        code = str(row.get("证券代码") or "").strip()
        if not code or code == "证券代码":
            continue
        code = code.zfill(6) if code.isdigit() else code
        results.append(
            {
                "trade_date": trade_date,
                "route_key": "northbound_sz",
                "route_name": "深股通",
                "direction": "northbound",
                "frequency": "quarterly",
                "security_code": code,
                "ts_code": ts_code_for_exchange(code, "SZSE"),
                "security_name": str(row.get("证券简称") or "").strip() or None,
                "holding_quantity": parse_number(row.get("深股通投资者合计持有数量")),
                "source_key": STOCK_CONNECT_SOURCE_KEY,
                "provider": STOCK_CONNECT_PROVIDER,
                "payload": {"request": {"url": SZSE_MARGIN_XLSX_URL, "params": params}},
            }
        )
    return results


def fetch_szse_southbound_sz_holdings(trade_date):
    date_text = iso_date(trade_date)
    dataframe, params = _szse_report_xlsx(
        "SGT_GGTCGSL",
        date_text,
        "https://www.szse.cn/szhk/szhkshareholding/hkholdamount/index.html",
    )
    if dataframe.empty:
        return []
    results = []
    for _, row in dataframe.iterrows():
        code = str(row.get("证券代码") or "").strip()
        if not code or code == "证券代码":
            continue
        code = code.zfill(5) if code.isdigit() else code
        results.append(
            {
                "trade_date": date_text,
                "route_key": "southbound_sz",
                "route_name": "港股通(深)",
                "direction": "southbound",
                "frequency": "daily",
                "security_code": code,
                "ts_code": hk_ts_code(code),
                "security_name": str(row.get("证券简称") or "").strip() or None,
                "holding_quantity": parse_number(row.get("港股通投资者合计持有数量")),
                "source_key": STOCK_CONNECT_SOURCE_KEY,
                "provider": STOCK_CONNECT_PROVIDER,
                "payload": {"request": {"url": SZSE_MARGIN_XLSX_URL, "params": params}},
            }
        )
    return results
