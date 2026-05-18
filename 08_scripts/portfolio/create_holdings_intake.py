#!/usr/bin/env python3
"""Create a holdings intake draft from user-provided names or portfolio registry coverage."""

import argparse
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_paths import env_or_project_path, relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_universe import parse_registry_rows, relation_exists, split_ts_code
from smr_wiki import dumps_json, now_ts

DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")
OUTPUT_DIR = env_or_project_path("SMR_PORTFOLIO_INTAKE_DIR", "04_portfolio", "intake")

NAME_ALIASES = {
    "德科立": "688205.SH",
    "阿里巴巴（港股）": "09988.HK",
    "阿里巴巴(港股)": "09988.HK",
    "阿里巴巴": "09988.HK",
    "阿里巴巴-W": "09988.HK",
    "科瑞技术": "002957.SZ",
    "佰维存储": "688525.SH",
    "新雷能": "300593.SZ",
    "中兴通讯": "000063.SZ",
    "瑞可达": "688800.SH",
    "易点天下": "301171.SZ",
}

REQUIRED_POSITION_FIELDS = [
    "entry_date",
    "entry_price",
    "shares_or_market_value",
    "target_price",
    "stop_loss",
    "thesis",
]


def primary_pool(pool_types):
    pool_priority = ["recommended", "candidate", "watchlist", "portfolio_seed", "seed"]
    for pool_type in pool_priority:
        if pool_type in pool_types:
            return pool_type
    return pool_types[0] if pool_types else None


def build_registry_maps():
    rows = parse_registry_rows()
    registry_by_ts_code = {}
    for row in rows:
        if row["pool_type"] == "us_benchmark":
            continue
        registry_by_ts_code[row["ts_code"]] = row
    return registry_by_ts_code


def resolve_requested_codes(args, registry_by_ts_code):
    if args.ts_code:
        resolved = []
        for ts_code in args.ts_code:
            if ts_code not in resolved:
                resolved.append(ts_code)
        return resolved

    if args.holding_name:
        resolved = []
        for raw_name in args.holding_name:
            ts_code = NAME_ALIASES.get(raw_name)
            if not ts_code:
                raise SystemExit(f"Unmapped holding name: {raw_name}")
            if ts_code not in resolved:
                resolved.append(ts_code)
        return resolved

    resolved = []
    for ts_code, row in registry_by_ts_code.items():
        if row["pool_type"] == "portfolio_seed":
            resolved.append(ts_code)
    if not resolved:
        raise SystemExit("No holdings found in portfolio_holdings_registry.md")
    return sorted(resolved)


def latest_value(conn, query, params):
    row = conn.execute(query, params).fetchone()
    return row[0] if row else None


def current_pool_types(conn, ts_code):
    if not relation_exists(conn, "stock_pool_current"):
        return []
    rows = conn.execute(
        """
        SELECT pool_type
        FROM stock_pool_current
        WHERE ts_code=?
        ORDER BY
            CASE pool_type
                WHEN 'recommended' THEN 5
                WHEN 'candidate' THEN 4
                WHEN 'watchlist' THEN 3
                WHEN 'portfolio_seed' THEN 2
                WHEN 'seed' THEN 1
                ELSE 0
            END DESC,
            datetime(added_date) DESC
        """,
        (ts_code,),
    ).fetchall()
    return [row[0] for row in rows]


def latest_sector(conn, ts_code, fallback_sector):
    if relation_exists(conn, "stock_pool_latest"):
        row = conn.execute(
            """
            SELECT sector
            FROM stock_pool_latest
            WHERE ts_code=?
            ORDER BY
                CASE pool_type
                    WHEN 'recommended' THEN 5
                    WHEN 'candidate' THEN 4
                    WHEN 'watchlist' THEN 3
                    WHEN 'portfolio_seed' THEN 2
                    WHEN 'seed' THEN 1
                    ELSE 0
                END DESC,
                datetime(added_date) DESC
            LIMIT 1
            """,
            (ts_code,),
        ).fetchone()
        if row and row[0]:
            return row[0]
    return fallback_sector


def build_intake_row(conn, ts_code, registry_by_ts_code):
    registry_row = registry_by_ts_code.get(ts_code)
    code, market = split_ts_code(ts_code)
    raw_name = registry_row["name"] if registry_row else ts_code
    pool_types = current_pool_types(conn, ts_code)
    latest_daily_date = latest_value(
        conn,
        "SELECT trade_date FROM daily_bar WHERE ts_code=? ORDER BY trade_date DESC LIMIT 1",
        (ts_code,),
    )
    latest_factor_date = latest_value(
        conn,
        "SELECT trade_date FROM factor_daily WHERE ts_code=? ORDER BY trade_date DESC LIMIT 1",
        (ts_code,),
    )
    factor_count = latest_value(
        conn,
        "SELECT COUNT(*) FROM factor_daily WHERE ts_code=? AND trade_date=?",
        (ts_code, latest_factor_date),
    ) if latest_factor_date else 0
    report_count = latest_value(
        conn,
        """
        SELECT COUNT(*)
        FROM source_manifest
        WHERE source_type='external_source_snapshot'
          AND entity_type='stock'
          AND entity_id=?
        """,
        (ts_code,),
    ) if relation_exists(conn, "source_manifest") else 0

    return {
        "user_input_name": raw_name,
        "ts_code": ts_code,
        "raw_code": code,
        "market": market,
        "sector": latest_sector(conn, ts_code, registry_row["sector"] if registry_row else None),
        "registry_pool_type": registry_row["pool_type"] if registry_row else None,
        "registry_added": registry_row["registry_added"] if registry_row else None,
        "current_pool_types": pool_types,
        "primary_current_pool": primary_pool(pool_types),
        "has_daily_bar": bool(latest_daily_date),
        "latest_daily_bar_trade_date": latest_daily_date,
        "has_factor_daily": bool(latest_factor_date),
        "latest_factor_trade_date": latest_factor_date,
        "latest_factor_count": factor_count,
        "has_external_research_snapshot": bool(report_count),
        "external_research_snapshot_count": report_count or 0,
        "position_exists": bool(
            latest_value(
                conn,
                "SELECT COUNT(*) FROM position WHERE ts_code=? AND status='open'",
                (ts_code,),
            )
        ),
        "missing_position_fields": REQUIRED_POSITION_FIELDS,
    }


def write_markdown(rows, created_at, output_path):
    lines = [
        "# SMR 当前持仓导入草稿",
        "",
        f"- created_at: {created_at}",
        f"- holdings_count: {len(rows)}",
        "- status: draft_only",
        "- note: 本文件只承接持仓名单、证券代码和系统覆盖状态，不直接写正式 position 主表。",
        "",
        "## 导入总览",
        "",
        "| 名称 | ts_code | 市场 | 板块 | 当前池层级 | 行情 | 因子 | 外部研究 | 已有正式持仓 |",
        "|------|---------|------|------|------------|------|------|----------|--------------|",
    ]
    for row in rows:
        lines.append(
            f"| {row['user_input_name']} | {row['ts_code']} | {row['market']} | {row['sector'] or '-'} | "
            f"{row['primary_current_pool'] or '-'} | "
            f"{'yes' if row['has_daily_bar'] else 'no'} | "
            f"{'yes' if row['has_factor_daily'] else 'no'} | "
            f"{row['external_research_snapshot_count']} | "
            f"{'yes' if row['position_exists'] else 'no'} |"
        )

    lines.extend(
        [
            "",
            "## 缺失字段",
            "",
            "- 当前还不能安全写入正式 `position` 主表。",
            "- 每只标的后续至少还需要补：`entry_date`、`entry_price`、`shares_or_market_value`、`target_price`、`stop_loss`、`thesis`。",
            "",
            "## 逐票明细",
            "",
        ]
    )

    for row in rows:
        lines.extend(
            [
                f"### {row['user_input_name']} / {row['ts_code']}",
                "",
                f"- market: {row['market']}",
                f"- sector: {row['sector'] or '-'}",
                f"- registry_pool_type: {row['registry_pool_type'] or '-'}",
                f"- registry_added: {row['registry_added'] or '-'}",
                f"- current_pool_types: {', '.join(row['current_pool_types']) if row['current_pool_types'] else '-'}",
                f"- latest_daily_bar_trade_date: {row['latest_daily_bar_trade_date'] or '-'}",
                f"- latest_factor_trade_date: {row['latest_factor_trade_date'] or '-'}",
                f"- latest_factor_count: {row['latest_factor_count']}",
                f"- external_research_snapshot_count: {row['external_research_snapshot_count']}",
                f"- missing_position_fields: {', '.join(row['missing_position_fields'])}",
                "",
            ]
        )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(rows, created_at, output_path):
    payload = {
        "created_at": created_at,
        "holdings_count": len(rows),
        "status": "draft_only",
        "rows": rows,
    }
    output_path.write_text(dumps_json(payload) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Create SMR holdings intake draft")
    parser.add_argument("--holding-name", action="append", help="User provided holding name; can be repeated")
    parser.add_argument("--ts-code", action="append", help="Explicit ts_code; can be repeated")
    args = parser.parse_args()

    created_at = now_ts()
    created_day = created_at[:10]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    registry_by_ts_code = build_registry_maps()
    requested_codes = resolve_requested_codes(args, registry_by_ts_code)
    rows = [build_intake_row(conn, ts_code, registry_by_ts_code) for ts_code in requested_codes]

    markdown_path = OUTPUT_DIR / f"{created_day}_current_holdings_intake.md"
    json_path = OUTPUT_DIR / f"{created_day}_current_holdings_intake.json"
    write_markdown(rows, created_at, markdown_path)
    write_json(rows, created_at, json_path)

    registry_entry = register_snapshot(
        conn,
        entity_type="portfolio_holdings_intake",
        entity_id=created_day,
        status="draft_created",
        source="create_holdings_intake.py",
        relationships={
            "markdown_rel_path": relative_to_project(markdown_path),
            "json_rel_path": relative_to_project(json_path),
        },
        payload={
            "holdings_count": len(rows),
            "requested_codes": requested_codes,
            "rows": rows,
        },
    )
    conn.commit()
    conn.close()

    log_run(
        "create_holdings_intake.py",
        "success",
        "portfolio holdings intake draft created",
        {
            "entity_id": registry_entry["entity_id"],
            "holdings_count": len(rows),
            "markdown_rel_path": relative_to_project(markdown_path),
            "json_rel_path": relative_to_project(json_path),
        },
    )
    print(f"Holdings intake draft created: {markdown_path}")
    print(f"Holdings intake json: {json_path}")
    print(f"Holdings count: {len(rows)}")


if __name__ == "__main__":
    main()
