#!/usr/bin/env python3
"""Capture official exchange margin-balance facts into SQLite and Markdown snapshots."""

import argparse
import sqlite3
import sys
from collections import Counter
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_market_flow import (
    CAPITAL_FLOW_OUTPUT_DIR,
    ensure_margin_tables,
    fetch_sse_margin_detail,
    fetch_sse_margin_summary,
    fetch_szse_margin_detail,
    fetch_szse_margin_summary,
    format_metric,
    iso_date,
    money_wan,
    money_yi,
    resolve_latest_margin_bundle,
    upsert_margin_market_summary,
    upsert_margin_security_detail,
    volume_wan,
)
from smr_paths import project_path, relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_universe import load_active_equity_universe
from smr_wiki import now_ts

DB_PATH = project_path("01_data", "db", "smr.db")


def active_margin_universe(conn):
    universe = load_active_equity_universe(conn, include_seed=True)
    return {
        ts_code: meta
        for ts_code, meta in universe.items()
        if meta.get("market") in {"SH", "SZ"}
    }


def annotate_universe(detail_rows, universe):
    hits = []
    detail_map = {row["ts_code"]: row for row in detail_rows}
    for ts_code, meta in sorted(universe.items()):
        row = detail_map.get(ts_code)
        if not row:
            continue
        hits.append(
            {
                "ts_code": ts_code,
                "name": meta.get("name") or row.get("security_name") or ts_code,
                "sector": meta.get("sector"),
                "pool_types": ",".join(meta.get("source_pool_types") or []),
                "exchange": row["exchange"],
                "trade_date": row["trade_date"],
                "financing_buy_amount": row.get("financing_buy_amount"),
                "financing_balance": row.get("financing_balance"),
                "securities_lending_sell_volume": row.get("securities_lending_sell_volume"),
                "securities_lending_balance_volume": row.get("securities_lending_balance_volume"),
                "securities_lending_balance_amount": row.get("securities_lending_balance_amount"),
                "margin_total_balance": row.get("margin_total_balance"),
            }
        )
    hits.sort(
        key=lambda row: (
            row.get("financing_balance") is None,
            -(row.get("financing_balance") or 0.0),
            row["ts_code"],
        )
    )
    return hits


def missing_universe(detail_rows, universe):
    detail_codes = {row["ts_code"] for row in detail_rows}
    missing = []
    for ts_code, meta in sorted(universe.items()):
        if ts_code in detail_codes:
            continue
        missing.append(
            {
                "ts_code": ts_code,
                "name": meta.get("name") or ts_code,
                "sector": meta.get("sector"),
                "pool_types": ",".join(meta.get("source_pool_types") or []),
            }
        )
    return missing


def render_summary_table(summary_rows):
    lines = [
        "| 交易所 | 交易日 | 融资买入额(亿元) | 融资偿还额(亿元) | 融资余额(亿元) | 融券卖出量(亿股/份) | 融券偿还量(亿股/份) | 融券余量(亿股/份) | 融券余额(亿元) | 融资融券余额(亿元) |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary_rows:
        lines.append(
            "| {exchange_name} | {trade_date} | {financing_buy} | {financing_repayment} | {financing_balance} | {lending_sell} | {lending_repayment} | {lending_balance_volume} | {lending_balance_amount} | {margin_total} |".format(
                exchange_name=row["exchange_name"],
                trade_date=row["trade_date"],
                financing_buy=format_metric(money_yi(row.get("financing_buy_amount"))),
                financing_repayment=format_metric(money_yi(row.get("financing_repayment_amount"))),
                financing_balance=format_metric(money_yi(row.get("financing_balance"))),
                lending_sell=format_metric((row.get("securities_lending_sell_volume") or 0.0) / 100000000 if row.get("securities_lending_sell_volume") is not None else None, digits=4),
                lending_repayment=format_metric((row.get("securities_lending_repayment_volume") or 0.0) / 100000000 if row.get("securities_lending_repayment_volume") is not None else None, digits=4),
                lending_balance_volume=format_metric((row.get("securities_lending_balance_volume") or 0.0) / 100000000 if row.get("securities_lending_balance_volume") is not None else None, digits=4),
                lending_balance_amount=format_metric(money_yi(row.get("securities_lending_balance_amount"))),
                margin_total=format_metric(money_yi(row.get("margin_total_balance"))),
            )
        )
    return lines


def render_universe_hits(hits):
    lines = [
        "| 标的 | 交易所 | 交易日 | 融资余额(亿元) | 融资买入额(亿元) | 融券余量(万股/份) | 融券卖出量(万股/份) | 融券余额(万元) | 融资融券余额(亿元) | pool_types |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in hits:
        lines.append(
            "| {name} / {ts_code} | {exchange} | {trade_date} | {financing_balance} | {financing_buy} | {lending_balance_volume} | {lending_sell} | {lending_balance_amount} | {margin_total} | {pool_types} |".format(
                name=row["name"],
                ts_code=row["ts_code"],
                exchange=row["exchange"],
                trade_date=row["trade_date"],
                financing_balance=format_metric(money_yi(row.get("financing_balance"))),
                financing_buy=format_metric(money_yi(row.get("financing_buy_amount"))),
                lending_balance_volume=format_metric(volume_wan(row.get("securities_lending_balance_volume"))),
                lending_sell=format_metric(volume_wan(row.get("securities_lending_sell_volume"))),
                lending_balance_amount=format_metric(money_wan(row.get("securities_lending_balance_amount"))),
                margin_total=format_metric(money_yi(row.get("margin_total_balance"))),
                pool_types=row["pool_types"] or "-",
            )
        )
    return lines


def write_snapshot(
    path,
    created_at,
    anchor_trade_date,
    requested_anchor_trade_date,
    bundles,
    universe_hits,
    universe_missing,
    all_detail_rows,
):
    exchange_summary_rows = [bundle["summary"] for bundle in bundles]
    counts_by_exchange = Counter(row["exchange"] for row in all_detail_rows)
    lines = [
        "# SMR 两融快照",
        "",
        f"- created_at: {created_at}",
        f"- anchor_trade_date: {anchor_trade_date}",
        f"- requested_anchor_trade_date: {requested_anchor_trade_date}",
        f"- exchange_trade_dates: { {bundle['summary']['exchange_name']: bundle['trade_date'] for bundle in bundles} }",
        f"- market_summary_count: {len(exchange_summary_rows)}",
        f"- detail_row_count: {len(all_detail_rows)}",
        f"- counts_by_exchange: {dict(counts_by_exchange)}",
        f"- active_universe_hit_count: {len(universe_hits)}",
        f"- active_universe_missing_count: {len(universe_missing)}",
        "",
        "## 口径说明",
        "",
        "- 这份快照优先记录官方两融事实层，不做解释层判断。",
        "- `anchor_trade_date` 现在表示本轮官方已落地的最新事实日期，不再直接沿用行情库里的参考交易日。",
        "- 上交所与深交所字段口径已统一到元 / 股(份) 后再入库，Markdown 里再换算成亿元 / 万股(份)便于阅读。",
        "- 深交所汇总口径来自官方 JSON，明细口径来自官方 xlsx；上交所汇总和明细都来自官方 `queryMargin.do`。",
        "- 如果某个交易日官方尚未放数，脚本会自动向前回退到最近可用交易日，并在上方显式写出请求锚点和各交易所实际日期。",
        "",
        "## 交易所汇总",
        "",
        *render_summary_table(exchange_summary_rows),
        "",
        "## 当前股票池命中",
        "",
    ]

    if universe_hits:
        lines.extend(render_universe_hits(universe_hits))
    else:
        lines.append("- 当前 active universe 在这轮两融明细里没有命中。")
    lines.append("")

    lines.extend(["## 当前股票池未命中", ""])
    if universe_missing:
        for row in universe_missing:
            lines.append(
                "- `{ts_code}` {name} | sector=`{sector}` | pool_types=`{pool_types}`".format(
                    ts_code=row["ts_code"],
                    name=row["name"],
                    sector=row.get("sector") or "-",
                    pool_types=row["pool_types"] or "-",
                )
            )
    else:
        lines.append("- 当前 active universe 里的 A 股标的都已在两融明细中命中。")
    lines.append("")

    top_financing = sorted(
        all_detail_rows,
        key=lambda row: (row.get("financing_balance") is None, -(row.get("financing_balance") or 0.0), row["ts_code"]),
    )[:10]
    lines.extend(["## 全市场融资余额前十", ""])
    if top_financing:
        for row in top_financing:
            lines.append(
                "- `{ts_code}` {name} | exchange=`{exchange}` | financing_balance=`{financing_balance} 亿元` | financing_buy=`{financing_buy} 亿元`".format(
                    ts_code=row["ts_code"],
                    name=row.get("security_name") or row["ts_code"],
                    exchange=row["exchange"],
                    financing_balance=format_metric(money_yi(row.get("financing_balance"))),
                    financing_buy=format_metric(money_yi(row.get("financing_buy_amount"))),
                )
            )
    else:
        lines.append("- 无可用明细。")
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Snapshot official exchange margin balance facts")
    parser.add_argument("--anchor-date", help="Anchor trade date in YYYY-MM-DD or YYYYMMDD format")
    parser.add_argument("--lookback-days", type=int, default=10, help="Backfill window when latest day has no official data")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    ensure_margin_tables(conn)
    requested_anchor_trade_date = iso_date(args.anchor_date) if args.anchor_date else now_ts()[:10]

    sse_bundle = resolve_latest_margin_bundle(
        fetch_summary=fetch_sse_margin_summary,
        fetch_detail=fetch_sse_margin_detail,
        anchor_date=requested_anchor_trade_date,
        lookback_days=args.lookback_days,
    )
    szse_bundle = resolve_latest_margin_bundle(
        fetch_summary=fetch_szse_margin_summary,
        fetch_detail=fetch_szse_margin_detail,
        anchor_date=requested_anchor_trade_date,
        lookback_days=args.lookback_days,
    )

    bundles = [bundle for bundle in (sse_bundle, szse_bundle) if bundle]
    if not bundles:
        raise SystemExit("No official margin data resolved for any exchange within lookback window")
    anchor_trade_date = max(iso_date(bundle["trade_date"]) for bundle in bundles if bundle.get("trade_date"))

    summary_rows = [bundle["summary"] for bundle in bundles]
    detail_rows = []
    for bundle in bundles:
        detail_rows.extend(bundle["detail"])

    upsert_margin_market_summary(conn, summary_rows)
    upsert_margin_security_detail(conn, detail_rows)

    universe = active_margin_universe(conn)
    universe_hits = annotate_universe(detail_rows, universe)
    universe_missing = missing_universe(detail_rows, universe)

    created_at = now_ts()
    snapshot_date = created_at[:10]
    CAPITAL_FLOW_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = CAPITAL_FLOW_OUTPUT_DIR / f"{snapshot_date}_margin_balance_snapshot.md"
    write_snapshot(
        output_path,
        created_at=created_at,
        anchor_trade_date=anchor_trade_date,
        requested_anchor_trade_date=requested_anchor_trade_date,
        bundles=bundles,
        universe_hits=universe_hits,
        universe_missing=universe_missing,
        all_detail_rows=detail_rows,
    )

    payload = {
        "anchor_trade_date": anchor_trade_date,
        "requested_anchor_trade_date": requested_anchor_trade_date,
        "resolved_trade_dates": {bundle["summary"]["exchange"]: bundle["trade_date"] for bundle in bundles},
        "market_summary_count": len(summary_rows),
        "detail_row_count": len(detail_rows),
        "counts_by_exchange": dict(Counter(row["exchange"] for row in detail_rows)),
        "active_universe_hit_count": len(universe_hits),
        "active_universe_missing_count": len(universe_missing),
        "hit_ts_codes": [row["ts_code"] for row in universe_hits],
        "summary_rel_path": relative_to_project(output_path),
    }
    entry = register_snapshot(
        conn,
        entity_type="margin_balance_snapshot",
        entity_id=snapshot_date,
        status="captured",
        source="snapshot_margin_balance.py",
        relationships={
            "summary_rel_path": relative_to_project(output_path),
        },
        payload=payload,
    )
    conn.commit()
    conn.close()

    log_run(
        "snapshot_margin_balance.py",
        "success",
        "official margin balance snapshot captured",
        {
            "anchor_trade_date": anchor_trade_date,
            "requested_anchor_trade_date": requested_anchor_trade_date,
            "resolved_trade_dates": payload["resolved_trade_dates"],
            "market_summary_count": len(summary_rows),
            "detail_row_count": len(detail_rows),
            "active_universe_hit_count": len(universe_hits),
            "summary_rel_path": relative_to_project(output_path),
            "registry_entry_id": entry["id"],
        },
    )
    print(f"Margin balance snapshot registered: {snapshot_date}")
    print(f"Summary file: {output_path}")
    print(f"Resolved trade dates: {payload['resolved_trade_dates']}")
    print(f"Detail rows: {len(detail_rows)}")
    print(f"Active universe hits: {len(universe_hits)}")


if __name__ == "__main__":
    main()
