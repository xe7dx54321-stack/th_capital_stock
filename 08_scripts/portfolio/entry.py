#!/usr/bin/env python3
"""SMR Portfolio Entry - Record a new position with recommendation and risk gates."""

import argparse
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_paths import env_or_project_path
from smr_portfolio import (
    has_unacknowledged_critical_alert,
    latest_recommendation,
    load_portfolio_policy,
    projected_costs_by_sector,
    projected_total_cost,
    recommended_in_current_pool,
    resolve_sector,
)
from smr_runlog import log_run

DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")
POSITIONS_DIR = env_or_project_path("SMR_POSITIONS_DIR", "04_portfolio", "positions")


def format_pct(value):
    return f"{value * 100:.1f}%"


def main():
    parser = argparse.ArgumentParser(description="Record a new SMR position with portfolio gates")
    parser.add_argument("--ts-code", required=True, help="Stock code e.g. 300308.SZ")
    parser.add_argument("--entry-price", required=True, type=float, help="Entry price")
    parser.add_argument("--shares", required=True, type=int, help="Number of shares")
    parser.add_argument("--target-price", required=True, type=float, help="Target price")
    parser.add_argument("--stop-loss", required=True, type=float, help="Stop loss price")
    parser.add_argument("--thesis", required=True, help="Investment thesis")
    parser.add_argument("--source-report-id", help="Recommendation report id to bind this entry")
    parser.add_argument("--confirm-recommendation", action="store_true", help="Explicitly confirm this entry comes from an approved recommendation")
    parser.add_argument("--dry-run", action="store_true", help="Validate gates without writing a position")
    args = parser.parse_args()

    if args.entry_price <= 0 or args.shares <= 0:
        raise SystemExit("entry-price and shares must be positive")
    if args.stop_loss >= args.entry_price:
        raise SystemExit("stop-loss must be below entry-price for a long position")
    if args.target_price <= args.entry_price:
        raise SystemExit("target-price must be above entry-price for a long position")
    if not args.confirm_recommendation:
        raise SystemExit("Must pass --confirm-recommendation before recording a live entry")

    entry_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry_date = entry_time[:10]
    cost = round(args.entry_price * args.shares, 2)

    conn = sqlite3.connect(DB_PATH)
    policy = load_portfolio_policy()

    if has_unacknowledged_critical_alert(conn):
        raise SystemExit("Cannot open a new position while unacknowledged critical risk alerts exist")

    recommendation = latest_recommendation(conn, args.ts_code)
    if not recommendation or not recommended_in_current_pool(conn, args.ts_code):
        raise SystemExit(f"{args.ts_code} is not currently in the recommended pool")

    if args.source_report_id and args.source_report_id != recommendation["report_id"]:
        raise SystemExit(
            f"source-report-id mismatch: expected {recommendation['report_id']}, got {args.source_report_id}"
        )

    sector = resolve_sector(conn, args.ts_code)
    portfolio_capital = float(policy["portfolio_capital"])
    projected_total = projected_total_cost(conn, extra_cost=cost)
    projected_total_pct = projected_total / portfolio_capital
    single_position_pct = cost / portfolio_capital
    sector_costs = projected_costs_by_sector(conn, extra_ts_code=args.ts_code, extra_cost=cost)
    sector_pct = sector_costs.get(sector or "unknown", 0.0) / portfolio_capital

    if projected_total_pct > policy["max_total_exposure_pct"]:
        raise SystemExit(
            f"Projected total exposure {format_pct(projected_total_pct)} exceeds limit {format_pct(policy['max_total_exposure_pct'])}"
        )
    if single_position_pct > policy["max_single_position_pct"]:
        raise SystemExit(
            f"Projected single-position exposure {format_pct(single_position_pct)} exceeds limit {format_pct(policy['max_single_position_pct'])}"
        )
    if sector_pct > policy["max_sector_concentration_pct"]:
        raise SystemExit(
            f"Projected sector exposure {format_pct(sector_pct)} exceeds limit {format_pct(policy['max_sector_concentration_pct'])}"
        )

    summary_lines = [
        f"ts_code={args.ts_code}",
        f"source_report_id={recommendation['report_id']}",
        f"sector={sector}",
        f"cost={cost:.2f}",
        f"single_position_pct={format_pct(single_position_pct)}",
        f"sector_pct={format_pct(sector_pct)}",
        f"total_exposure_pct={format_pct(projected_total_pct)}",
    ]

    if args.dry_run:
        conn.close()
        log_run(
            "entry.py",
            "success",
            "entry gate dry-run pass",
            {
                "ts_code": args.ts_code,
                "source_report_id": recommendation["report_id"],
                "cost": cost,
                "single_position_pct": round(single_position_pct, 6),
                "sector_pct": round(sector_pct, 6),
                "total_exposure_pct": round(projected_total_pct, 6),
                "dry_run": True,
            },
        )
        print("Entry gate check PASS")
        for line in summary_lines:
            print(f"  {line}")
        return

    conn.execute(
        """
        INSERT INTO position
        (ts_code, entry_date, entry_price, shares, cost, target_price, stop_loss, thesis, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'open')
        """,
        (args.ts_code, entry_date, args.entry_price, args.shares, cost, args.target_price, args.stop_loss, args.thesis),
    )
    conn.commit()
    conn.close()

    POSITIONS_DIR.mkdir(parents=True, exist_ok=True)
    pos_file = POSITIONS_DIR / f"{args.ts_code.replace('.', '_')}_{entry_date}.md"
    with open(pos_file, "w", encoding="utf-8") as f:
        f.write(f"# Position: {args.ts_code}\n\n")
        f.write(f"- Entry Time: {entry_time}\n")
        f.write(f"- Entry Price: {args.entry_price}\n")
        f.write(f"- Shares: {args.shares}\n")
        f.write(f"- Cost: {cost}\n")
        f.write(f"- Target Price: {args.target_price}\n")
        f.write(f"- Stop Loss: {args.stop_loss}\n")
        f.write(f"- Thesis: {args.thesis}\n")
        f.write(f"- Recommendation Report: {recommendation['report_id']}\n")
        f.write(f"- Thesis Strength: {recommendation.get('thesis_strength') or 'N/A'}\n")
        f.write(f"- Sector: {sector or 'N/A'}\n")
        f.write(f"- Single Position Pct: {format_pct(single_position_pct)}\n")
        f.write(f"- Sector Pct: {format_pct(sector_pct)}\n")
        f.write(f"- Total Exposure Pct: {format_pct(projected_total_pct)}\n")

    print(f"Position recorded: {args.ts_code} @ {args.entry_price} x {args.shares}")
    for line in summary_lines:
        print(f"  {line}")
    print(f"File: {pos_file}")

    log_run(
        "entry.py",
        "success",
        "position recorded",
        {
            "ts_code": args.ts_code,
            "source_report_id": recommendation["report_id"],
            "cost": cost,
            "single_position_pct": round(single_position_pct, 6),
            "sector_pct": round(sector_pct, 6),
            "total_exposure_pct": round(projected_total_pct, 6),
            "dry_run": False,
        },
    )


if __name__ == "__main__":
    try:
        main()
    except SystemExit as exc:
        message = str(exc)
        if message:
            log_run("entry.py", "blocked", message, {})
        raise
