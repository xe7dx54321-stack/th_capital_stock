#!/usr/bin/env python3
"""Capture official stock-connect summaries and available holding snapshots."""

import argparse
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_market_flow import (
    CAPITAL_FLOW_OUTPUT_DIR,
    attach_stock_connect_realtime_probe,
    completed_quarter_candidates,
    ensure_stock_connect_tables,
    fetch_eastmoney_stock_connect_realtime_probe,
    fetch_sse_northbound_sh_holdings,
    fetch_sse_northbound_sh_summary,
    fetch_sse_southbound_sh_holdings,
    fetch_sse_southbound_sh_summary,
    fetch_szse_northbound_sz_holdings,
    fetch_szse_northbound_sz_summary,
    fetch_szse_southbound_sz_holdings,
    fetch_szse_southbound_sz_summary,
    format_metric,
    iso_date,
    money_yi,
    quarter_code_to_date,
    upsert_stock_connect_market_summary,
    upsert_stock_connect_security_holding,
)
from smr_paths import project_path, relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_universe import load_active_equity_universe
from smr_wiki import now_ts

DB_PATH = project_path("01_data", "db", "smr.db")


def active_connect_universe(conn):
    universe = load_active_equity_universe(conn, include_seed=True)
    return {
        ts_code: meta
        for ts_code, meta in universe.items()
        if meta.get("market") in {"SH", "SZ", "HK"}
    }


def resolve_daily_summary(fetcher, anchor_date, lookback_days):
    from smr_market_flow import backfill_date_candidates

    for candidate in backfill_date_candidates(anchor_date, lookback_days):
        try:
            row = fetcher(candidate)
        except Exception:
            continue
        if row:
            return row
    return None


def resolve_daily_holdings(fetcher, anchor_date, lookback_days):
    from smr_market_flow import backfill_date_candidates

    for candidate in backfill_date_candidates(anchor_date, lookback_days):
        try:
            rows = fetcher(candidate)
        except Exception:
            continue
        if rows:
            return {
                "trade_date": rows[0]["trade_date"],
                "rows": rows,
            }
    return None


def resolve_quarterly_holdings(fetcher, anchor_date, lookback_quarters, use_quarter_code=False):
    for quarter_code in completed_quarter_candidates(anchor_date, lookback_quarters):
        argument = quarter_code if use_quarter_code else quarter_code_to_date(quarter_code)
        try:
            rows = fetcher(argument)
        except Exception:
            continue
        if rows:
            return {
                "quarter_code": quarter_code,
                "trade_date": rows[0]["trade_date"],
                "rows": rows,
            }
    return None


def aggregate_universe_holdings(universe, holdings_rows):
    grouped = defaultdict(list)
    for row in holdings_rows:
        grouped[row["ts_code"]].append(row)

    results = []
    for ts_code, meta in sorted(universe.items()):
        rows = grouped.get(ts_code, [])
        if not rows:
            continue
        latest_trade_dates = sorted({row["trade_date"] for row in rows})
        frequencies = sorted({row["frequency"] for row in rows})
        route_names = sorted({row["route_name"] for row in rows})
        total_holding = sum((row.get("holding_quantity") or 0.0) for row in rows)
        results.append(
            {
                "ts_code": ts_code,
                "name": meta.get("name") or ts_code,
                "market": meta.get("market"),
                "sector": meta.get("sector"),
                "pool_types": ",".join(meta.get("source_pool_types") or []),
                "trade_dates": latest_trade_dates,
                "frequencies": frequencies,
                "route_names": route_names,
                "holding_quantity": total_holding,
            }
        )
    results.sort(
        key=lambda row: (
            row["market"] not in {"HK"},
            row.get("holding_quantity") is None,
            -(row.get("holding_quantity") or 0.0),
            row["ts_code"],
        )
    )
    return results


def missing_universe_holdings(universe, holdings_rows):
    seen = {row["ts_code"] for row in holdings_rows}
    missing = []
    for ts_code, meta in sorted(universe.items()):
        if ts_code in seen:
            continue
        missing.append(
            {
                "ts_code": ts_code,
                "name": meta.get("name") or ts_code,
                "market": meta.get("market"),
                "pool_types": ",".join(meta.get("source_pool_types") or []),
                "sector": meta.get("sector"),
            }
        )
    return missing


def render_market_summary(rows):
    lines = [
        "| 路由 | 交易日 | 方向 | 币种 | 买入金额(亿元) | 卖出金额(亿元) | 交易总额(亿元) | 买入笔数(万笔) | 卖出笔数(万笔) | 总笔数(万笔) | ETF交易额(亿元) | 口径 |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        payload = row.get("payload") or {}
        basis = "官方+估算" if payload.get("buy_sell_estimated") else "官方"
        if row.get("direction") == "northbound" and not payload.get("buy_sell_estimated"):
            basis = "官方（买卖拆分未回填）"
        lines.append(
            "| {route_name} | {trade_date} | {direction} | {currency} | {buy_amount} | {sell_amount} | {total_amount} | {buy_volume} | {sell_volume} | {total_volume} | {etf_total_amount} | {basis} |".format(
                route_name=row["route_name"],
                trade_date=row["trade_date"],
                direction="北向" if row["direction"] == "northbound" else "南向",
                currency=row["currency"],
                buy_amount=format_metric(money_yi(row.get("buy_amount"))),
                sell_amount=format_metric(money_yi(row.get("sell_amount"))),
                total_amount=format_metric(money_yi(row.get("total_amount"))),
                buy_volume=format_metric((row.get("buy_volume") or 0.0) / 10000 if row.get("buy_volume") is not None else None),
                sell_volume=format_metric((row.get("sell_volume") or 0.0) / 10000 if row.get("sell_volume") is not None else None),
                total_volume=format_metric((row.get("total_volume") or 0.0) / 10000 if row.get("total_volume") is not None else None),
                etf_total_amount=format_metric(money_yi(row.get("etf_total_amount"))),
                basis=basis,
            )
        )
    return lines


def render_northbound_realtime_probe_rows(probe_by_route, market_rows):
    market_row_map = {row["route_key"]: row for row in market_rows}
    lines = [
        "| 路线 | 实时试探日期 | 当前状态 | 净买额(亿元) | 实时成交额(亿元) | 估算买入额(亿元) | 估算卖出额(亿元) | 回填结果 |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for route_key in ("northbound_sh", "northbound_sz"):
        probe = (probe_by_route or {}).get(route_key) or {}
        market_row = market_row_map.get(route_key) or {}
        payload = market_row.get("payload") or {}
        route_name = market_row.get("route_name") or probe.get("route_key") or route_key
        if payload.get("buy_sell_estimated"):
            refill_result = "已按同日实时净买额反推回填"
        else:
            reason = payload.get("estimate_unavailable_reason")
            if reason == "probe_trade_date_mismatch":
                refill_result = "实时试探日期和事实日不一致，未回填"
            elif reason == "probe_missing_total_amount":
                refill_result = "实时探针未给成交额，未回填"
            elif reason == "probe_missing_net_buy_amount":
                refill_result = "实时探针未给净买额，未回填"
            elif reason == "probe_missing":
                refill_result = "本轮没拿到实时探针"
            else:
                refill_result = "当前未回填"
        lines.append(
            "| {route_name} | {probe_date} | {status_label} | {net_buy_amount} | {buy_sell_amount} | {buy_amount} | {sell_amount} | {refill_result} |".format(
                route_name=route_name,
                probe_date=probe.get("trade_date") or "-",
                status_label=probe.get("status_label") or "-",
                net_buy_amount=format_metric(money_yi(probe.get("net_buy_amount"))),
                buy_sell_amount=format_metric(money_yi(probe.get("buy_sell_amount"))),
                buy_amount=format_metric(money_yi(market_row.get("buy_amount"))),
                sell_amount=format_metric(money_yi(market_row.get("sell_amount"))),
                refill_result=refill_result,
            )
        )
    return lines


def render_universe_holdings(rows):
    lines = [
        "| 标的 | 市场 | 数据日期 | 频率 | 路由 | 官方持有数量(股/份) | pool_types |",
        "| --- | --- | --- | --- | --- | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| {name} / {ts_code} | {market} | {trade_dates} | {frequencies} | {routes} | {holding_quantity} | {pool_types} |".format(
                name=row["name"],
                ts_code=row["ts_code"],
                market=row["market"],
                trade_dates=" / ".join(row["trade_dates"]),
                frequencies=" / ".join(row["frequencies"]),
                routes=" / ".join(row["route_names"]),
                holding_quantity=format_metric(row.get("holding_quantity"), digits=0),
                pool_types=row["pool_types"] or "-",
            )
        )
    return lines


def write_snapshot(
    path,
    created_at,
    anchor_trade_date,
    requested_anchor_trade_date,
    market_rows,
    realtime_probe_by_route,
    holdings_rows,
    universe_hits,
    universe_missing,
):
    lines = [
        "# SMR Stock Connect 快照",
        "",
        f"- created_at: {created_at}",
        f"- anchor_trade_date: {anchor_trade_date}",
        f"- requested_anchor_trade_date: {requested_anchor_trade_date}",
        f"- market_trade_dates: { {row['route_name']: row['trade_date'] for row in market_rows} }",
        f"- holding_trade_dates: {dict(sorted({row['route_name']: row['trade_date'] for row in holdings_rows}.items()))}",
        f"- market_summary_count: {len(market_rows)}",
        f"- holding_row_count: {len(holdings_rows)}",
        f"- holding_counts_by_route: {dict(Counter(row['route_name'] for row in holdings_rows))}",
        f"- active_universe_hit_count: {len(universe_hits)}",
        f"- active_universe_missing_count: {len(universe_missing)}",
        "",
        "## 口径说明",
        "",
        "- 这份快照只写官方 mutual market（互联互通）事实层，不做解释层。",
        "- `anchor_trade_date` 现在表示四条日频成交概况里本轮已抓到的最新事实日期，不再直接沿用行情库参考交易日。",
        "- 四条日频成交概况都来自交易所官方口径：沪股通 / 港股通(沪) 走上交所，深股通 / 港股通(深) 走深交所。",
        "- 北向买入 / 卖出如果能补齐，只会在“实时试探日期”和“官方事实日”一致时，按 `官方总成交额 + 实时净买额` 反推估算；不一致时绝不回填历史事实。",
        "- 官方证券持有数量当前是混合频率：港股通(沪/深) 这里能拿到日频；沪股通 / 深股通当前拿到的是季频口径。",
        "- 所以这份快照里“市场汇总”是日频，“持有数量”是按官方当前可得频率分别落地，不能把二者混成同一频率理解。",
        "- 如果当天部分路由尚未放数，脚本会从请求锚点向前回退，并把日频路线日期和持股日期分别写清楚。",
        "",
        "## 四路日频成交概况",
        "",
        *render_market_summary(market_rows),
        "",
        "## 北向实时试探（单独展示，不等同于官方事实日）",
        "",
        *render_northbound_realtime_probe_rows(realtime_probe_by_route, market_rows),
        "",
        "## 当前股票池官方持有数量命中",
        "",
    ]
    if universe_hits:
        lines.extend(render_universe_holdings(universe_hits))
    else:
        lines.append("- 当前 active universe 没有命中官方可得持有数量。")
    lines.append("")

    lines.extend(["## 当前股票池未命中", ""])
    if universe_missing:
        for row in universe_missing:
            lines.append(
                "- `{ts_code}` {name} | market=`{market}` | sector=`{sector}` | pool_types=`{pool_types}`".format(
                    ts_code=row["ts_code"],
                    name=row["name"],
                    market=row["market"],
                    sector=row.get("sector") or "-",
                    pool_types=row["pool_types"] or "-",
                )
            )
    else:
        lines.append("- 当前 active universe 里的 A/H 标的都命中了官方可得持有数量。")
    lines.append("")

    top_market = sorted(
        market_rows,
        key=lambda row: (row.get("total_amount") is None, -(row.get("total_amount") or 0.0), row["route_key"]),
    )
    lines.extend(["## 今日路由强度排序", ""])
    for row in top_market:
        lines.append(
            "- `{route}` | trade_date=`{trade_date}` | total_amount=`{total_amount} 亿元 {currency}` | total_volume=`{total_volume} 万笔`".format(
                route=row["route_name"],
                trade_date=row["trade_date"],
                total_amount=format_metric(money_yi(row.get("total_amount"))),
                currency=row["currency"],
                total_volume=format_metric((row.get("total_volume") or 0.0) / 10000 if row.get("total_volume") is not None else None),
            )
        )
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Snapshot official stock-connect facts")
    parser.add_argument("--anchor-date", help="Anchor trade date in YYYY-MM-DD or YYYYMMDD format")
    parser.add_argument("--lookback-days", type=int, default=10, help="Backfill window for daily official pages")
    parser.add_argument("--lookback-quarters", type=int, default=8, help="Backfill window for quarterly holding pages")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    ensure_stock_connect_tables(conn)
    requested_anchor_trade_date = iso_date(args.anchor_date) if args.anchor_date else now_ts()[:10]

    market_rows = []
    for fetcher in (
        fetch_sse_northbound_sh_summary,
        fetch_sse_southbound_sh_summary,
        fetch_szse_northbound_sz_summary,
        fetch_szse_southbound_sz_summary,
    ):
        row = resolve_daily_summary(fetcher, requested_anchor_trade_date, args.lookback_days)
        if row:
            market_rows.append(row)
    if not market_rows:
        raise SystemExit("No official stock-connect market summary resolved within lookback window")
    realtime_probe_by_route = fetch_eastmoney_stock_connect_realtime_probe()
    market_rows = [attach_stock_connect_realtime_probe(row, realtime_probe_by_route) for row in market_rows]
    anchor_trade_date = max(iso_date(row["trade_date"]) for row in market_rows if row.get("trade_date"))

    holding_bundles = []
    southbound_sh = resolve_daily_holdings(fetch_sse_southbound_sh_holdings, requested_anchor_trade_date, args.lookback_days)
    if southbound_sh:
        holding_bundles.append(southbound_sh)
    southbound_sz = resolve_daily_holdings(fetch_szse_southbound_sz_holdings, requested_anchor_trade_date, args.lookback_days)
    if southbound_sz:
        holding_bundles.append(southbound_sz)
    northbound_sh = resolve_quarterly_holdings(
        fetch_sse_northbound_sh_holdings,
        requested_anchor_trade_date,
        args.lookback_quarters,
    )
    if northbound_sh:
        holding_bundles.append(northbound_sh)
    northbound_sz = resolve_quarterly_holdings(
        fetch_szse_northbound_sz_holdings,
        requested_anchor_trade_date,
        args.lookback_quarters,
        use_quarter_code=True,
    )
    if northbound_sz:
        holding_bundles.append(northbound_sz)

    holdings_rows = []
    for bundle in holding_bundles:
        holdings_rows.extend(bundle["rows"])

    upsert_stock_connect_market_summary(conn, market_rows)
    if holdings_rows:
        upsert_stock_connect_security_holding(conn, holdings_rows)

    universe = active_connect_universe(conn)
    universe_hits = aggregate_universe_holdings(universe, holdings_rows)
    universe_missing = missing_universe_holdings(universe, holdings_rows)

    created_at = now_ts()
    snapshot_date = created_at[:10]
    CAPITAL_FLOW_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = CAPITAL_FLOW_OUTPUT_DIR / f"{snapshot_date}_stock_connect_flow_snapshot.md"
    write_snapshot(
        output_path,
        created_at=created_at,
        anchor_trade_date=anchor_trade_date,
        requested_anchor_trade_date=requested_anchor_trade_date,
        market_rows=market_rows,
        realtime_probe_by_route=realtime_probe_by_route,
        holdings_rows=holdings_rows,
        universe_hits=universe_hits,
        universe_missing=universe_missing,
    )

    northbound_estimate_summary = []
    for row in market_rows:
        if row.get("direction") != "northbound":
            continue
        payload = row.get("payload") or {}
        probe = payload.get("realtime_probe") or {}
        northbound_estimate_summary.append(
            {
                "route_key": row.get("route_key"),
                "route_name": row.get("route_name"),
                "fact_trade_date": row.get("trade_date"),
                "probe_trade_date": probe.get("trade_date"),
                "probe_status_label": probe.get("status_label"),
                "estimated": bool(payload.get("buy_sell_estimated")),
                "reason": payload.get("estimate_unavailable_reason"),
            }
        )

    payload = {
        "anchor_trade_date": anchor_trade_date,
        "requested_anchor_trade_date": requested_anchor_trade_date,
        "market_trade_dates": {row["route_key"]: row["trade_date"] for row in market_rows},
        "holding_trade_dates": {row["route_key"]: row["trade_date"] for row in holdings_rows},
        "market_summary_count": len(market_rows),
        "holding_row_count": len(holdings_rows),
        "holding_counts_by_route": dict(Counter(row["route_key"] for row in holdings_rows)),
        "active_universe_hit_count": len(universe_hits),
        "active_universe_missing_count": len(universe_missing),
        "route_realtime_probe": realtime_probe_by_route,
        "northbound_estimate_summary": northbound_estimate_summary,
        "summary_rel_path": relative_to_project(output_path),
    }
    entry = register_snapshot(
        conn,
        entity_type="stock_connect_flow_snapshot",
        entity_id=snapshot_date,
        status="captured",
        source="snapshot_stock_connect_flow.py",
        relationships={
            "summary_rel_path": relative_to_project(output_path),
        },
        payload=payload,
    )
    conn.commit()
    conn.close()

    log_run(
        "snapshot_stock_connect_flow.py",
        "success",
        "official stock-connect snapshot captured",
        {
            "anchor_trade_date": anchor_trade_date,
            "requested_anchor_trade_date": requested_anchor_trade_date,
            "market_summary_count": len(market_rows),
            "holding_row_count": len(holdings_rows),
            "active_universe_hit_count": len(universe_hits),
            "summary_rel_path": relative_to_project(output_path),
            "registry_entry_id": entry["id"],
        },
    )
    print(f"Stock connect snapshot registered: {snapshot_date}")
    print(f"Summary file: {output_path}")
    print(f"Market summary rows: {len(market_rows)}")
    print(f"Holding rows: {len(holdings_rows)}")
    print(f"Active universe hits: {len(universe_hits)}")


if __name__ == "__main__":
    main()
