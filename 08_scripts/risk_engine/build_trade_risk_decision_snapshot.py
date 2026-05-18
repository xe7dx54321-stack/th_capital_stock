#!/usr/bin/env python3
"""Build a boss-facing trade risk snapshot for buy/sell decisions."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH, get_latest_registry_entry, get_registry_entry_by_id
from smr_paths import env_or_project_path, relative_to_project
from smr_portfolio import current_open_positions, latest_price, load_portfolio_policy, projected_total_cost
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_universe import relation_exists

OUTPUT_DIR = env_or_project_path("SMR_RISK_DECISION_DIR", "05_risk", "decision")

BUY_VERDICT_LABELS = {
    "buy": "可买入",
    "buy_small": "小仓试单",
    "watch": "继续观察",
    "block": "暂不买入",
}

SELL_VERDICT_LABELS = {
    "sell": "优先卖出",
    "trim": "建议减仓",
    "watch": "持仓观察",
    "hold": "继续持有",
}

PORTFOLIO_STATE_LABELS = {
    "normal": "正常推进",
    "cautious": "谨慎推进",
    "blocked": "暂停新增风险",
}

BUY_PRIORITY_RANK = {"buy": 4, "buy_small": 3, "watch": 2, "block": 1}
SELL_PRIORITY_RANK = {"sell": 4, "trim": 3, "watch": 2, "hold": 1}

PRIORITY_BUY_SCORE = {"high": 10, "medium": 5, "low": 0}
OBJECTIVE_BUY_SCORE = {"trend_follow": 8, "trend_positive": 5, "observe": -5, "repair_needed": -14}
TREND_BUY_SCORE = {"trend_strong": 8, "trend_hot": -4, "under_ma60": -10}
VALUATION_BUY_SCORE = {"high": -8, "medium": -3}
RESEARCH_BUY_SCORE = {"fresh": 4, "usable": 1, "aging": -4, "stale": -9, "missing": -12}
FRESHNESS_BUY_SCORE = {"fresh": 4, "usable": 2, "aging": -2, "stale": -5, "missing": -8}
PUBLIC_SIGNAL_BUY_SCORE = {
    "supportive_strong": 6,
    "supportive": 4,
    "neutral": 0,
    "neutral_watch": -2,
    "stretched": -4,
    "cautious": -8,
    "not_applicable": 0,
}

OBJECTIVE_SELL_SCORE = {"repair_needed": 24, "observe": 12, "trend_positive": 2, "trend_follow": 0}
TREND_SELL_SCORE = {"under_ma60": 22, "trend_hot": 6, "trend_strong": -8}
VALUATION_SELL_SCORE = {"high": 10, "medium": 4}
RESEARCH_SELL_SCORE = {"aging": 4, "stale": 8, "missing": 10}
PUBLIC_SIGNAL_SELL_SCORE = {
    "supportive_strong": -5,
    "supportive": -3,
    "neutral": 0,
    "neutral_watch": 4,
    "stretched": 8,
    "cautious": 14,
    "not_applicable": 0,
}

DISPLAY_LABELS = {
    "ready": "可推进",
    "watch_only": "仅观察",
    "blocked": "阻塞",
    "reference_only": "持仓参照层",
    "live_positions": "真实持仓",
    "swap_ready": "优先换仓",
    "swap_watch": "观察换仓",
    "swap_blocked": "阻塞换仓",
    "holding_watch": "持仓复核",
    "opportunity_followup": "机会跟踪",
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
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        rows.append(text)
    return rows


def display_label(value):
    if value in (None, ""):
        return "-"
    return DISPLAY_LABELS.get(str(value), str(value))


def label_from_nested(item, plain_key, nested_key):
    nested = item.get(nested_key) or {}
    if nested.get("label"):
        return nested.get("label")
    return item.get(plain_key)


def summary_from_nested(item, plain_key, nested_key):
    nested = item.get(nested_key) or {}
    if nested.get("summary"):
        return nested.get("summary")
    return item.get(plain_key)


def load_snapshot_entry(conn, entity_type, entity_id=None, required=True):
    if entity_id:
        entry = get_latest_registry_entry(conn, entity_type, entity_id)
        if entry is not None:
            return entry
    row = conn.execute(
        """
        SELECT id
        FROM task_registry_entity_latest
        WHERE entity_type=?
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """,
        (entity_type,),
    ).fetchone()
    if not row:
        if required:
            raise SystemExit(f"{entity_type} not found")
        return None
    entry = get_registry_entry_by_id(conn, row[0])
    if entry is None and required:
        raise SystemExit(f"latest {entity_type} entry missing")
    return entry


def load_live_position_map(conn):
    positions = {}
    for (
        ts_code,
        entry_date,
        entry_price,
        shares,
        cost,
        target_price,
        stop_loss,
        thesis,
        pnl,
        pnl_pct,
    ) in current_open_positions(conn):
        current_price = latest_price(conn, ts_code)
        current_pnl_pct = None
        if current_price is not None and safe_float(entry_price) not in (None, 0):
            current_pnl_pct = round((current_price - float(entry_price)) / float(entry_price) * 100, 2)
        elif safe_float(pnl_pct) is not None:
            current_pnl_pct = round(float(pnl_pct) * 100, 2)
        positions[ts_code] = {
            "ts_code": ts_code,
            "entry_date": entry_date,
            "entry_price": safe_float(entry_price),
            "shares": shares,
            "cost": safe_float(cost) or 0.0,
            "target_price": safe_float(target_price),
            "stop_loss": safe_float(stop_loss),
            "thesis": thesis,
            "pnl": safe_float(pnl),
            "pnl_pct": current_pnl_pct,
            "current_price": safe_float(current_price),
        }
    return positions


def load_reference_holdings(conn):
    if not relation_exists(conn, "stock_pool_current"):
        return []
    rows = conn.execute(
        """
        SELECT ts_code, sector
        FROM stock_pool_current
        WHERE pool_type='portfolio_seed'
        ORDER BY ts_code
        """
    ).fetchall()
    return [
        {
            "ts_code": row[0],
            "name": None,
            "sector": row[1],
        }
        for row in rows
    ]


def recent_alerts_by_symbol(conn, symbols):
    if not symbols:
        return {}
    placeholders = ",".join("?" for _ in symbols)
    rows = conn.execute(
        f"""
        SELECT ts_code, severity, alert_type, message, action, alert_time, acknowledged
        FROM risk_alert
        WHERE ts_code IN ({placeholders})
        ORDER BY datetime(alert_time) DESC, alert_id DESC
        """,
        tuple(symbols),
    ).fetchall()
    grouped = {symbol: [] for symbol in symbols}
    for row in rows:
        grouped.setdefault(row[0], []).append(
            {
                "ts_code": row[0],
                "severity": row[1],
                "alert_type": row[2],
                "message": row[3],
                "action": row[4],
                "alert_time": row[5],
                "acknowledged": bool(row[6]),
            }
        )
    return grouped


def portfolio_context(conn, policy, risk_entry, precheck_entry, live_positions, reference_holdings):
    decision_policy = (policy.get("decision_policy") or {}).copy()
    capital = float(policy["portfolio_capital"])
    risk_payload = (risk_entry or {}).get("payload", {}) or {}
    precheck_payload = (precheck_entry or {}).get("payload", {}) or {}

    mode = "live_positions" if live_positions else "reference_only"
    exposure_pct = round(projected_total_cost(conn) / capital, 6) if live_positions else 0.0
    headroom_pct = max(0.0, round(float(policy["max_total_exposure_pct"]) - exposure_pct, 6))

    critical_unacked = conn.execute(
        "SELECT COUNT(*) FROM risk_alert WHERE severity='critical' AND acknowledged=0"
    ).fetchone()[0]
    warning_unacked = conn.execute(
        "SELECT COUNT(*) FROM risk_alert WHERE severity='warning' AND acknowledged=0"
    ).fetchone()[0]

    precheck_status = precheck_payload.get("precheck_status") or (precheck_entry or {}).get("status")
    if critical_unacked > 0 or precheck_status == "blocked":
        state = "blocked"
    elif warning_unacked > 0 or precheck_status == "watch_only" or mode == "reference_only":
        state = "cautious"
    else:
        state = "normal"

    constraints = []
    if mode == "reference_only":
        constraints.append("当前系统还没接入真实 open positions，买卖结论按持仓参照层推演，适合作为老板人工判断参考。")
    else:
        constraints.append(f"当前真实持仓总暴露约 {exposure_pct * 100:.2f}%，距离上限还剩 {headroom_pct * 100:.2f}%。")

    if critical_unacked > 0:
        constraints.append(f"当前还有 {critical_unacked} 条未确认的 critical 风险预警，新增风险应暂停。")
    elif warning_unacked > 0:
        constraints.append(f"当前还有 {warning_unacked} 条未确认的 warning 风险预警，买入侧需要降速。")
    else:
        constraints.append("当前没有未确认风险预警。")

    if precheck_status == "blocked":
        constraints.append("执行前检查仍是阻塞状态，说明至少有一组动作还过不了正式门禁。")
    elif precheck_status == "watch_only":
        constraints.append("执行前检查仍是仅观察状态，适合先做跟踪，不适合直接重仓推进。")
    elif precheck_status == "ready":
        constraints.append("执行前检查显示已有可推进方案，但仍要逐票看买入赔率和卖出优先级。")

    if mode == "reference_only" and reference_holdings:
        constraints.append(f"当前参照持仓共 {len(reference_holdings)} 只，系统更适合做换仓优化，不适合解释成净加仓。")

    if state == "blocked":
        buy_call = "暂停新增风险，先处理组合阻塞项和风险预警。"
    elif state == "cautious":
        buy_call = "买入侧只适合小仓试单或继续观察，不适合追高和多线扩张。"
    else:
        buy_call = "可以买，但只推进通过门禁且赔率仍然合适的标的。"

    return {
        "mode": mode,
        "state": state,
        "state_label": PORTFOLIO_STATE_LABELS[state],
        "buy_call": buy_call,
        "sell_call": "当前先看卖出优先级，再决定进攻节奏。",
        "critical_unacked": critical_unacked,
        "warning_unacked": warning_unacked,
        "precheck_status": precheck_status,
        "exposure_pct": exposure_pct,
        "headroom_pct": headroom_pct,
        "constraints": ordered_unique(constraints),
        "decision_policy": decision_policy,
        "risk_payload": risk_payload,
        "precheck_payload": precheck_payload,
    }


def build_strategy_map(strategy_payload):
    items = strategy_payload.get("items") or []
    return {item.get("ts_code"): item for item in items if item.get("ts_code")}


def gate_status_score(gate_status):
    return {"ready": 15, "watch_only": 2, "blocked": -30}.get(gate_status, 0)


def action_type_score(action_type):
    return {
        "swap_ready": 8,
        "swap_watch": 2,
        "opportunity_followup": 3,
    }.get(action_type, 0)


def build_buy_candidate(action, strategy_item, portfolio_ctx, policy):
    decision_policy = portfolio_ctx["decision_policy"]
    gate_status = action.get("gate_status") or "blocked"
    action_type = action.get("action_type") or ""
    priority = action.get("priority") or "low"
    item = strategy_item or {}

    score = 50.0
    why = []
    risks = []
    next_checks = list(action.get("next_checks") or [])

    score += gate_status_score(gate_status)
    if gate_status == "ready":
        why.append("当前门禁已经通过，可以讨论执行节奏。")
    elif gate_status == "watch_only":
        risks.append("当前只能按观察单理解，还不能当成正式开仓。")
    else:
        risks.append("当前门禁未通过，不能把它当成可直接买入的对象。")

    score += action_type_score(action_type)
    score += PRIORITY_BUY_SCORE.get(priority, 0)

    objective_view = item.get("objective_view")
    trend_label = label_from_nested(item, "trend_label", "trend_state")
    valuation_label = label_from_nested(item, "valuation_label", "valuation_pressure")
    research_label = label_from_nested(item, "research_label", "research_staleness")
    official_freshness = (item.get("official_material") or {}).get("freshness_label")
    transcript_freshness = (item.get("public_transcript") or {}).get("freshness_label")
    public_signal = (item.get("public_analyst_signal") or {}).get("stance_label")
    latest_pct_chg = safe_float(item.get("latest_pct_chg"))

    score += OBJECTIVE_BUY_SCORE.get(objective_view, 0)
    score += TREND_BUY_SCORE.get(trend_label, 0)
    score += VALUATION_BUY_SCORE.get(valuation_label, 0)
    score += RESEARCH_BUY_SCORE.get(research_label, 0)
    score += FRESHNESS_BUY_SCORE.get(official_freshness, 0)
    score += FRESHNESS_BUY_SCORE.get(transcript_freshness, 0)
    score += PUBLIC_SIGNAL_BUY_SCORE.get(public_signal, 0)

    if objective_view in {"trend_follow", "trend_positive"}:
        why.append("客观看法仍偏正，说明这只票还处在可以研究买点的阶段。")
    if research_label in {"stale", "missing"}:
        risks.append("研究锚点偏旧，买入前要补最新公告、电话会或一手材料。")
    if valuation_label == "high":
        risks.append("估值压力偏高，不能把情绪抬估值直接当成安全垫。")
    if official_freshness in {"missing", "stale"}:
        risks.append("缺少足够新的官方一手材料，建议先补原文再拍板。")

    chase_threshold = float(decision_policy.get("chase_pct_threshold") or 8.0)
    pullback_threshold = float(decision_policy.get("pullback_pct_threshold") or -5.0)
    if latest_pct_chg is not None and latest_pct_chg >= chase_threshold:
        score -= 6
        risks.append("短线涨幅已经偏快，更适合等回踩确认，不适合追高。")
    elif latest_pct_chg is not None and latest_pct_chg <= pullback_threshold and objective_view in {"trend_follow", "trend_positive"}:
        score += 2
        why.append("最近已经出现一定回踩，买点比直接追涨更友好。")

    risk_flags = list(action.get("risk_flags") or [])
    score -= min(12, len(risk_flags) * 4)
    if portfolio_ctx["state"] == "cautious":
        score -= 4
    if portfolio_ctx["state"] == "blocked":
        score -= 20
        risks.append("组合层当前已经进入暂停新增风险状态。")

    score = round(score, 1)

    verdict = "block"
    if portfolio_ctx["state"] != "blocked" and gate_status == "ready" and score >= float(decision_policy.get("buy_score_strong") or 75):
        verdict = "buy"
    elif portfolio_ctx["state"] != "blocked" and gate_status == "ready" and score >= float(decision_policy.get("buy_score_probe") or 62):
        verdict = "buy_small"
    elif portfolio_ctx["state"] != "blocked" and gate_status in {"ready", "watch_only"} and score >= float(decision_policy.get("buy_score_watch") or 52):
        verdict = "watch"

    if portfolio_ctx["state"] == "cautious" and verdict == "buy":
        verdict = "buy_small"

    default_tranche_pct = float(decision_policy.get("default_buy_tranche_pct") or 0.08)
    cautious_tranche_pct = float(decision_policy.get("cautious_buy_tranche_pct") or 0.04)
    action_trade_amount_pct = safe_float(action.get("trade_amount_pct"))
    suggested_tranche_pct = None
    if verdict == "buy":
        suggested_tranche_pct = min(action_trade_amount_pct or default_tranche_pct, default_tranche_pct)
    elif verdict == "buy_small":
        suggested_tranche_pct = min(action_trade_amount_pct or cautious_tranche_pct, cautious_tranche_pct)

    rationale = ordered_unique([*(action.get("rationale") or []), *why])
    risk_rows = ordered_unique([*risk_flags, *risks])
    next_rows = ordered_unique(next_checks + (item.get("next_check_items") or []))

    summary = {
        "buy": "门禁通过且赔率仍然合适，可以进入老板人工确认的买入清单。",
        "buy_small": "方向没问题，但更适合先用小仓试单，不要一把打满。",
        "watch": "先跟踪，不急着下结论。",
        "block": "当前不适合买入。",
    }[verdict]

    source_refs = ordered_unique(
        [
            *(action.get("source_refs") or []),
            ((item.get("external_research") or {}).get("source_rel_path")),
            ((item.get("public_transcript") or {}).get("source_rel_path")),
            ((item.get("public_analyst_signal") or {}).get("source_rel_path")),
            *(((item.get("official_material") or {}).get("source_rel_paths")) or [])[:3],
        ]
    )

    return {
        "ts_code": ((action.get("add") or {}).get("ts_code")) or item.get("ts_code"),
        "name": ((action.get("add") or {}).get("name")) or item.get("name"),
        "sector": ((action.get("add") or {}).get("sector")) or item.get("sector"),
        "trade_role": action_type,
        "linked_remove": action.get("remove"),
        "gate_status": gate_status,
        "priority": priority,
        "score": score,
        "verdict": verdict,
        "verdict_label": BUY_VERDICT_LABELS[verdict],
        "trade_amount": safe_float(action.get("trade_amount")),
        "trade_amount_pct": action_trade_amount_pct,
        "suggested_tranche_pct": round(suggested_tranche_pct, 6) if suggested_tranche_pct is not None else None,
        "summary": summary,
        "why": rationale[:4],
        "risks": risk_rows[:4],
        "next_checks": next_rows[:4],
        "source_refs": source_refs[:6],
    }


def choose_primary_remove_action(actions):
    if not actions:
        return None

    def sort_key(item):
        gate_status = item.get("gate_status") or "blocked"
        priority = item.get("priority") or "low"
        return (
            {"ready": 3, "watch_only": 2, "blocked": 1}.get(gate_status, 0),
            {"high": 3, "medium": 2, "low": 1}.get(priority, 0),
        )

    return sorted(actions, key=sort_key, reverse=True)[0]


def build_sell_candidate(ts_code, strategy_item, live_position, remove_actions, holding_action, alerts, portfolio_ctx, policy):
    decision_policy = portfolio_ctx["decision_policy"]
    item = strategy_item or {}
    score = 0.0
    why = []
    risks = []
    next_checks = []
    source_refs = []

    primary_remove_action = choose_primary_remove_action(remove_actions)
    if primary_remove_action is not None:
        gate_status = primary_remove_action.get("gate_status") or "blocked"
        score += {"ready": 26, "watch_only": 14, "blocked": 6}.get(gate_status, 0)
        why.append("系统当前已经把它放进调出腿候选，说明有更强的替代对象在排队。")
        next_checks.extend(primary_remove_action.get("next_checks") or [])
        source_refs.extend(primary_remove_action.get("source_refs") or [])
        linked_buy = primary_remove_action.get("add")
    else:
        linked_buy = None

    if holding_action is not None:
        score += {"high": 18, "medium": 10, "low": 4}.get(holding_action.get("priority") or "low", 0)
        why.append("这只票已经进入持仓复核视角，需要重新判断是否继续拿。")
        next_checks.extend(holding_action.get("next_checks") or [])
        source_refs.extend(holding_action.get("source_refs") or [])

    objective_view = item.get("objective_view")
    trend_label = label_from_nested(item, "trend_label", "trend_state")
    valuation_label = label_from_nested(item, "valuation_label", "valuation_pressure")
    research_label = label_from_nested(item, "research_label", "research_staleness")
    public_signal = (item.get("public_analyst_signal") or {}).get("stance_label")
    latest_pct_chg = safe_float(item.get("latest_pct_chg"))

    score += OBJECTIVE_SELL_SCORE.get(objective_view, 0)
    score += TREND_SELL_SCORE.get(trend_label, 0)
    score += VALUATION_SELL_SCORE.get(valuation_label, 0)
    score += RESEARCH_SELL_SCORE.get(research_label, 0)
    score += PUBLIC_SIGNAL_SELL_SCORE.get(public_signal, 0)

    if objective_view == "repair_needed":
        why.append("客观看法已经进入等待修复，不适合继续把它当核心持仓。")
    elif objective_view == "observe":
        why.append("客观看法降到观察级别，持仓耐心要比之前更低。")
    if valuation_label == "high":
        risks.append("估值压力偏高，后面一旦兑现不及预期，回撤会更难受。")
    if research_label in {"stale", "missing"}:
        risks.append("研究锚点偏旧，如果继续拿，需要先补新的事实材料。")

    critical_alerts = sum(1 for item in alerts if item.get("severity") == "critical" and not item.get("acknowledged"))
    warning_alerts = sum(1 for item in alerts if item.get("severity") == "warning" and not item.get("acknowledged"))
    score += critical_alerts * 30 + warning_alerts * 10
    if critical_alerts:
        why.append("已经出现未确认的 critical 风险预警，这种情况下卖出优先级必须往前提。")
    elif warning_alerts:
        why.append("已经出现未确认的 warning 风险预警，至少要先降一档乐观程度。")

    pullback_threshold = abs(float(decision_policy.get("pullback_pct_threshold") or -5.0))
    take_profit_threshold = float(decision_policy.get("take_profit_pct_threshold") or 10.0)
    if latest_pct_chg is not None and latest_pct_chg <= -pullback_threshold:
        score += 10
        why.append("最近已经明显走弱，继续拿的容错率在下降。")
    if latest_pct_chg is not None and latest_pct_chg >= take_profit_threshold and valuation_label == "high":
        score += 8
        why.append("短线涨幅已经很大且估值压力高，减仓兑现会比继续贪更稳。")

    force_sell = False
    if live_position is not None:
        current_price = safe_float(live_position.get("current_price"))
        stop_loss = safe_float(live_position.get("stop_loss"))
        target_price = safe_float(live_position.get("target_price"))
        pnl_pct = safe_float(live_position.get("pnl_pct"))

        if stop_loss is not None and current_price is not None and current_price <= stop_loss:
            score = max(score, 100)
            force_sell = True
            why.append("当前价格已经打到止损线，应该优先执行卖出而不是继续等。")
        if target_price is not None and current_price is not None and current_price >= target_price:
            score += 28
            why.append("当前价格已经到目标位，适合先做分批兑现。")
        if pnl_pct is not None and pnl_pct <= -(float(policy["warning_drawdown_pct"]) * 100):
            score += 18
            why.append("当前回撤已经进入预警区，需要先尊重风控纪律。")
        if not live_position.get("thesis"):
            score += 35
            why.append("系统里没有记录这笔真实持仓的 thesis，继续拿没有足够依据。")

    score = round(score, 1)

    verdict = "hold"
    if force_sell or score >= float(decision_policy.get("sell_score_exit") or 60):
        verdict = "sell"
    elif score >= float(decision_policy.get("sell_score_trim") or 35):
        verdict = "trim"
    elif score >= float(decision_policy.get("sell_score_watch") or 18):
        verdict = "watch"

    if not why and verdict == "hold":
        why.append("当前没有足够强的卖出证据，先维持跟踪。")

    summary = {
        "sell": "卖出优先级已经足够高，应该先处理风险，再谈进攻。",
        "trim": "还没到必须清仓，但更适合先做减仓或降权。",
        "watch": "先盯紧，不急着做大动作。",
        "hold": "当前没有足够强的卖出信号。",
    }[verdict]

    source_refs = ordered_unique(
        [
            *source_refs,
            ((item.get("external_research") or {}).get("source_rel_path")),
            ((item.get("public_transcript") or {}).get("source_rel_path")),
            ((item.get("public_analyst_signal") or {}).get("source_rel_path")),
            *(((item.get("official_material") or {}).get("source_rel_paths")) or [])[:3],
        ]
    )
    next_rows = ordered_unique(next_checks + (item.get("next_check_items") or []))
    replacement_risks = [
        f"如果换到替代腿，还要注意：{text}" for text in ((primary_remove_action or {}).get("risk_flags") or [])[:2]
    ]
    risk_rows = ordered_unique(
        [
            *replacement_risks,
            *(((holding_action or {}).get("risk_flags")) or []),
            *(alert.get("message") for alert in alerts[:2]),
            *risks,
        ]
    )

    return {
        "ts_code": ts_code,
        "name": item.get("name") or (live_position or {}).get("ts_code") or ts_code,
        "sector": item.get("sector"),
        "linked_buy": linked_buy,
        "score": score,
        "verdict": verdict,
        "verdict_label": SELL_VERDICT_LABELS[verdict],
        "summary": summary,
        "why": ordered_unique(why)[:4],
        "risks": risk_rows[:4],
        "next_checks": next_rows[:4],
        "source_refs": source_refs[:6],
    }


def build_buy_candidates(action_payload, strategy_map, portfolio_ctx, policy):
    by_code = {}
    for action in action_payload.get("actions") or []:
        add_leg = action.get("add") or {}
        ts_code = add_leg.get("ts_code")
        if not ts_code:
            continue
        candidate = build_buy_candidate(action, strategy_map.get(ts_code) or {}, portfolio_ctx, policy)
        existing = by_code.get(ts_code)
        if existing is None or candidate["score"] > existing["score"]:
            by_code[ts_code] = candidate
    return sorted(
        by_code.values(),
        key=lambda item: (-BUY_PRIORITY_RANK.get(item["verdict"], 0), -item["score"], item["ts_code"] or ""),
    )


def build_sell_candidates(conn, action_payload, strategy_payload, strategy_map, portfolio_ctx, policy):
    live_positions = load_live_position_map(conn)
    reference_holdings = load_reference_holdings(conn)

    remove_actions = {}
    holding_actions = {}
    for action in action_payload.get("actions") or []:
        remove_leg = action.get("remove") or {}
        remove_code = remove_leg.get("ts_code")
        if remove_code:
            remove_actions.setdefault(remove_code, []).append(action)
        subject = action.get("subject") or {}
        subject_code = subject.get("ts_code")
        if subject_code and action.get("action_type") == "holding_watch":
            holding_actions[subject_code] = action

    tracked_codes = set(live_positions)
    tracked_codes.update(item.get("ts_code") for item in reference_holdings if item.get("ts_code"))
    tracked_codes.update(remove_actions)
    tracked_codes.update(holding_actions)
    alerts_by_symbol = recent_alerts_by_symbol(conn, sorted(tracked_codes))

    candidates = []
    for ts_code in sorted(tracked_codes):
        strategy_item = strategy_map.get(ts_code) or {}
        candidate = build_sell_candidate(
            ts_code,
            strategy_item,
            live_positions.get(ts_code),
            remove_actions.get(ts_code) or [],
            holding_actions.get(ts_code),
            alerts_by_symbol.get(ts_code) or [],
            portfolio_ctx,
            policy,
        )
        candidates.append(candidate)

    return sorted(
        candidates,
        key=lambda item: (-SELL_PRIORITY_RANK.get(item["verdict"], 0), -item["score"], item["ts_code"] or ""),
    )


def headline_actions(portfolio_ctx, buy_candidates, sell_candidates):
    rows = []
    top_sell = [item for item in sell_candidates if item.get("verdict") in {"sell", "trim"}][:2]
    top_buy = [item for item in buy_candidates if item.get("verdict") in {"buy", "buy_small"}][:2]

    if top_sell:
        rows.append("先处理卖出侧：" + "、".join(f"{item['name']}（{item['verdict_label']}）" for item in top_sell))
    if top_buy:
        rows.append("买入侧只看：" + "、".join(f"{item['name']}（{item['verdict_label']}）" for item in top_buy))
    if not rows:
        rows.append("当前更适合观察，不急着扩大风险暴露。")

    return rows[:3]


def sell_call_from_candidates(sell_candidates):
    top = sell_candidates[0] if sell_candidates else None
    if not top:
        return "当前没有需要优先处理的卖出对象。"
    verdict = top.get("verdict")
    if verdict == "sell":
        return "卖出侧已经出现高优先级对象，应先处理风险，再决定新的买入。"
    if verdict == "trim":
        return "卖出侧已有减仓对象，更适合先降风险后加仓。"
    if verdict == "watch":
        return "卖出侧以复核观察为主，暂时没有强制退出。"
    return "当前卖出侧没有明显强制动作。"


def render_markdown(created_at, decision_date, portfolio_ctx, buy_candidates, sell_candidates, relationships):
    lines = [
        "# SMR 买卖决策风控",
        "",
        f"- created_at: `{created_at}`",
        f"- decision_date: `{decision_date}`",
        f"- portfolio_mode: `{portfolio_ctx['mode']}`",
        f"- portfolio_state: `{portfolio_ctx['state']}`",
        "",
        "## 总体结论",
        "",
        f"- 组合状态：{portfolio_ctx['state_label']}",
        f"- 买入侧结论：{portfolio_ctx['buy_call']}",
        f"- 卖出侧结论：{portfolio_ctx['sell_call']}",
        "",
        "## 组合闸门",
        "",
    ]
    for item in portfolio_ctx["constraints"]:
        lines.append(f"- {item}")

    lines.extend(["", "## 买入侧", ""])
    if not buy_candidates:
        lines.append("- 当前没有可评估的买入候选。")
    else:
        for index, item in enumerate(buy_candidates[:5], start=1):
            linked_remove = item.get("linked_remove") or {}
            tranche = item.get("suggested_tranche_pct")
            lines.extend(
                [
                    f"### {index}. {item['name']}（{item['ts_code']}）",
                    "",
                    f"- 结论：{item['verdict_label']} / score={item['score']}",
                    f"- 动作类型：{display_label(item.get('trade_role'))}",
                    f"- 门禁状态：{display_label(item.get('gate_status'))}",
                    f"- 建议仓位：{f'{tranche * 100:.2f}%' if tranche is not None else '-'}",
                    f"- 对应调出腿：{linked_remove.get('name') or linked_remove.get('ts_code') or '-'}",
                    f"- 摘要：{item['summary']}",
                    "- 支撑理由：",
                ]
            )
            for reason in item.get("why") or ["当前没有额外支撑理由。"]:
                lines.append(f"  - {reason}")
            lines.append("- 主要风险：")
            for risk in item.get("risks") or ["当前没有额外风险提示。"]:
                lines.append(f"  - {risk}")
            lines.append("- 下单前再看：")
            for check in item.get("next_checks") or ["当前没有额外检查项。"]:
                lines.append(f"  - {check}")

    lines.extend(["", "## 卖出侧", ""])
    if not sell_candidates:
        lines.append("- 当前没有可评估的卖出候选。")
    else:
        for index, item in enumerate(sell_candidates[:6], start=1):
            linked_buy = item.get("linked_buy") or {}
            lines.extend(
                [
                    f"### {index}. {item['name']}（{item['ts_code']}）",
                    "",
                    f"- 结论：{item['verdict_label']} / score={item['score']}",
                    f"- 对应替代腿：{linked_buy.get('name') or linked_buy.get('ts_code') or '-'}",
                    f"- 摘要：{item['summary']}",
                    "- 为什么：",
                ]
            )
            for reason in item.get("why") or ["当前没有额外卖出理由。"]:
                lines.append(f"  - {reason}")
            lines.append("- 风险与提醒：")
            for risk in item.get("risks") or ["当前没有额外风险提示。"]:
                lines.append(f"  - {risk}")
            lines.append("- 继续核对：")
            for check in item.get("next_checks") or ["当前没有额外检查项。"]:
                lines.append(f"  - {check}")

    lines.extend(
        [
            "",
            "## 文件入口",
            "",
            f"- action_memo_rel_path: `{relationships.get('action_memo_rel_path') or '-'}`",
            f"- strategy_watch_rel_path: `{relationships.get('strategy_watch_rel_path') or '-'}`",
            f"- risk_snapshot_rel_path: `{relationships.get('risk_snapshot_rel_path') or '-'}`",
            f"- execution_precheck_rel_path: `{relationships.get('execution_precheck_rel_path') or '-'}`",
        ]
    )
    return "\n".join(lines) + "\n"


def build_trade_risk_snapshot(conn, entity_id=None, created_at=None):
    created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    policy = load_portfolio_policy()
    action_entry = load_snapshot_entry(conn, "portfolio_action_memo_snapshot", entity_id, required=True)
    decision_date = action_entry.get("entity_id")
    strategy_entry = load_snapshot_entry(conn, "strategy_watch_batch", decision_date, required=False)
    risk_entry = load_snapshot_entry(conn, "risk_monitor_snapshot", decision_date, required=False)
    precheck_entry = load_snapshot_entry(conn, "execution_precheck_snapshot", decision_date, required=False)

    action_payload = action_entry.get("payload", {}) or {}
    strategy_payload = (strategy_entry or {}).get("payload", {}) or {}
    strategy_map = build_strategy_map(strategy_payload)

    live_positions = load_live_position_map(conn)
    reference_holdings = load_reference_holdings(conn)
    portfolio_ctx = portfolio_context(conn, policy, risk_entry, precheck_entry, live_positions, reference_holdings)

    buy_candidates = build_buy_candidates(action_payload, strategy_map, portfolio_ctx, policy)
    sell_candidates = build_sell_candidates(conn, action_payload, strategy_payload, strategy_map, portfolio_ctx, policy)
    portfolio_ctx["sell_call"] = sell_call_from_candidates(sell_candidates)
    headlines = headline_actions(portfolio_ctx, buy_candidates, sell_candidates)

    relationships = {
        "summary_rel_path": None,
        "action_memo_rel_path": ((action_entry.get("relationships", {}) or {}).get("summary_rel_path"))
        or action_payload.get("summary_rel_path"),
        "strategy_watch_rel_path": ((strategy_entry or {}).get("relationships", {}) or {}).get("summary_rel_path")
        or strategy_payload.get("summary_rel_path"),
        "risk_snapshot_rel_path": ((risk_entry or {}).get("relationships", {}) or {}).get("alert_file_rel_path")
        or ((risk_entry or {}).get("relationships", {}) or {}).get("observation_file_rel_path")
        or ((risk_entry or {}).get("payload", {}) or {}).get("alert_file_rel_path")
        or ((risk_entry or {}).get("payload", {}) or {}).get("observation_file_rel_path"),
        "execution_precheck_rel_path": ((precheck_entry or {}).get("relationships", {}) or {}).get("summary_rel_path")
        or ((precheck_entry or {}).get("payload", {}) or {}).get("summary_rel_path"),
        "action_entry_id": action_entry.get("id"),
        "strategy_entry_id": (strategy_entry or {}).get("id"),
        "risk_entry_id": (risk_entry or {}).get("id"),
        "precheck_entry_id": (precheck_entry or {}).get("id"),
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{decision_date}_trade_risk_decision.md"
    relationships["summary_rel_path"] = relative_to_project(output_path)
    output_path.write_text(
        render_markdown(created_at, decision_date, portfolio_ctx, buy_candidates, sell_candidates, relationships),
        encoding="utf-8",
    )

    payload = {
        "portfolio_mode": portfolio_ctx["mode"],
        "portfolio_state": portfolio_ctx["state"],
        "portfolio_state_label": portfolio_ctx["state_label"],
        "portfolio_buy_call": portfolio_ctx["buy_call"],
        "portfolio_sell_call": portfolio_ctx["sell_call"],
        "portfolio_exposure_pct": portfolio_ctx["exposure_pct"],
        "portfolio_headroom_pct": portfolio_ctx["headroom_pct"],
        "critical_unacknowledged_alert_count": portfolio_ctx["critical_unacked"],
        "warning_unacknowledged_alert_count": portfolio_ctx["warning_unacked"],
        "precheck_status": portfolio_ctx["precheck_status"],
        "portfolio_constraints": portfolio_ctx["constraints"],
        "headline_actions": headlines,
        "buy_candidate_count": len(buy_candidates),
        "sell_candidate_count": len(sell_candidates),
        "buy_candidates": buy_candidates[:6],
        "sell_candidates": sell_candidates[:6],
        "summary_rel_path": relationships["summary_rel_path"],
    }
    entry = register_snapshot(
        conn,
        entity_type="trade_risk_decision_snapshot",
        entity_id=decision_date,
        status=portfolio_ctx["state"],
        source="build_trade_risk_decision_snapshot.py",
        relationships=relationships,
        payload=payload,
        created_at=created_at,
    )
    return {
        "entry": entry,
        "output_path": output_path,
        "payload": payload,
        "relationships": relationships,
    }


def main():
    parser = argparse.ArgumentParser(description="Build boss-facing trade risk decision snapshot")
    parser.add_argument("--date", help="Prefer this entity_id date")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    result = build_trade_risk_snapshot(conn, args.date)
    conn.commit()
    conn.close()

    payload = result["payload"]
    log_run(
        "build_trade_risk_decision_snapshot.py",
        "success",
        "trade risk decision snapshot built",
        {
            "entity_id": result["entry"]["entity_id"],
            "portfolio_state": payload.get("portfolio_state"),
            "buy_candidate_count": payload.get("buy_candidate_count"),
            "sell_candidate_count": payload.get("sell_candidate_count"),
            "summary_rel_path": relative_to_project(result["output_path"]),
        },
    )
    print(f"Trade risk decision built: {result['entry']['entity_id']}")
    print(f"Portfolio state: {payload.get('portfolio_state')}")
    print(f"Buy candidates: {payload.get('buy_candidate_count')}")
    print(f"Sell candidates: {payload.get('sell_candidate_count')}")
    print(f"Summary file: {result['output_path']}")


if __name__ == "__main__":
    main()
