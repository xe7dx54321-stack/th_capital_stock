#!/usr/bin/env python3
"""Build lightweight strategy evidence for opportunity radar candidates."""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_paths import env_or_project_path, project_path, relative_to_project
from smr_agents import ensure_auto_handoff
from smr_registry import register_snapshot
from smr_runlog import log_run

DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")
OUTPUT_DIR = env_or_project_path("SMR_OPPORTUNITY_EVIDENCE_DIR", "02_research", "opportunity_evidence")
POLICY_PATH = project_path("00_control", "opportunity_engine_policy.json")
SCRIPT_NAME = "build_strategy_evidence_snapshot.py"


def load_policy() -> dict:
    if not POLICY_PATH.exists():
        return {}
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def safe_float(value, default=None):
    if value in (None, "", "None", "nan", "-", "--"):
        return default
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(number) or math.isinf(number):
        return default
    return number


def pct_return(current, previous):
    current = safe_float(current)
    previous = safe_float(previous)
    if current is None or previous in (None, 0):
        return None
    return current / previous - 1.0


def avg(values):
    rows = [safe_float(value) for value in values if safe_float(value) is not None]
    if not rows:
        return None
    return sum(rows) / len(rows)


def median(values):
    rows = sorted([safe_float(value) for value in values if safe_float(value) is not None])
    if not rows:
        return None
    middle = len(rows) // 2
    if len(rows) % 2:
        return rows[middle]
    return (rows[middle - 1] + rows[middle]) / 2


def latest_registry_snapshot(conn, entity_type, entity_id=None):
    filters = ["entity_type=?"]
    params = [entity_type]
    if entity_id:
        filters.append("entity_id=?")
        params.append(entity_id)
    row = conn.execute(
        f"""
        SELECT id, entity_type, entity_id, status, source, relationships_json, payload_json, created_at
        FROM task_registry_entity_latest
        WHERE {' AND '.join(filters)}
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """,
        params,
    ).fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "entity_type": row[1],
        "entity_id": row[2],
        "status": row[3],
        "source": row[4],
        "relationships": json.loads(row[5] or "{}"),
        "payload": json.loads(row[6] or "{}"),
        "created_at": row[7],
    }


def candidate_items_from_radar(radar_snapshot, limit):
    payload = (radar_snapshot or {}).get("payload") or {}
    rows = []
    for market_items in (payload.get("markets") or {}).values():
        rows.extend(market_items or [])
    if not rows:
        rows = payload.get("top_candidates") or []
    rows.sort(key=lambda item: (-(safe_float(item.get("opportunity_score"), 0.0) or 0.0), item.get("ts_code") or ""))
    return rows[:limit]


def load_history(conn, ts_code, market, limit=180):
    if market == "US":
        rows = conn.execute(
            """
            SELECT trade_date, open, high, low, close, pct_chg, vol, amount
            FROM us_daily_bar
            WHERE symbol=?
            ORDER BY trade_date DESC
            LIMIT ?
            """,
            (ts_code, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT trade_date, open, high, low, close, pct_chg, vol, amount
            FROM daily_bar
            WHERE ts_code=?
            ORDER BY trade_date DESC
            LIMIT ?
            """,
            (ts_code, limit),
        ).fetchall()
    return [dict(row) for row in reversed(rows)]


def rolling_mean(values, end_index, window):
    if end_index + 1 < window:
        return None
    rows = [safe_float(value) for value in values[end_index + 1 - window : end_index + 1]]
    if any(value is None for value in rows):
        return None
    return sum(rows) / len(rows)


def previous_high(highs, end_index, window):
    if end_index < window:
        return None
    rows = [safe_float(value) for value in highs[end_index - window : end_index]]
    rows = [value for value in rows if value is not None]
    return max(rows) if rows else None


def volume_ratio(volumes, end_index, window=20):
    if end_index < window:
        return None
    current = safe_float(volumes[end_index])
    avg_vol = avg(volumes[end_index - window : end_index])
    if current is None or not avg_vol:
        return None
    return current / avg_vol


def iter_strategy_trades(history, strategy_id, hold_days):
    closes = [safe_float(row.get("close")) for row in history]
    highs = [safe_float(row.get("high")) for row in history]
    vols = [safe_float(row.get("vol")) for row in history]
    trades = []
    for idx in range(len(history) - hold_days):
        close = closes[idx]
        future_close = closes[idx + hold_days]
        if close in (None, 0) or future_close is None:
            continue
        ma20 = rolling_mean(closes, idx, 20)
        ma60 = rolling_mean(closes, idx, 60)
        vol_ratio = volume_ratio(vols, idx, 20)
        signal = False
        signal_note = ""
        if strategy_id == "breakout_20d_volume_hold10":
            high_20 = previous_high(highs, idx, 20)
            signal = close is not None and high_20 is not None and close > high_20 and (vol_ratio or 0) >= 1.2
            signal_note = "20日突破+量能确认"
        elif strategy_id == "ma20_ma60_trend_hold20":
            signal = ma20 is not None and ma60 is not None and close > ma20 > ma60
            signal_note = "20/60日均线多头排列"
        elif strategy_id == "pullback_above_ma60_hold10":
            signal = ma20 is not None and ma60 is not None and ma60 < close < ma20
            signal_note = "60日线上方回撤"
        if not signal:
            continue
        ret = future_close / close - 1.0
        trades.append(
            {
                "entry_date": history[idx].get("trade_date"),
                "exit_date": history[idx + hold_days].get("trade_date"),
                "return": ret,
                "signal_note": signal_note,
            }
        )
    return trades


def summarize_trades(trades, strategy_id, hold_days, policy):
    returns = [trade["return"] for trade in trades]
    total = len(returns)
    wins = [value for value in returns if value > 0]
    losses = [value for value in returns if value <= 0]
    avg_return = avg(returns)
    avg_win = avg(wins) or 0.0
    avg_loss = avg(losses) or 0.0
    win_rate = len(wins) / total if total else None
    profit_factor = None
    if losses:
        loss_abs = abs(sum(losses))
        profit_factor = sum(wins) / loss_abs if loss_abs > 0 else None
    elif wins:
        profit_factor = 99.0
    worst_return = min(returns) if returns else None
    best_return = max(returns) if returns else None
    guards = policy.get("risk_guards") or {}
    min_trades = int(guards.get("min_backtest_trades_for_ready") or 8)
    min_win_rate = safe_float(guards.get("min_win_rate_for_ready"), 0.48) or 0.48
    min_avg_return = safe_float(guards.get("min_avg_return_for_ready"), 0.0) or 0.0
    if total < min_trades:
        evidence_label = "thin_sample"
    elif win_rate is not None and avg_return is not None and win_rate >= min_win_rate and avg_return >= min_avg_return:
        evidence_label = "ready_for_paper_watch"
    elif avg_return is not None and avg_return < 0:
        evidence_label = "negative_evidence"
    else:
        evidence_label = "mixed_evidence"
    return {
        "strategy_id": strategy_id,
        "hold_days": hold_days,
        "trade_count": total,
        "win_rate": round(win_rate, 4) if win_rate is not None else None,
        "avg_return": round(avg_return, 4) if avg_return is not None else None,
        "median_return": round(median(returns), 4) if returns else None,
        "avg_win": round(avg_win, 4),
        "avg_loss": round(avg_loss, 4),
        "best_return": round(best_return, 4) if best_return is not None else None,
        "worst_return": round(worst_return, 4) if worst_return is not None else None,
        "profit_factor": round(profit_factor, 2) if profit_factor is not None else None,
        "evidence_label": evidence_label,
        "sample_trades": trades[-5:],
    }


def strategy_specs_for_candidate(candidate):
    tags = set(candidate.get("signal_tags") or [])
    specs = [
        ("breakout_20d_volume_hold10", 10),
        ("ma20_ma60_trend_hold20", 20),
        ("pullback_above_ma60_hold10", 10),
    ]
    if "breakout_with_volume" in tags or "price_volume_acceleration" in tags:
        return specs
    if "trend_continuation" in tags:
        return [("ma20_ma60_trend_hold20", 20), ("breakout_20d_volume_hold10", 10), ("pullback_above_ma60_hold10", 10)]
    if "reversal_probe" in tags:
        return [("pullback_above_ma60_hold10", 10), ("ma20_ma60_trend_hold20", 20), ("breakout_20d_volume_hold10", 10)]
    return specs


def best_summary(summaries):
    def key(item):
        label_rank = {
            "ready_for_paper_watch": 3,
            "mixed_evidence": 2,
            "thin_sample": 1,
            "negative_evidence": 0,
        }.get(item.get("evidence_label"), 0)
        return (
            label_rank,
            item.get("avg_return") if item.get("avg_return") is not None else -99,
            item.get("win_rate") if item.get("win_rate") is not None else -1,
            item.get("trade_count") or 0,
        )
    return sorted(summaries, key=key, reverse=True)[0] if summaries else None


def build_candidate_evidence(conn, candidate, policy):
    ts_code = candidate.get("ts_code")
    market = candidate.get("market") or ("US" if "." not in str(ts_code) else "A")
    history = load_history(conn, ts_code, market)
    summaries = []
    for strategy_id, hold_days in strategy_specs_for_candidate(candidate):
        trades = iter_strategy_trades(history, strategy_id, hold_days)
        summaries.append(summarize_trades(trades, strategy_id, hold_days, policy))
    best = best_summary(summaries)
    return {
        "ts_code": ts_code,
        "name": candidate.get("name") or ts_code,
        "market": market,
        "sector": candidate.get("sector") or "",
        "opportunity_score": candidate.get("opportunity_score"),
        "radar_bucket": candidate.get("radar_bucket"),
        "signal_tags": candidate.get("signal_tags") or [],
        "history_days": len(history),
        "best_evidence": best or {},
        "strategy_summaries": summaries,
    }


def render_pct(value):
    number = safe_float(value)
    if number is None:
        return "-"
    return f"{number:.2%}"


def evidence_overview(items):
    ready = [item for item in items if (item.get("best_evidence") or {}).get("evidence_label") == "ready_for_paper_watch"]
    thin = [item for item in items if (item.get("best_evidence") or {}).get("evidence_label") == "thin_sample"]
    negative = [item for item in items if (item.get("best_evidence") or {}).get("evidence_label") == "negative_evidence"]
    lines = [
        f"本轮对 {len(items)} 个雷达候选做轻量历史验证，{len(ready)} 个达到纸面观察证据门槛。",
        f"样本偏薄 {len(thin)} 个，负证据 {len(negative)} 个；这些不应直接进入组合动作。",
    ]
    if ready:
        top = sorted(
            ready,
            key=lambda item: (
                -((item.get("best_evidence") or {}).get("avg_return") or 0),
                item.get("ts_code") or "",
            ),
        )[0]
        best = top.get("best_evidence") or {}
        lines.append(
            f"当前证据最好的是 {top.get('name')} / {top.get('ts_code')}，"
            f"{best.get('strategy_id')} 平均收益 {render_pct(best.get('avg_return'))}，"
            f"胜率 {render_pct(best.get('win_rate'))}。"
        )
    return lines


def write_markdown(path, payload):
    lines = [
        "# 策略证据快照",
        "",
        f"- generated_at: {payload.get('generated_at')}",
        f"- batch_date: {payload.get('batch_date')}",
        f"- source_radar_entry_id: {payload.get('source_radar_entry_id')}",
        "- mode: paper_only evidence, not execution.",
        "",
        "## 核心结论",
        "",
    ]
    for line in payload.get("overview_lines") or []:
        lines.append(f"- {line}")
    lines.extend(
        [
            "",
            "## 候选证据",
            "",
            "| 标的 | 雷达分 | 最佳策略 | 交易数 | 胜率 | 平均收益 | 最差收益 | 证据标签 |",
            "| --- | ---: | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for item in payload.get("items") or []:
        best = item.get("best_evidence") or {}
        lines.append(
            "| {subject} | {score} | {strategy} | {trades} | {win} | {avg} | {worst} | {label} |".format(
                subject=f"{item.get('name')} / {item.get('ts_code')}",
                score=f"{safe_float(item.get('opportunity_score'), 0.0):.2f}",
                strategy=best.get("strategy_id") or "-",
                trades=best.get("trade_count") or 0,
                win=render_pct(best.get("win_rate")),
                avg=render_pct(best.get("avg_return")),
                worst=render_pct(best.get("worst_return")),
                label=best.get("evidence_label") or "-",
            )
        )
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Build opportunity strategy evidence snapshot")
    parser.add_argument("--date", help="Radar entity date; defaults to latest radar snapshot")
    parser.add_argument("--limit", type=int, default=16, help="Max radar candidates to evaluate")
    args = parser.parse_args()

    policy = load_policy()
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    batch_date = generated_at[:10]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{batch_date}_strategy_evidence_snapshot.md"

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        radar_snapshot = latest_registry_snapshot(conn, "opportunity_radar_snapshot", args.date)
        if not radar_snapshot:
            raise SystemExit("No opportunity_radar_snapshot found. Run build_opportunity_radar_snapshot.py first.")
        candidates = candidate_items_from_radar(radar_snapshot, args.limit)
        items = [build_candidate_evidence(conn, candidate, policy) for candidate in candidates]
        payload = {
            "generated_at": generated_at,
            "batch_date": batch_date,
            "source_radar_entry_id": radar_snapshot["id"],
            "source_radar_entity_id": radar_snapshot["entity_id"],
            "candidate_count": len(items),
            "ready_count": sum(
                1 for item in items if (item.get("best_evidence") or {}).get("evidence_label") == "ready_for_paper_watch"
            ),
            "items": items,
            "policy_rel_path": relative_to_project(POLICY_PATH),
        }
        payload["overview_lines"] = evidence_overview(items)
        write_markdown(output_path, payload)
        registry_entry = register_snapshot(
            conn,
            entity_type="strategy_evidence_snapshot",
            entity_id=batch_date,
            status="generated" if items else "empty",
            source=SCRIPT_NAME,
            relationships={
                "summary_rel_path": relative_to_project(output_path),
                "source_radar_entry_id": radar_snapshot["id"],
                "source_radar_entity_id": radar_snapshot["entity_id"],
            },
            payload={**payload, "summary_rel_path": relative_to_project(output_path)},
            created_at=generated_at,
        )
        handoff_result = ensure_auto_handoff(
            conn,
            registry_entry,
            note="策略证据快照已生成，自动转交研究代理区分纸面观察、样本偏薄和负证据。",
            created_by=SCRIPT_NAME,
        )
        conn.commit()
    finally:
        conn.close()

    log_run(
        SCRIPT_NAME,
        "success",
        "strategy evidence snapshot built",
        {
            "registry_entry_id": registry_entry["id"],
            "summary_rel_path": relative_to_project(output_path),
            "candidate_count": payload["candidate_count"],
            "ready_count": payload["ready_count"],
            "handoff_result": handoff_result["reason"],
            "handoff_id": handoff_result["handoff"]["handoff_id"] if handoff_result["handoff"] else None,
        },
    )
    print(f"Strategy evidence snapshot: {relative_to_project(output_path)}")
    print(f"  candidate_count={payload['candidate_count']}")
    print(f"  ready_count={payload['ready_count']}")


if __name__ == "__main__":
    main()
