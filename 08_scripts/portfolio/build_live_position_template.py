#!/usr/bin/env python3
"""Build a fillable live-position intake template from the latest holdings intake draft."""

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_paths import env_or_project_path, normalize_project_path, relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run

DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")
INTAKE_DIR = env_or_project_path("SMR_PORTFOLIO_INTAKE_DIR", "04_portfolio", "intake")

REQUIRED_FIELDS = [
    "entry_date",
    "entry_price",
    "size_input_type",
    "size_input_value",
    "target_price",
    "stop_loss",
    "thesis",
]


def find_latest_holdings_intake():
    candidates = [path for path in INTAKE_DIR.glob("*_current_holdings_intake.json") if path.is_file()]
    if not candidates:
        raise SystemExit("No current holdings intake json found. Run create_holdings_intake.py first.")
    return sorted(candidates, key=lambda path: (path.stat().st_mtime, path.name), reverse=True)[0]


def latest_close(conn, ts_code):
    row = conn.execute(
        """
        SELECT close, trade_date
        FROM daily_bar
        WHERE ts_code=?
        ORDER BY trade_date DESC
        LIMIT 1
        """,
        (ts_code,),
    ).fetchone()
    if not row:
        return None, None
    return row[0], row[1]


def build_template_row(conn, row):
    ts_code = row.get("ts_code")
    latest_price, latest_trade_date = latest_close(conn, ts_code)
    return {
        "ts_code": ts_code,
        "name": row.get("user_input_name") or row.get("name") or ts_code,
        "sector": row.get("sector"),
        "market": row.get("market"),
        "current_pool_types": row.get("current_pool_types") or [],
        "primary_current_pool": row.get("primary_current_pool"),
        "reference_latest_close": latest_price,
        "reference_trade_date": latest_trade_date,
        "reference_has_external_research_snapshot": row.get("has_external_research_snapshot"),
        "reference_external_research_snapshot_count": row.get("external_research_snapshot_count"),
        "entry_date": "",
        "entry_price": None,
        "size_input_type": "shares",
        "size_input_value": None,
        "target_price": None,
        "stop_loss": None,
        "thesis": "",
        "source_report_id": None,
        "notes": "",
    }


def write_markdown(created_at, template_rows, output_path, input_rel_path):
    lines = [
        "# SMR 真实持仓最小字段模板",
        "",
        f"- created_at: {created_at}",
        f"- source_intake_rel_path: `{input_rel_path}`",
        f"- holdings_count: {len(template_rows)}",
        "- status: template_only",
        "- note: 先填写这个模板，再走 validate_live_position_intake.py 校验，最后再走 import_live_positions.py 导入。",
        "",
        "## 填写规则",
        "",
        "- `entry_date` 用 `YYYY-MM-DD`。",
        "- `entry_price / target_price / stop_loss` 都填价格，不要带货币符号。",
        "- `size_input_type` 目前支持 `shares` 或 `market_value`。",
        "- 如果填 `shares`，`size_input_value` 填真实股数。",
        "- 如果填 `market_value`，`size_input_value` 填建仓成本口径的金额，系统会按 `entry_price` 反推股数。",
        "- 这层是为了把已有真实持仓安全接到 `position` 主表，不替代以后新增仓位的 `entry.py` 门禁。",
        "",
        "## 必填字段",
        "",
        f"- {', '.join(REQUIRED_FIELDS)}",
        "",
        "## 模板预览",
        "",
        "| 名称 | ts_code | 当前池层级 | 参考收盘价 | size_input_type | size_input_value | entry_price | target_price | stop_loss |",
        "|------|---------|------------|------------|-----------------|------------------|-------------|--------------|-----------|",
    ]
    for row in template_rows:
        lines.append(
            f"| {row['name']} | {row['ts_code']} | {row.get('primary_current_pool') or '-'} | "
            f"{row.get('reference_latest_close') or '-'} | {row.get('size_input_type') or '-'} | "
            f"{row.get('size_input_value') or '-'} | {row.get('entry_price') or '-'} | "
            f"{row.get('target_price') or '-'} | {row.get('stop_loss') or '-'} |"
        )
    lines.append("")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Build a fillable live-position template")
    parser.add_argument("--input", help="Path to current_holdings_intake json; defaults to latest")
    args = parser.parse_args()

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    input_path = normalize_project_path(args.input) if args.input else find_latest_holdings_intake()
    if input_path is None or not input_path.exists():
        raise SystemExit("Input holdings intake json not found")

    payload = json.loads(input_path.read_text(encoding="utf-8"))
    source_rows = payload.get("rows") or []
    if not source_rows:
        raise SystemExit("Input holdings intake json contains no rows")

    INTAKE_DIR.mkdir(parents=True, exist_ok=True)
    template_date = created_at[:10]
    markdown_path = INTAKE_DIR / f"{template_date}_live_position_template.md"
    json_path = INTAKE_DIR / f"{template_date}_live_position_template.json"

    conn = sqlite3.connect(DB_PATH)
    template_rows = [build_template_row(conn, row) for row in source_rows]
    template_payload = {
        "created_at": created_at,
        "source_intake_rel_path": relative_to_project(input_path),
        "holdings_count": len(template_rows),
        "required_fields": REQUIRED_FIELDS,
        "rows": template_rows,
    }
    write_markdown(created_at, template_rows, markdown_path, relative_to_project(input_path))
    json_path.write_text(json.dumps(template_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    register_snapshot(
        conn,
        entity_type="portfolio_live_position_template",
        entity_id=template_date,
        status="created",
        source="build_live_position_template.py",
        relationships={
            "source_intake_rel_path": relative_to_project(input_path),
            "markdown_rel_path": relative_to_project(markdown_path),
            "json_rel_path": relative_to_project(json_path),
        },
        payload={
            "holdings_count": len(template_rows),
            "required_fields": REQUIRED_FIELDS,
        },
        created_at=created_at,
    )
    conn.commit()
    conn.close()

    log_run(
        "build_live_position_template.py",
        "success",
        "live position template built",
        {
            "source_intake_rel_path": relative_to_project(input_path),
            "holdings_count": len(template_rows),
            "markdown_rel_path": relative_to_project(markdown_path),
            "json_rel_path": relative_to_project(json_path),
        },
    )
    print(f"Live position template markdown: {markdown_path}")
    print(f"Live position template json: {json_path}")
    print(f"Holdings count: {len(template_rows)}")


if __name__ == "__main__":
    main()
