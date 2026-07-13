#!/usr/bin/env python3
"""Update lightweight outcome prices for approved/observation recommendations."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_data_health import check_freshness_gate
from smr_decision import ensure_decision_tables
from smr_paper_portfolio import mark_open_positions_to_market
from smr_runlog import log_run

SCRIPT_NAME = "update_decision_outcomes.py"


def relation_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name=?", (name,)).fetchone()
    return bool(row)


def price_on_or_after(conn: sqlite3.Connection, ticker: str, target_date: str, market: str | None) -> float | None:
    table = "us_daily_bar" if market == "US" else "daily_bar"
    if not relation_exists(conn, table):
        return None
    columns = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    ticker_column = "ts_code" if "ts_code" in columns else "symbol"
    row = conn.execute(
        f"SELECT close FROM {table} WHERE {ticker_column}=? AND trade_date>=? ORDER BY trade_date ASC LIMIT 1",
        (ticker, target_date),
    ).fetchone()
    return float(row[0]) if row and row[0] is not None else None


def update_outcomes(conn: sqlite3.Connection, limit: int = 200) -> dict[str, int]:
    ensure_decision_tables(conn)
    gate = check_freshness_gate(conn, "paper_performance", ["daily_bar"], allow_degraded=False)
    if gate.status == "block":
        conn.execute(
            """
            UPDATE decision_ledger
            SET performance_update_status='skipped', performance_update_reason=?, updated_at=?
            WHERE status IN ('approved_paper', 'observation_only')
            """,
            ("daily_bar stale or missing; performance update skipped", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        return {"updated": 0, "skipped": conn.total_changes, **mark_open_positions_to_market(conn)}
    rows = conn.execute(
        """
        SELECT recommendation_id, ticker, market, decision_time, status
        FROM decision_ledger
        WHERE status IN ('approved_paper', 'observation_only')
          AND ticker IS NOT NULL
        ORDER BY datetime(updated_at) DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    updated = 0
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for rec_id, ticker, market, decision_time, _status in rows:
        base = datetime.fromisoformat(str(decision_time)[:19]).date()
        p1d = price_on_or_after(conn, ticker, (base + timedelta(days=1)).isoformat(), market)
        p1w = price_on_or_after(conn, ticker, (base + timedelta(days=7)).isoformat(), market)
        p1m = price_on_or_after(conn, ticker, (base + timedelta(days=30)).isoformat(), market)
        p3m = price_on_or_after(conn, ticker, (base + timedelta(days=90)).isoformat(), market)
        conn.execute(
            """
            UPDATE decision_ledger
            SET outcome_price_1d=?, outcome_price_1w=?, outcome_price_1m=?, outcome_price_3m=?,
                performance_update_status='updated', performance_update_reason=NULL, updated_at=?
            WHERE recommendation_id=?
            """,
            (p1d, p1w, p1m, p3m, now, rec_id),
        )
        updated += 1
    return {"updated": updated, "skipped": 0, **mark_open_positions_to_market(conn)}


def update_thesis_outcome_status(conn: sqlite3.Connection, limit: int = 50) -> dict[str, Any]:
    """根据 outcome_price 与 reference_price 的对比，更新复盘结论字段。

    【功能】
    这是复盘闭环的关键环节：把"价格表现"翻译成"投资逻辑是否被验证"，
    让研究决策能从复盘中学习。具体更新三个字段：
    - thesis_confirmed: 投资逻辑是否被确认（1=确认，0=证伪，不更新=待观察）
    - outcome_status: 决策结果状态（open/confirmed/failed/partially_confirmed）
    - failure_reason: 失败原因（仅在 outcome_status=failed 时填充）

    判定规则（用小白的话术讲解）：
    想象你是一个投资经理，1 个月前推荐了一只股票，现在回头看：
    - 涨了 → 投资逻辑被确认（thesis_confirmed=1）
    - 跌超 10% → 投资逻辑被证伪（thesis_confirmed=0）
    - 涨跌不大 → 先别下结论，继续观察（不更新 thesis_confirmed）
    3 个月后再做一次更严格的"期末考试"（outcome_status）：
    - 涨超 5% → confirmed（确认成功）
    - 跌超 10% → failed（失败），并记录失败原因
    - 介于之间 → partially_confirmed（部分确认）

    【参数】
    - conn: 数据库连接对象（sqlite3.Connection）
    - limit: 一次最多处理多少条记录，默认 50

    【返回值】
    dict，包含：
    - updated: 已更新的记录数（int）
    - skipped: 跳过的记录数（int，数据不足或时间未到）
    - details: 详情列表（list[dict]），每条记录一个 dict，含 recommendation_id、ticker、action 等

    【异常处理】
    - 单条记录处理失败不会中断整个流程，错误信息记录到 details 中
    - 数据库 commit/rollback 由调用方（main 函数）负责
    - reference_price 为空时回退到 outcome_price_1d 作为参考价
    """
    ensure_decision_tables(conn)
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # 查询需要处理的记录：有 1m 或 3m 价格数据的 approved/observation 记录
    rows = conn.execute(
        """
        SELECT recommendation_id, ticker, decision_time, reference_price,
               outcome_price_1d, outcome_price_1m, outcome_price_3m,
               thesis_confirmed, outcome_status
        FROM decision_ledger
        WHERE status IN ('approved_paper', 'observation_only')
          AND (outcome_price_1m IS NOT NULL OR outcome_price_3m IS NOT NULL)
        ORDER BY datetime(decision_time) ASC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    updated = 0
    skipped = 0
    details: list[dict[str, Any]] = []

    for rec_id, ticker, decision_time, reference_price, p1d, p1m, p3m, thesis_confirmed, outcome_status in rows:
        try:
            # 解析决策时间，计算距今天数
            decision_dt = datetime.fromisoformat(str(decision_time)[:19])
            days_since_decision = (now - decision_dt).days

            # 确定参考价：优先用 reference_price，没有则回退到 outcome_price_1d
            # （outcome_price_1d 是决策后第 1 天的收盘价，最接近决策时点）
            ref_price = reference_price if reference_price is not None else p1d
            if ref_price is None or ref_price <= 0:
                # 没有参考价或参考价非正，无法计算收益率，跳过
                skipped += 1
                details.append({
                    "recommendation_id": rec_id,
                    "ticker": ticker,
                    "action": "skipped",
                    "reason": "no valid reference_price or outcome_price_1d",
                })
                continue

            # 收集本次需要更新的字段（只更新有数据支撑的字段，不盲目覆盖）
            updates: dict[str, Any] = {}
            return_rate_3m: float | None = None

            # === 规则 1：thesis_confirmed 判定（基于 1 个月数据）===
            # 条件：outcome_price_1m 有值 且 距决策日满 30 天
            if p1m is not None and days_since_decision >= 30:
                return_rate_1m = (p1m - ref_price) / ref_price
                if return_rate_1m > 0:
                    updates["thesis_confirmed"] = 1
                elif return_rate_1m < -0.1:
                    updates["thesis_confirmed"] = 0
                # 介于 -0.1 和 0 之间：待观察，不更新 thesis_confirmed

            # === 规则 2：outcome_status 判定（基于 3 个月数据）===
            # 条件：outcome_price_3m 有值 且 距决策日满 90 天
            if p3m is not None and days_since_decision >= 90:
                return_rate_3m = (p3m - ref_price) / ref_price
                if return_rate_3m > 0.05:
                    updates["outcome_status"] = "confirmed"
                elif return_rate_3m < -0.1:
                    updates["outcome_status"] = "failed"
                else:
                    updates["outcome_status"] = "partially_confirmed"

                # === 规则 3：failure_reason 判定（仅当 outcome_status=failed）===
                # kill_conditions_json 是定性文本（如"Primary evidence breaks thesis"），
                # 无法用程序自动判定是否被价格触发，故跳过 kill_condition_triggered 规则。
                # 基本面恶化信号也无可用的结构化数据源，跳过 fundamental_deterioration 规则。
                if updates.get("outcome_status") == "failed" and return_rate_3m is not None:
                    if return_rate_3m < -0.1:
                        updates["failure_reason"] = "price_decline_exceeds_10pct"
            # 未满 3 个月：保持 outcome_status = 'open'（仍在观察期）

            # 检查是否有字段需要更新
            if not updates:
                skipped += 1
                details.append({
                    "recommendation_id": rec_id,
                    "ticker": ticker,
                    "action": "skipped",
                    "reason": "no field change (time window not met or data insufficient)",
                    "days_since_decision": days_since_decision,
                })
                continue

            # 执行更新：动态构建 SET 子句，只更新有变化的字段
            set_parts = [f"{field}=?" for field in updates]
            set_parts.append("updated_at=?")
            params = list(updates.values()) + [now_str, rec_id]
            conn.execute(
                f"UPDATE decision_ledger SET {', '.join(set_parts)} WHERE recommendation_id=?",
                params,
            )
            updated += 1
            details.append({
                "recommendation_id": rec_id,
                "ticker": ticker,
                "action": "updated",
                "days_since_decision": days_since_decision,
                "reference_price_used": ref_price,
                "outcome_price_1m": p1m,
                "outcome_price_3m": p3m,
                **updates,
            })
        except Exception as exc:
            # 单条记录处理失败，记录错误但继续处理下一条
            skipped += 1
            details.append({
                "recommendation_id": rec_id,
                "ticker": ticker,
                "action": "error",
                "reason": str(exc),
            })

    return {"updated": updated, "skipped": skipped, "details": details}


def main() -> None:
    parser = argparse.ArgumentParser(description="Update decision outcome prices")
    parser.add_argument("--limit", type=int, default=200)
    args = parser.parse_args()
    conn = sqlite3.connect(DB_PATH)
    try:
        result = update_outcomes(conn, limit=args.limit)
        thesis_result = update_thesis_outcome_status(conn, limit=args.limit)
        conn.commit()
    finally:
        conn.close()
    result["thesis_outcome"] = thesis_result
    log_run(SCRIPT_NAME, "success", "decision outcomes updated", result)
    print(result)


if __name__ == "__main__":
    main()
