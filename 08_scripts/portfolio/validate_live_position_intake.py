#!/usr/bin/env python3
"""Validate a filled live-position intake template before importing into position."""

import argparse
import json
import math
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_paths import env_or_project_path, normalize_project_path, relative_to_project
from smr_portfolio import load_portfolio_policy
from smr_registry import register_snapshot
from smr_runlog import log_run

DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")
INTAKE_DIR = env_or_project_path("SMR_PORTFOLIO_INTAKE_DIR", "04_portfolio", "intake")


def find_latest_template_json():
    candidates = [path for path in INTAKE_DIR.glob("*_live_position_template.json") if path.is_file()]
    if not candidates:
        raise SystemExit("No live position template json found. Run build_live_position_template.py first.")
    return sorted(candidates, key=lambda path: (path.stat().st_mtime, path.name), reverse=True)[0]


def safe_float(value):
    if value in (None, "", "None", "nan", "-", "--"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def board_lot_size(ts_code):
    if str(ts_code).endswith(".SZ") or str(ts_code).endswith(".SH") or str(ts_code).endswith(".BJ"):
        return 100
    return 1


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


def current_pool_types(conn, ts_code):
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
            END DESC
        """,
        (ts_code,),
    ).fetchall()
    return [row[0] for row in rows]


def latest_recommendation(conn, ts_code):
    row = conn.execute(
        """
        SELECT report_id
        FROM research_decision_latest
        WHERE ts_code=? AND suggested_pool='recommended'
        LIMIT 1
        """,
        (ts_code,),
    ).fetchone()
    return row[0] if row else None


def duplicate_counts(rows):
    counts = defaultdict(int)
    for row in rows:
        ts_code = row.get("ts_code")
        if ts_code:
            counts[ts_code] += 1
    return counts


def parse_date(value):
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        return None


def normalize_size(ts_code, entry_price, size_input_type, size_input_value):
    blockers = []
    warnings = []
    lot = board_lot_size(ts_code)
    if size_input_type not in {"shares", "market_value"}:
        blockers.append("size_input_type 只能是 shares 或 market_value。")
        return None, None, blockers, warnings

    raw_value = safe_float(size_input_value)
    if raw_value is None or raw_value <= 0:
        blockers.append("size_input_value 必须是正数。")
        return None, None, blockers, warnings

    if size_input_type == "shares":
        if not math.isclose(raw_value, round(raw_value), rel_tol=0.0, abs_tol=1e-6):
            blockers.append("shares 模式下，size_input_value 必须是整数股数。")
            return None, None, blockers, warnings
        shares = int(round(raw_value))
        if shares <= 0:
            blockers.append("shares 必须大于 0。")
            return None, None, blockers, warnings
        if lot > 1 and shares % lot != 0:
            warnings.append(f"A 股 / 北交所常见买入手数为 {lot} 股，你当前填的是奇数手，请确认这是已有真实持仓而不是新开仓计划。")
        cost = round(entry_price * shares, 2)
        return shares, cost, blockers, warnings

    derived_shares = int(round(raw_value / entry_price / lot) * lot) if lot > 1 else int(round(raw_value / entry_price))
    if derived_shares <= 0:
        blockers.append("按 market_value 反推的股数 <= 0，请检查金额和 entry_price。")
        return None, None, blockers, warnings
    derived_cost = round(entry_price * derived_shares, 2)
    diff_pct = abs(derived_cost - raw_value) / raw_value if raw_value else 0.0
    warnings.append(
        f"当前按 market_value 反推得到 `{derived_shares}` 股，导入主表时将以推导后的 shares/cost 作为真实计算基线。"
    )
    if diff_pct >= 0.02:
        warnings.append(
            f"按 lot 取整后，推导成本 `{derived_cost:.2f}` 与输入 market_value `{raw_value:.2f}` 差异约 `{diff_pct * 100:.2f}%`。"
        )
    return derived_shares, derived_cost, blockers, warnings


def validate_row(conn, row, duplicate_map):
    ts_code = str(row.get("ts_code") or "").strip()
    name = row.get("name") or ts_code
    blockers = []
    warnings = []

    if not ts_code:
        blockers.append("缺少 ts_code。")
        return {
            "ts_code": ts_code,
            "name": name,
            "validation_status": "blocked",
            "blockers": blockers,
            "warnings": warnings,
        }

    if duplicate_map.get(ts_code, 0) > 1:
        blockers.append("输入文件里同一个 ts_code 出现了重复行。")

    entry_date_raw = str(row.get("entry_date") or "").strip()
    entry_date = parse_date(entry_date_raw)
    if entry_date is None:
        blockers.append("entry_date 必须是 YYYY-MM-DD。")

    entry_price = safe_float(row.get("entry_price"))
    target_price = safe_float(row.get("target_price"))
    stop_loss = safe_float(row.get("stop_loss"))
    if entry_price is None or entry_price <= 0:
        blockers.append("entry_price 必须大于 0。")
    if target_price is None or target_price <= 0:
        blockers.append("target_price 必须大于 0。")
    if stop_loss is None or stop_loss <= 0:
        blockers.append("stop_loss 必须大于 0。")
    if entry_price is not None and stop_loss is not None and stop_loss >= entry_price:
        blockers.append("stop_loss 必须小于 entry_price。")
    if entry_price is not None and target_price is not None and target_price <= entry_price:
        blockers.append("target_price 必须大于 entry_price。")

    thesis = str(row.get("thesis") or "").strip()
    if not thesis:
        blockers.append("thesis 不能为空。")

    latest_price, latest_trade_date = latest_close(conn, ts_code)
    if latest_price is None:
        blockers.append("当前库里没有这只票的最新 daily_bar，导入后 PnL 主链跑不起来。")

    open_position_exists = conn.execute(
        "SELECT COUNT(*) FROM position WHERE ts_code=? AND status='open'",
        (ts_code,),
    ).fetchone()[0]
    if open_position_exists:
        blockers.append("position 主表里已经存在这只票的 open 持仓，当前导入会重复。")

    pool_types = current_pool_types(conn, ts_code)
    latest_report_id = latest_recommendation(conn, ts_code)
    primary_current_pool = pool_types[0] if pool_types else None
    if primary_current_pool != "portfolio_seed":
        warnings.append("这只票当前不在 portfolio_seed 顶层，确认它是否真的是你当前真实持仓。")
    if "recommended" not in set(pool_types):
        warnings.append("这只票当前不在 recommended。对已有持仓这不阻塞导入，但说明它不满足新增开仓门禁。")
    if not row.get("source_report_id"):
        warnings.append("当前没填 source_report_id。对已有持仓这不阻塞，但后续追溯推荐来源会弱一些。")
    elif latest_report_id and row.get("source_report_id") != latest_report_id:
        warnings.append(f"当前填写的 source_report_id 与系统最新 recommended 来源 `{latest_report_id}` 不一致。")

    derived_shares = None
    derived_cost = None
    size_input_type = str(row.get("size_input_type") or "").strip()
    size_input_value = row.get("size_input_value")
    if entry_price is not None and entry_price > 0:
        derived_shares, derived_cost, size_blockers, size_warnings = normalize_size(
            ts_code,
            entry_price,
            size_input_type,
            size_input_value,
        )
        blockers.extend(size_blockers)
        warnings.extend(size_warnings)

    if latest_trade_date and entry_date and entry_date.strftime("%Y-%m-%d") > latest_trade_date:
        warnings.append("entry_date 晚于当前库里最新 trade_date，请确认日期口径是否正确。")

    validation_status = "ready" if not blockers else "blocked"
    projected_single_position_pct = None
    if derived_cost is not None:
        projected_single_position_pct = round(derived_cost / float(load_portfolio_policy()["portfolio_capital"]), 6)

    return {
        "ts_code": ts_code,
        "name": name,
        "sector": row.get("sector"),
        "market": row.get("market"),
        "current_pool_types": pool_types or row.get("current_pool_types") or [],
        "primary_current_pool": primary_current_pool or row.get("primary_current_pool"),
        "entry_date": entry_date_raw,
        "entry_price": entry_price,
        "size_input_type": size_input_type,
        "size_input_value": size_input_value,
        "derived_shares": derived_shares,
        "derived_cost": derived_cost,
        "target_price": target_price,
        "stop_loss": stop_loss,
        "thesis": thesis,
        "source_report_id": row.get("source_report_id"),
        "latest_trade_date": latest_trade_date,
        "latest_close": latest_price,
        "validation_status": validation_status,
        "blockers": blockers,
        "warnings": warnings,
        "notes": row.get("notes"),
        "projected_single_position_pct": projected_single_position_pct,
    }


def build_policy_summary(policy, ready_rows):
    total_cost = round(sum(row.get("derived_cost") or 0.0 for row in ready_rows), 2)
    capital = float(policy["portfolio_capital"])
    sector_costs = Counter()
    for row in ready_rows:
        sector_costs[row.get("sector") or "unknown"] += row.get("derived_cost") or 0.0
    sector_pct = {sector: round(cost / capital, 6) for sector, cost in sector_costs.items()} if capital else {}
    total_exposure_pct = round(total_cost / capital, 6) if capital else 0.0

    warnings = []
    if total_exposure_pct > policy["max_total_exposure_pct"]:
        warnings.append(
            f"按当前输入推演，总暴露约 `{total_exposure_pct * 100:.2f}%`，高于策略上限 `{policy['max_total_exposure_pct'] * 100:.2f}%`。"
        )
    for sector, pct in sorted(sector_pct.items()):
        if pct > policy["max_sector_concentration_pct"]:
            warnings.append(
                f"行业 `{sector}` 暴露约 `{pct * 100:.2f}%`，高于策略上限 `{policy['max_sector_concentration_pct'] * 100:.2f}%`。"
            )
    for row in ready_rows:
        if (row.get("projected_single_position_pct") or 0.0) > policy["max_single_position_pct"]:
            warnings.append(
                f"{row['ts_code']} 单票暴露约 `{row['projected_single_position_pct'] * 100:.2f}%`，高于策略上限 `{policy['max_single_position_pct'] * 100:.2f}%`。"
            )
    return total_cost, total_exposure_pct, dict(sector_costs), sector_pct, warnings


def write_markdown(output_path, payload):
    lines = [
        "# SMR 真实持仓导入校验报告",
        "",
        f"- created_at: {payload['created_at']}",
        f"- input_rel_path: `{payload['input_rel_path']}`",
        f"- row_count: {payload['row_count']}",
        f"- ready_count: {payload['ready_count']}",
        f"- blocked_count: {payload['blocked_count']}",
        f"- warning_count: {payload['warning_count']}",
        f"- projected_total_cost: `{payload['projected_total_cost']}`",
        f"- projected_total_exposure_pct: `{payload['projected_total_exposure_pct']}`",
        "",
        "## 全局提醒",
        "",
    ]
    for item in payload.get("global_warnings") or ["当前没有额外全局提醒。"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 行级校验结果", ""])
    for row in payload.get("rows") or []:
        lines.extend(
            [
                f"### {row.get('name') or row.get('ts_code')} / {row.get('ts_code') or '-'}",
                "",
                f"- validation_status: `{row.get('validation_status') or '-'}`",
                f"- primary_current_pool: `{row.get('primary_current_pool') or '-'}`",
                f"- latest_trade_date: `{row.get('latest_trade_date') or '-'}`",
                f"- latest_close: `{row.get('latest_close')}`",
                f"- derived_shares: `{row.get('derived_shares')}`",
                f"- derived_cost: `{row.get('derived_cost')}`",
                f"- projected_single_position_pct: `{row.get('projected_single_position_pct')}`",
                "",
                "#### blockers",
                "",
            ]
        )
        for item in row.get("blockers") or ["无"]:
            lines.append(f"- {item}")
        lines.extend(["", "#### warnings", ""])
        for item in row.get("warnings") or ["无"]:
            lines.append(f"- {item}")
        lines.append("")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Validate a filled live-position intake template")
    parser.add_argument("--input", help="Path to live_position_template json; defaults to latest")
    args = parser.parse_args()

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    input_path = normalize_project_path(args.input) if args.input else find_latest_template_json()
    if input_path is None or not input_path.exists():
        raise SystemExit("Input live position template json not found")

    raw_payload = json.loads(input_path.read_text(encoding="utf-8"))
    rows = raw_payload.get("rows") or []
    if not rows:
        raise SystemExit("Input live position template json contains no rows")

    conn = sqlite3.connect(DB_PATH)
    duplicate_map = duplicate_counts(rows)
    validated_rows = [validate_row(conn, row, duplicate_map) for row in rows]
    ready_rows = [row for row in validated_rows if row["validation_status"] == "ready"]
    blocked_rows = [row for row in validated_rows if row["validation_status"] != "ready"]

    policy = load_portfolio_policy()
    projected_total_cost, projected_total_exposure_pct, sector_costs, sector_pct, global_warnings = build_policy_summary(
        policy,
        ready_rows,
    )
    warning_count = len(global_warnings) + sum(len(row.get("warnings") or []) for row in validated_rows)

    output_date = created_at[:10]
    markdown_path = INTAKE_DIR / f"{output_date}_live_position_validation.md"
    json_path = INTAKE_DIR / f"{output_date}_live_position_validation.json"
    output_payload = {
        "created_at": created_at,
        "input_rel_path": relative_to_project(input_path),
        "row_count": len(validated_rows),
        "ready_count": len(ready_rows),
        "blocked_count": len(blocked_rows),
        "warning_count": warning_count,
        "projected_total_cost": projected_total_cost,
        "projected_total_exposure_pct": projected_total_exposure_pct,
        "projected_sector_costs": sector_costs,
        "projected_sector_exposure_pct": sector_pct,
        "global_warnings": global_warnings,
        "ready_rows": ready_rows,
        "blocked_rows": blocked_rows,
        "rows": validated_rows,
    }
    write_markdown(markdown_path, output_payload)
    json_path.write_text(json.dumps(output_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    status = "ready" if ready_rows and not blocked_rows else "blocked" if blocked_rows else "empty"
    register_snapshot(
        conn,
        entity_type="portfolio_live_position_validation",
        entity_id=output_date,
        status=status,
        source="validate_live_position_intake.py",
        relationships={
            "input_rel_path": relative_to_project(input_path),
            "markdown_rel_path": relative_to_project(markdown_path),
            "json_rel_path": relative_to_project(json_path),
        },
        payload={
            "ready_count": len(ready_rows),
            "blocked_count": len(blocked_rows),
            "warning_count": warning_count,
            "projected_total_exposure_pct": projected_total_exposure_pct,
            "global_warnings": global_warnings,
        },
        created_at=created_at,
    )
    conn.commit()
    conn.close()

    log_run(
        "validate_live_position_intake.py",
        "success",
        "live position intake validated",
        {
            "input_rel_path": relative_to_project(input_path),
            "ready_count": len(ready_rows),
            "blocked_count": len(blocked_rows),
            "warning_count": warning_count,
            "markdown_rel_path": relative_to_project(markdown_path),
            "json_rel_path": relative_to_project(json_path),
        },
    )
    print(f"Live position validation markdown: {markdown_path}")
    print(f"Live position validation json: {json_path}")
    print(f"Ready rows: {len(ready_rows)}")
    print(f"Blocked rows: {len(blocked_rows)}")
    print(f"Warnings: {warning_count}")


if __name__ == "__main__":
    main()
