#!/usr/bin/env python3
"""Build execution-plan drafts from rotation candidates and portfolio constraints."""

import argparse
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH, ensure_auto_handoff, get_latest_registry_entry
from smr_paths import env_or_project_path, relative_to_project
from smr_portfolio import (
    current_open_positions,
    has_unacknowledged_critical_alert,
    load_portfolio_policy,
    resolve_sector,
)
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_universe import relation_exists

OUTPUT_DIR = env_or_project_path("SMR_PORTFOLIO_EXECUTION_PLAN_DIR", "04_portfolio", "execution_plans")

DISPLAY_LABELS = {
    "reference_only": "参照层建议",
    "live_positions": "真实持仓模式",
    "ready": "可推进",
    "watch_only": "仅观察",
    "blocked": "阻塞",
    "same_sector_upgrade": "同主线做强换弱",
    "cross_sector_mainline_switch": "跨主题切主线",
    "cross_sector_probe": "跨主题试探",
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
    results = []
    for value in values:
        if value in (None, ""):
            continue
        if value in seen:
            continue
        seen.add(value)
        results.append(value)
    return results


def display_label(value):
    if value in (None, ""):
        return "-"
    return DISPLAY_LABELS.get(str(value), str(value))


def load_rotation_entry(conn, entity_id=None):
    if entity_id:
        entry = get_latest_registry_entry(conn, "rotation_candidate_snapshot", entity_id)
        if entry is None:
            raise SystemExit(f"rotation_candidate_snapshot not found for entity_id: {entity_id}")
        return entry

    row = conn.execute(
        """
        SELECT entity_id
        FROM task_registry_entity_latest
        WHERE entity_type='rotation_candidate_snapshot'
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """
    ).fetchone()
    if not row:
        raise SystemExit("rotation_candidate_snapshot not found")
    entry = get_latest_registry_entry(conn, "rotation_candidate_snapshot", row[0])
    if entry is None:
        raise SystemExit("latest rotation_candidate_snapshot entry missing")
    return entry


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
    return safe_float(row[0]), row[1]


def load_reference_holdings(conn):
    if not relation_exists(conn, "stock_pool_current"):
        return []
    rows = conn.execute(
        """
        SELECT ts_code
        FROM stock_pool_current
        WHERE pool_type='portfolio_seed'
        ORDER BY ts_code
        """
    ).fetchall()
    results = []
    for (ts_code,) in rows:
        sector = resolve_sector(conn, ts_code) or "unknown"
        results.append({"ts_code": ts_code, "sector": sector})
    return results


def current_mode(conn):
    open_positions = current_open_positions(conn)
    if open_positions:
        return "live_positions", open_positions
    return "reference_only", []


def board_lot_size(ts_code):
    if ts_code.endswith(".SZ") or ts_code.endswith(".SH") or ts_code.endswith(".BJ"):
        return 100
    return 1


def target_gap_pct(item):
    research = item.get("external_research") or {}
    target_price = safe_float(research.get("target_price_yuan"))
    latest_close = safe_float(item.get("latest_close"))
    if target_price is None or latest_close in (None, 0):
        return None
    return round((target_price - latest_close) / latest_close * 100, 2)


def base_reference_context(conn, policy):
    holdings = load_reference_holdings(conn)
    capital = float(policy["portfolio_capital"])
    holding_count = len(holdings)
    if holding_count <= 0:
        return {
            "mode": "reference_only",
            "holding_count": 0,
            "slot_pct": 0.0,
            "slot_capital": 0.0,
            "total_exposure_pct": 0.0,
            "sector_costs": {},
        }

    slot_pct = min(float(policy["max_single_position_pct"]), float(policy["max_total_exposure_pct"]) / holding_count)
    slot_capital = capital * slot_pct
    sector_costs = {}
    for item in holdings:
        sector = item["sector"]
        sector_costs[sector] = sector_costs.get(sector, 0.0) + slot_capital
    return {
        "mode": "reference_only",
        "holding_count": holding_count,
        "slot_pct": round(slot_pct, 6),
        "slot_capital": round(slot_capital, 2),
        "total_exposure_pct": round(slot_pct * holding_count, 6),
        "sector_costs": sector_costs,
    }


def base_live_context(conn, policy, open_positions):
    capital = float(policy["portfolio_capital"])
    sector_costs = {}
    positions_by_code = {}
    total_cost = 0.0
    for ts_code, entry_date, entry_price, shares, cost, target_price, stop_loss, thesis, pnl, pnl_pct in open_positions:
        item = {
            "ts_code": ts_code,
            "entry_date": entry_date,
            "entry_price": safe_float(entry_price),
            "shares": shares,
            "cost": safe_float(cost) or 0.0,
            "target_price": safe_float(target_price),
            "stop_loss": safe_float(stop_loss),
            "thesis": thesis,
            "pnl": safe_float(pnl),
            "pnl_pct": safe_float(pnl_pct),
        }
        positions_by_code[ts_code] = item
        total_cost += item["cost"]
        sector = resolve_sector(conn, ts_code) or "unknown"
        sector_costs[sector] = sector_costs.get(sector, 0.0) + item["cost"]
    return {
        "mode": "live_positions",
        "holding_count": len(open_positions),
        "slot_pct": None,
        "slot_capital": None,
        "total_exposure_pct": round(total_cost / capital, 6) if capital else 0.0,
        "sector_costs": sector_costs,
        "positions_by_code": positions_by_code,
    }


def simulated_sector_costs(base_sector_costs, remove_sector, add_sector, trade_amount):
    sector_costs = dict(base_sector_costs)
    if remove_sector:
        sector_costs[remove_sector] = max(0.0, sector_costs.get(remove_sector, 0.0) - trade_amount)
    if add_sector:
        sector_costs[add_sector] = sector_costs.get(add_sector, 0.0) + trade_amount
    return sector_costs


def build_gate_result(conn, policy, mode, trade_amount, add_item, remove_item, after_sector_costs, before_total_exposure_pct):
    capital = float(policy["portfolio_capital"])
    add_sector = add_item.get("sector") or "unknown"
    gate_checks = []
    if add_item.get("primary_pool") != "recommended":
        gate_checks.append(("watch_only_not_recommended", False, "调入腿当前还不在推荐池，不能直接走正式开仓门禁。"))
    else:
        gate_checks.append(("recommended_pool", True, "调入腿当前已在推荐池。"))

    if has_unacknowledged_critical_alert(conn):
        gate_checks.append(("critical_risk_alert", False, "当前存在未确认的 critical 风险预警。"))
    else:
        gate_checks.append(("critical_risk_alert", True, "当前没有未确认的 critical 风险预警。"))

    single_position_pct = trade_amount / capital if capital else 0.0
    if single_position_pct > float(policy["max_single_position_pct"]):
        gate_checks.append(("single_position_limit", False, "单票暴露会超过上限。"))
    else:
        gate_checks.append(("single_position_limit", True, "单票暴露仍在上限内。"))

    sector_pct = after_sector_costs.get(add_sector, 0.0) / capital if capital else 0.0
    if sector_pct > float(policy["max_sector_concentration_pct"]):
        gate_checks.append(("sector_limit", False, "换仓后该行业暴露会超过上限。"))
    else:
        gate_checks.append(("sector_limit", True, "换仓后行业暴露仍在上限内。"))

    total_exposure_pct = before_total_exposure_pct
    if total_exposure_pct > float(policy["max_total_exposure_pct"]):
        gate_checks.append(("total_exposure_limit", False, "当前总暴露已超过上限。"))
    else:
        gate_checks.append(("total_exposure_limit", True, "总暴露约束正常。"))

    if mode == "live_positions" and remove_item.get("ts_code") not in {
        row[0] for row in current_open_positions(conn)
    }:
        gate_checks.append(("live_remove_leg", False, "调出腿不在真实 open positions 中。"))
    elif mode == "live_positions":
        gate_checks.append(("live_remove_leg", True, "调出腿存在于真实 open positions 中。"))

    status = "ready"
    if any(not passed for _key, passed, _message in gate_checks):
        if any(key == "watch_only_not_recommended" and not passed for key, passed, _ in gate_checks):
            status = "watch_only"
        else:
            status = "blocked"

    return {
        "status": status,
        "checks": [{"key": key, "passed": passed, "message": message} for key, passed, message in gate_checks],
        "single_position_pct": round(single_position_pct, 6),
        "add_sector_pct_after": round(sector_pct, 6),
        "total_exposure_pct": round(total_exposure_pct, 6),
    }


def expected_uplift(add_item, remove_item, pair_score):
    add_gap = target_gap_pct(add_item)
    remove_gap = target_gap_pct(remove_item)
    if add_gap is not None and remove_gap is not None:
        delta = round(add_gap - remove_gap, 2)
        summary = f"若按公开目标价口径，调入腿隐含空间约 `{add_gap}%`，调出腿约 `{remove_gap}%`，差额 `{delta}%`。"
        return {
            "mode": "target_gap_delta",
            "add_target_gap_pct": add_gap,
            "remove_target_gap_pct": remove_gap,
            "delta_pct": delta,
            "summary": summary,
        }
    return {
        "mode": "structure_proxy_only",
        "add_target_gap_pct": add_gap,
        "remove_target_gap_pct": remove_gap,
        "delta_pct": None,
        "summary": f"当前缺少统一目标价口径，先用结构改善代理分 `{pair_score}` 表示相对优化强度。",
    }


def execution_checklist(mode, gate_result, add_item, remove_item, trade_amount, suggested_shares, latest_trade_date):
    checks = []
    if gate_result["status"] == "watch_only":
        checks.append("先等待调入腿进入推荐池，再决定是否走正式开仓。")
    elif gate_result["status"] == "blocked":
        checks.append("先解决被门禁拦住的项，再考虑执行。")
    else:
        checks.append("可以先做一笔受控试单，再观察换仓后的主线延续。")

    checks.append(f"拟替换金额约 `{trade_amount:.2f}`，建议下单前再确认最新价格与流动性。")
    if suggested_shares:
        checks.append(f"若按最新价粗估，调入腿可先试 `{suggested_shares}` 股。")
    checks.append(f"执行前复核 `{remove_item.get('ts_code')}` 的退出理由是否仍成立。")
    checks.append(f"执行前补齐 `{add_item.get('ts_code')}` 的止损、目标价和 thesis（投资逻辑）。")
    if latest_trade_date:
        checks.append(f"当前计划基于 `{latest_trade_date}` 的最新行情。")
    return checks[:5]


def build_plan_rows(conn, policy, mode, context, rotation_pairs):
    capital = float(policy["portfolio_capital"])
    plans = []
    positions_by_code = context.get("positions_by_code") or {}
    for pair in rotation_pairs:
        add_item = pair.get("add") or {}
        remove_item = pair.get("remove") or {}
        add_code = add_item.get("ts_code")
        remove_code = remove_item.get("ts_code")
        if not add_code or not remove_code:
            continue

        add_sector = add_item.get("sector") or "unknown"
        remove_sector = remove_item.get("sector") or "unknown"
        if mode == "live_positions" and remove_code in positions_by_code:
            trade_amount = safe_float(positions_by_code[remove_code].get("cost")) or 0.0
        else:
            trade_amount = safe_float(context.get("slot_capital")) or 0.0
        latest_close_value, latest_trade_date = latest_close(conn, add_code)
        lot = board_lot_size(add_code)
        suggested_shares = None
        if latest_close_value and trade_amount > 0:
            raw_shares = int(trade_amount // latest_close_value)
            if lot > 1:
                raw_shares = (raw_shares // lot) * lot
            suggested_shares = raw_shares if raw_shares > 0 else None
        after_sector_costs = simulated_sector_costs(context.get("sector_costs") or {}, remove_sector, add_sector, trade_amount)
        gate_result = build_gate_result(
            conn,
            policy,
            mode,
            trade_amount,
            add_item,
            remove_item,
            after_sector_costs,
            safe_float(context.get("total_exposure_pct")) or 0.0,
        )
        uplift = expected_uplift(add_item, remove_item, pair.get("pair_score"))
        plan = {
            "plan_id": f"{add_code}__{remove_code}",
            "mode": mode,
            "add": add_item,
            "remove": remove_item,
            "rotation_type": pair.get("fit_label"),
            "pair_score": pair.get("pair_score"),
            "trade_amount": round(trade_amount, 2),
            "trade_amount_pct": round(trade_amount / capital, 6) if capital else 0.0,
            "suggested_shares": suggested_shares,
            "latest_trade_date": latest_trade_date,
            "latest_add_close": latest_close_value,
            "gate_result": gate_result,
            "uplift": uplift,
            "risk_flags": ordered_unique(pair.get("risk_flags") or []),
            "expected_positive_change": ordered_unique(pair.get("expected_positive_change") or []),
            "before_sector_pct": round((context.get("sector_costs") or {}).get(add_sector, 0.0) / capital, 6) if capital else 0.0,
            "after_sector_pct": round(after_sector_costs.get(add_sector, 0.0) / capital, 6) if capital else 0.0,
            "after_sector_costs": {key: round(value, 2) for key, value in after_sector_costs.items()},
            "execution_checklist": execution_checklist(
                mode,
                gate_result,
                add_item,
                remove_item,
                trade_amount,
                suggested_shares,
                latest_trade_date,
            ),
        }
        plans.append(plan)
    status_rank = {"ready": 0, "watch_only": 1, "blocked": 2}
    plans.sort(key=lambda item: (status_rank.get((item.get("gate_result") or {}).get("status"), 9), -(safe_float(item.get("pair_score")) or 0.0)))
    return plans


def format_pct(value):
    if value is None:
        return "-"
    return f"{value * 100:.2f}%"


def write_plan(path, created_at, rotation_date, policy, mode, context, plans):
    lines = [
        "# SMR 执行方案草案",
        "",
        f"- created_at: {created_at}",
        f"- rotation_snapshot_date: {rotation_date}",
        f"- plan_mode: {display_label(mode)}",
        f"- portfolio_capital: {policy['portfolio_capital']}",
        f"- max_single_position_pct: {format_pct(policy['max_single_position_pct'])}",
        f"- max_sector_concentration_pct: {format_pct(policy['max_sector_concentration_pct'])}",
        f"- max_total_exposure_pct: {format_pct(policy['max_total_exposure_pct'])}",
        "",
        "## 使用边界",
        "",
    ]
    if mode == "reference_only":
        lines.append("- 当前还没有真实持仓，所以这份草案基于持仓参照层做等权参照推演。")
        lines.append(f"- 当前参照槽位数：`{context.get('holding_count', 0)}`，单槽位名义资金约 `{context.get('slot_capital', 0.0):.2f}`。")
    else:
        lines.append("- 当前已有真实 open positions，这份草案基于真实持仓成本做换仓推演。")
    lines.extend(
        [
            "- 这里的“预期正向变化”分两层：有目标价时给目标价差额口径，没有时退回到结构改善代理分。",
            "- 真正执行前，仍要叠加 `entry.py / pnl.py / risk_monitor_snapshot` 的正式门禁。",
            "",
            "## 当前组合参照",
            "",
            f"- holding_count: `{context.get('holding_count', 0)}`",
            f"- total_exposure_pct: `{format_pct(context.get('total_exposure_pct'))}`",
        ]
    )
    if mode == "reference_only":
        lines.append(f"- slot_pct: `{format_pct(context.get('slot_pct'))}`")
        lines.append(f"- slot_capital: `{context.get('slot_capital', 0.0):.2f}`")
    lines.extend(["", "## 优先执行方案", ""])
    if not plans:
        lines.append("- 当前没有可生成的执行方案草案。")
        lines.append("")
    for plan in plans[:3]:
        add_item = plan["add"]
        remove_item = plan["remove"]
        gate = plan["gate_result"]
        uplift = plan["uplift"]
        lines.extend(
            [
                f"### 调入 {add_item.get('name') or add_item.get('ts_code', '-')} / {add_item.get('ts_code') or '-'}",
                "",
                f"- 对应调出：`{remove_item.get('ts_code') or '-'} {remove_item.get('name') or ''}`",
                f"- gate_status: {display_label(gate.get('status') or '-')}",
                f"- rotation_type: {display_label(plan.get('rotation_type') or '-')}",
                f"- pair_score: `{plan.get('pair_score')}`",
                f"- trade_amount: `{plan.get('trade_amount')}`",
                f"- trade_amount_pct: `{format_pct(plan.get('trade_amount_pct'))}`",
                f"- suggested_shares: `{plan.get('suggested_shares') or '-'}`",
                f"- add_sector_pct_before_after: `{format_pct(plan.get('before_sector_pct'))}` -> `{format_pct(plan.get('after_sector_pct'))}`",
                f"- uplift_mode: `{uplift.get('mode') or '-'}`",
                f"- uplift_summary: {uplift.get('summary') or '-'}",
                "",
                "#### 结构改善",
                "",
            ]
        )
        for reason in plan.get("expected_positive_change") or []:
            lines.append(f"- {reason}")
        lines.extend(["", "#### 主要风险", ""])
        for risk in plan.get("risk_flags") or ["当前没有额外风险说明。"]:
            lines.append(f"- {risk}")
        lines.extend(["", "#### 执行前检查", ""])
        for item in plan.get("execution_checklist") or []:
            lines.append(f"- {item}")
        lines.extend(["", "#### 门禁明细", ""])
        for check in gate.get("checks") or []:
            status = "PASS" if check.get("passed") else "BLOCK"
            lines.append(f"- {status} / `{check.get('key')}` / {check.get('message')}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Build execution-plan drafts from rotation candidates")
    parser.add_argument("--date", help="rotation_candidate_snapshot entity_id date")
    args = parser.parse_args()

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    rotation_entry = load_rotation_entry(conn, args.date)
    rotation_payload = rotation_entry.get("payload", {}) or {}
    rotation_pairs = rotation_payload.get("rotation_pairs") or []
    rotation_date = rotation_entry.get("entity_id")
    policy = load_portfolio_policy()
    mode, open_positions = current_mode(conn)
    if mode == "live_positions":
        context = base_live_context(conn, policy, open_positions)
    else:
        context = base_reference_context(conn, policy)
    plans = build_plan_rows(conn, policy, mode, context, rotation_pairs)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{rotation_date}_rotation_execution_plan.md"
    write_plan(output_path, created_at, rotation_date, policy, mode, context, plans)

    status_counts = Counter((plan.get("gate_result") or {}).get("status", "unknown") for plan in plans)
    entry = register_snapshot(
        conn,
        entity_type="rotation_execution_plan_snapshot",
        entity_id=rotation_date,
        status="generated" if plans else "empty",
        source="build_rotation_execution_plan.py",
        relationships={
            "summary_rel_path": relative_to_project(output_path),
            "rotation_snapshot_rel_path": rotation_payload.get("summary_rel_path"),
            "rotation_source_entry_id": rotation_entry["id"],
        },
        payload={
            "plan_mode": mode,
            "holding_count": context.get("holding_count", 0),
            "slot_capital": context.get("slot_capital"),
            "slot_pct": context.get("slot_pct"),
            "total_exposure_pct": context.get("total_exposure_pct"),
            "plan_count": len(plans),
            "status_counts": dict(status_counts),
            "summary_rel_path": relative_to_project(output_path),
            "plans": plans,
        },
        created_at=created_at,
    )
    handoff_result = ensure_auto_handoff(
        conn,
        entry,
        note="执行方案草案已更新，自动转交 Hermes-like 研究代理补充解释并同步调度。",
        created_by="build_rotation_execution_plan.py",
    )
    conn.commit()
    conn.close()

    log_run(
        "build_rotation_execution_plan.py",
        "success",
        "rotation execution plans built",
        {
            "entity_id": rotation_date,
            "plan_mode": mode,
            "plan_count": len(plans),
            "summary_rel_path": relative_to_project(output_path),
            "handoff_result": handoff_result["reason"],
            "handoff_id": handoff_result["handoff"]["handoff_id"] if handoff_result["handoff"] else None,
        },
    )
    print(f"Rotation execution plan snapshot registered: {rotation_date}")
    print(f"Summary file: {output_path}")
    print(f"Plan mode: {mode}")
    print(f"Plan count: {len(plans)}")
    if handoff_result["handoff"]:
        print(
            f"Auto handoff {handoff_result['reason']}: "
            f"{handoff_result['handoff']['handoff_id']} -> {handoff_result['handoff']['to_profile_id']}"
        )
    else:
        print(f"Auto handoff skipped: {handoff_result['reason']}")


if __name__ == "__main__":
    main()
