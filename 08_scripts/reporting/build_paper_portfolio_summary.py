#!/usr/bin/env python3
"""Build a paper portfolio summary with exposure and stale-price awareness."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_paper_portfolio import ensure_paper_portfolio_tables, is_price_fresh, latest_price_info, mark_open_positions_to_market
from smr_phase6_watchlists import watchlist_map
from smr_paths import project_path
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts


SCRIPT_NAME = "build_paper_portfolio_summary.py"


def loads_json(raw: str | None, fallback: Any) -> Any:
    if raw in (None, ""):
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name=?", (name,)).fetchone()
    return bool(row)


def open_positions(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    if not _table_exists(conn, "paper_portfolio_positions"):
        return []
    rows = conn.execute(
        """
        SELECT position_id, ticker, market, quantity, avg_cost, position_pct, status, opened_at, closed_at,
               source_recommendation_id, metadata_json
        FROM paper_portfolio_positions
        WHERE status='open'
        ORDER BY datetime(opened_at) DESC, id DESC
        """
    ).fetchall()
    return [
        {
            "position_id": row[0],
            "ticker": row[1],
            "market": row[2],
            "quantity": row[3],
            "avg_cost": row[4],
            "position_pct": row[5],
            "status": row[6],
            "opened_at": row[7],
            "closed_at": row[8],
            "source_recommendation_id": row[9],
            "metadata": loads_json(row[10], {}),
        }
        for row in rows
    ]


def recommendation_metadata(conn: sqlite3.Connection, recommendation_id: str | None) -> dict[str, Any]:
    if not recommendation_id or not _table_exists(conn, "decision_ledger"):
        return {}
    row = conn.execute(
        """
        SELECT metadata_json
        FROM decision_ledger
        WHERE recommendation_id=?
        ORDER BY datetime(updated_at) DESC, id DESC
        LIMIT 1
        """,
        (recommendation_id,),
    ).fetchone()
    return loads_json(row[0], {}) if row else {}


def position_summary(conn: sqlite3.Connection, position: dict[str, Any], watchlist_lookup: dict[str, dict[str, Any]]) -> dict[str, Any]:
    latest = latest_price_info(conn, position["ticker"], position.get("market"))
    fresh = is_price_fresh(latest)
    avg_cost = float(position.get("avg_cost") or 0.0)
    qty = float(position.get("quantity") or 0.0)
    latest_price = latest.get("price")
    unrealized_pnl = None
    price_status = "missing"
    if latest_price is not None:
        price_status = "fresh" if fresh else "stale"
        if fresh:
            unrealized_pnl = (float(latest_price) - avg_cost) * qty
    rec_meta = recommendation_metadata(conn, position.get("source_recommendation_id"))
    watchlist_item = watchlist_lookup.get(str(position.get("ticker") or "").upper()) or {}
    theme = (
        position.get("metadata", {}).get("theme")
        or rec_meta.get("theme")
        or rec_meta.get("candidate", {}).get("theme")
        or watchlist_item.get("theme")
        or "unknown"
    )
    sector = (
        position.get("metadata", {}).get("sector")
        or rec_meta.get("sector")
        or rec_meta.get("candidate", {}).get("sector")
        or watchlist_item.get("sector")
        or "unknown"
    )
    market = position.get("market") or rec_meta.get("market") or watchlist_item.get("market") or "unknown"
    return {
        **position,
        "theme": theme,
        "sector": sector,
        "market": market,
        "latest_price": latest_price,
        "latest_trade_date": latest.get("trade_date"),
        "price_status": price_status,
        "price_reason": latest.get("reason"),
        "price_fresh": fresh if latest_price is not None else False,
        "unrealized_pnl": unrealized_pnl,
    }


def summarize_exposure(rows: list[dict[str, Any]], key: str) -> dict[str, float]:
    totals = defaultdict(float)
    for row in rows:
        pct = float(row.get("position_pct") or 0.0)
        bucket = str(row.get(key) or "unknown")
        totals[bucket] += pct
    return {bucket: round(value, 4) for bucket, value in totals.items()}


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Paper Portfolio Summary",
        "",
        f"- generated_at: `{payload.get('generated_at')}`",
        f"- stale_price_count: `{payload.get('stale_price_count')}`",
        f"- open_position_count: `{len(payload.get('positions') or [])}`",
        "",
        "## Exposures",
        "",
    ]
    for label, values in (payload.get("exposures") or {}).items():
        lines.append(f"- {label}: `{values}`")
    lines.extend(["", "## Positions", "", "| ticker | market | pct | avg_cost | latest_price | pnl | price_status | theme | sector |", "|---|---|---:|---:|---:|---:|---|---|---|"])
    for row in payload.get("positions") or []:
        lines.append(
            "| {ticker} | {market} | {position_pct:.2f} | {avg_cost:.2f} | {latest_price} | {pnl} | {price_status} | {theme} | {sector} |".format(
                ticker=row.get("ticker") or "-",
                market=row.get("market") or "-",
                position_pct=float(row.get("position_pct") or 0.0),
                avg_cost=float(row.get("avg_cost") or 0.0),
                latest_price=row.get("latest_price") if row.get("latest_price") is not None else "-",
                pnl=round(float(row.get("unrealized_pnl") or 0.0), 2) if row.get("unrealized_pnl") is not None else "-",
                price_status=row.get("price_status") or "-",
                theme=row.get("theme") or "-",
                sector=row.get("sector") or "-",
            )
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build paper portfolio summary")
    parser.add_argument("--db-path", default=str(DB_PATH))
    args = parser.parse_args()

    conn = sqlite3.connect(args.db_path)
    conn.row_factory = sqlite3.Row
    try:
        ensure_paper_portfolio_tables(conn)
        mark_open_positions_to_market(conn)
        try:
            watchlist_lookup = watchlist_map("ai_core")
        except Exception:
            watchlist_lookup = {}
        positions = [position_summary(conn, row, watchlist_lookup) for row in open_positions(conn)]
        exposures = {
            "theme": summarize_exposure(positions, "theme"),
            "market": summarize_exposure(positions, "market"),
            "sector": summarize_exposure(positions, "sector"),
        }
        stale_price_count = sum(1 for row in positions if row.get("price_status") == "stale")
        payload = {
            "generated_at": now_ts(),
            "open_position_count": len(positions),
            "stale_price_count": stale_price_count,
            "positions": positions,
            "exposures": exposures,
            "price_status_counts": dict(Counter(row.get("price_status") or "missing" for row in positions)),
        }
        output_dir = project_path("06_reports", "adhoc", "phase6")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{payload['generated_at'][:10]}_paper_portfolio_summary.md"
        output_path.write_text(render_markdown(payload), encoding="utf-8")
        register_snapshot(
            conn,
            entity_type="paper_portfolio_summary",
            entity_id=payload["generated_at"][:10],
            status="generated",
            source=SCRIPT_NAME,
            payload={**payload, "summary_rel_path": str(output_path)},
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "paper portfolio summary built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
