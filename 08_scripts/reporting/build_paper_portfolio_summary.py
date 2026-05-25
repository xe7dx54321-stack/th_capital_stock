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
from smr_decision import build_review_audit_metadata
from smr_paper_portfolio import ensure_paper_portfolio_tables, is_price_fresh, latest_price_info, mark_open_positions_to_market
from smr_phase6_watchlists import watchlist_map
from smr_paths import project_path
from smr_portfolio_risk import DEFAULT_PHASE6_RISK_POLICY
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


def summarize_total_exposure(rows: list[dict[str, Any]]) -> float:
    return round(sum(float(row.get("position_pct") or 0.0) for row in rows), 4)


def summarize_pending_exposure(conn: sqlite3.Connection) -> float:
    if not _table_exists(conn, "decision_ledger"):
        return 0.0
    row = conn.execute(
        """
        SELECT SUM(COALESCE(suggested_position_pct, 0))
        FROM decision_ledger
        WHERE status='pending_human_review'
        """
    ).fetchone()
    return round(float(row[0] or 0.0), 4) if row else 0.0


def pending_candidate_rows(conn: sqlite3.Connection, watchlist_lookup: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    if not _table_exists(conn, "decision_ledger"):
        return []
    rows = conn.execute(
        """
        SELECT recommendation_id, ticker, market, action, status, suggested_position_pct,
               max_position_pct, metadata_json, updated_at
        FROM decision_ledger
        WHERE status IN ('pending_human_review', 'candidate_shadow')
        ORDER BY datetime(updated_at) DESC, id DESC
        """
    ).fetchall()
    results = []
    for row in rows:
        metadata = loads_json(row[7], {})
        metadata = build_review_audit_metadata(metadata, status=row[4])
        candidate = metadata.get("candidate") or {}
        portfolio_risk = metadata.get("portfolio_risk") or (candidate.get("snapshots") or {}).get("portfolio_risk") or {}
        ticker = str(row[1] or candidate.get("ticker") or "").upper()
        watchlist_item = watchlist_lookup.get(ticker) or {}
        base_pct = float(row[5] if row[5] is not None else candidate.get("suggested_position_pct") or 0.0)
        if base_pct <= 0.0:
            base_pct = float(
                portfolio_risk.get("base_position_pct")
                if portfolio_risk.get("base_position_pct") is not None
                else candidate.get("suggested_position_pct")
                or 0.0
            )
        risk_adjusted_pct = float(
            portfolio_risk.get("recommended_position_pct")
            if portfolio_risk.get("recommended_position_pct") is not None
            else portfolio_risk.get("risk_adjusted_sizing")
            if portfolio_risk.get("risk_adjusted_sizing") is not None
            else base_pct
        )
        full_size_pct = float(
            portfolio_risk.get("base_position_pct")
            if portfolio_risk.get("base_position_pct") is not None
            else metadata.get("full_size_position_pct")
            if metadata.get("full_size_position_pct") is not None
            else candidate.get("max_position_pct")
            or base_pct
        )
        promotion_mode = metadata.get("promotion_mode") or candidate.get("promotion_mode")
        position_policy = metadata.get("position_policy") or candidate.get("position_policy")
        results.append(
            {
                "recommendation_id": row[0],
                "ticker": ticker,
                "market": row[2] or metadata.get("market") or portfolio_risk.get("market") or watchlist_item.get("market") or "unknown",
                "action": row[3],
                "status": row[4],
                "position_pct": base_pct,
                "risk_adjusted_position_pct": risk_adjusted_pct,
                "full_size_position_pct": full_size_pct,
                "max_position_pct": float(row[6] or candidate.get("max_position_pct") or 0.0),
                "theme": metadata.get("theme") or candidate.get("theme") or portfolio_risk.get("theme") or watchlist_item.get("theme") or "unknown",
                "sector": metadata.get("sector") or candidate.get("sector") or portfolio_risk.get("sector") or watchlist_item.get("sector") or "unknown",
                "portfolio_risk": portfolio_risk,
                "promotion_mode": promotion_mode,
                "position_policy": position_policy,
                "primary_thesis_type": metadata.get("primary_thesis_type") or candidate.get("primary_thesis_type"),
                "core_blockers": metadata.get("core_blockers") or [],
                "supporting_warnings": metadata.get("supporting_warnings") or [],
                "optional_warnings": metadata.get("optional_warnings") or [],
                "bear_case_status": metadata.get("bear_case_status"),
                "residual_risk_level": metadata.get("residual_risk_level"),
                "requires_human_review": bool(metadata.get("requires_human_review")),
                "auto_approval_allowed": bool(metadata.get("auto_approval_allowed")),
                "paper_order_allowed": bool(metadata.get("paper_order_allowed")),
                "reduction_reason": metadata.get("reduction_reason")
                or ("partially_mitigated_bear_case_and_non_core_data_quality_warnings" if promotion_mode == "reduced_size_pending" else None),
                "audit_flags": metadata.get("audit_flags") or [],
                "updated_at": row[8],
            }
        )
    return results


def _add_exposure_maps(base: dict[str, dict[str, float]], rows: list[dict[str, Any]], pct_key: str = "position_pct") -> dict[str, dict[str, float]]:
    projected = {dimension: dict(values) for dimension, values in base.items()}
    for row in rows:
        pct = float(row.get(pct_key) or 0.0)
        for dimension in ("theme", "market", "sector"):
            bucket = str(row.get(dimension) or "unknown")
            projected.setdefault(dimension, {})
            projected[dimension][bucket] = round(projected[dimension].get(bucket, 0.0) + pct, 4)
    return projected


def projected_reduced_size_exposure(
    current_total: float,
    current_exposures: dict[str, dict[str, float]],
    reduced_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    projected = _add_exposure_maps(current_exposures, reduced_rows, "risk_adjusted_position_pct")
    return {
        "total": round(current_total + sum(float(row.get("risk_adjusted_position_pct") or 0.0) for row in reduced_rows), 4),
        "market": projected.get("market") or {},
        "theme": projected.get("theme") or {},
        "sector": projected.get("sector") or {},
    }


def dedupe_reduced_size_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Avoid double-counting repeated reduced-size validations for a ticker."""

    by_ticker: dict[str, dict[str, Any]] = {}
    for row in rows:
        ticker = str(row.get("ticker") or row.get("recommendation_id") or "")
        current = by_ticker.get(ticker)
        if current is None:
            by_ticker[ticker] = row
            continue
        rec_id = str(row.get("recommendation_id") or "")
        current_id = str(current.get("recommendation_id") or "")
        if rec_id.startswith("phase14_") and not current_id.startswith("phase14_"):
            by_ticker[ticker] = row
    return list(by_ticker.values())


def _exposure_warnings(projected: dict[str, dict[str, float]], *, prefix: str = "PROJECTED") -> list[dict[str, str]]:
    limits = {
        "theme": float(DEFAULT_PHASE6_RISK_POLICY["max_theme_exposure_pct"]),
        "market": float(DEFAULT_PHASE6_RISK_POLICY["max_market_exposure_pct"]),
        "sector": float(DEFAULT_PHASE6_RISK_POLICY["max_sector_exposure_pct"]),
    }
    warnings = []
    for dimension, buckets in projected.items():
        limit = limits.get(dimension)
        if limit is None:
            continue
        for bucket, value in buckets.items():
            if value > limit:
                warnings.append(
                    {
                        "code": f"{dimension.upper()}_EXPOSURE_LIMIT",
                        "message": f"{bucket} {dimension} projected exposure {value:.2f}% exceeds limit {limit:.2f}%",
                        "suggested_action": "downsize or delay one or more pending candidates",
                    }
                )
            elif value >= limit * 0.85:
                warnings.append(
                    {
                        "code": f"{dimension.upper()}_EXPOSURE_WARNING",
                        "message": f"{bucket} {dimension} projected exposure {value:.2f}% approaches limit {limit:.2f}%",
                        "suggested_action": "prefer risk-adjusted sizing",
                    }
                )
    return warnings


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Paper Portfolio Summary",
        "",
        f"- generated_at: `{payload.get('generated_at')}`",
        f"- stale_price_count: `{payload.get('stale_price_count')}`",
        f"- open_position_count: `{len(payload.get('positions') or [])}`",
        f"- current_exposure_total: `{payload.get('current_exposure_total')}`",
        f"- pending_exposure_if_all_approved: `{payload.get('pending_exposure_if_all_approved')}`",
        f"- exposure_after_risk_adjusted_sizing: `{payload.get('exposure_after_risk_adjusted_sizing')}`",
        "",
        "## Current Exposure",
        "",
    ]
    for label, values in (payload.get("current_exposure") or {}).items():
        lines.append(f"- {label}: `{values}`")
    pending = payload.get("pending_approval_scenario") or {}
    lines.extend(["", "## Pending Approval Scenario", ""])
    lines.append(f"- candidate_count: `{pending.get('candidate_count') or 0}`")
    lines.append(f"- gross_new_position_pct: `{pending.get('gross_new_position_pct') or 0}`")
    lines.append(f"- projected_exposure_if_all_approved: `{pending.get('projected_exposure_if_all_approved') or {}}`")
    risk_adjusted = payload.get("risk_adjusted_scenario") or {}
    lines.extend(["", "## Risk-adjusted Scenario", ""])
    lines.append(f"- gross_new_position_pct: `{risk_adjusted.get('gross_new_position_pct') or 0}`")
    lines.append(f"- risk_adjusted_exposure: `{risk_adjusted.get('risk_adjusted_exposure') or {}}`")
    reduced = payload.get("pending_reduced_size_candidates") or []
    lines.extend(["", "## Reduced-size Pending", ""])
    lines.append(f"- candidate_count: `{len(reduced)}`")
    lines.append(f"- projected_exposure_if_reduced_size_approved: `{payload.get('projected_exposure_if_reduced_size_approved') or {}}`")
    for row in reduced:
        lines.append(
            f"- {row.get('ticker')}: {row.get('risk_adjusted_position_pct')}% reduced from {row.get('full_size_position_pct')}%; "
            f"thesis={row.get('primary_thesis_type')}; warnings={row.get('optional_warnings') or []}"
        )
    lines.extend(["", "## Warnings", ""])
    for warning in payload.get("warnings") or []:
        lines.append(f"- `{warning.get('code')}` {warning.get('message')} Suggested: {warning.get('suggested_action')}")
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
        pending_rows = pending_candidate_rows(conn, watchlist_lookup)
        reduced_size_rows = [
            row
            for row in pending_rows
            if row.get("status") == "pending_human_review"
            and row.get("promotion_mode") == "reduced_size_pending"
        ]
        reduced_size_rows = dedupe_reduced_size_rows(reduced_size_rows)
        current_exposure_total = summarize_total_exposure(positions)
        pending_exposure_if_all_approved = round(sum(float(row.get("position_pct") or 0.0) for row in pending_rows), 4)
        risk_adjusted_new_position_pct = round(sum(float(row.get("risk_adjusted_position_pct") or 0.0) for row in pending_rows), 4)
        exposure_after_risk_adjusted_sizing = round(current_exposure_total + risk_adjusted_new_position_pct, 4)
        projected_all = _add_exposure_maps(exposures, pending_rows, "position_pct")
        projected_risk_adjusted = _add_exposure_maps(exposures, pending_rows, "risk_adjusted_position_pct")
        reduced_size_projected = projected_reduced_size_exposure(current_exposure_total, exposures, reduced_size_rows)
        warnings = _exposure_warnings(projected_all) + _exposure_warnings(projected_risk_adjusted, prefix="RISK_ADJUSTED")
        stale_price_count = sum(1 for row in positions if row.get("price_status") == "stale")
        payload = {
            "generated_at": now_ts(),
            "open_position_count": len(positions),
            "stale_price_count": stale_price_count,
            "positions": positions,
            "exposures": exposures,
            "current_exposure": exposures,
            "current_exposure_total": current_exposure_total,
            "pending_exposure_if_all_approved": pending_exposure_if_all_approved,
            "exposure_after_risk_adjusted_sizing": exposure_after_risk_adjusted_sizing,
            "pending_approval_scenario": {
                "candidate_count": len(pending_rows),
                "gross_new_position_pct": pending_exposure_if_all_approved,
                "projected_exposure_if_all_approved": projected_all,
                "candidates": pending_rows,
            },
            "pending_reduced_size_candidates": reduced_size_rows,
            "projected_exposure_if_reduced_size_approved": reduced_size_projected,
            "risk_adjusted_scenario": {
                "candidate_count": len(pending_rows),
                "gross_new_position_pct": risk_adjusted_new_position_pct,
                "risk_adjusted_exposure": projected_risk_adjusted,
            },
            "warnings": warnings,
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
