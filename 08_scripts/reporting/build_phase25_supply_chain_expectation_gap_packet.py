#!/usr/bin/env python3
"""Build Phase 25 supply-chain expectation-gap packets."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_end_demand_proxy import build_end_demand_proxy
from smr_expectation_gap import build_expectation_gap
from smr_phase25_utils import resolve_phase25_tickers, unique_list
from smr_registry import register_snapshot
from smr_revenue_sensitivity_model import build_revenue_sensitivity
from smr_runlog import log_run
from smr_supplier_exposure_model import get_supplier_exposure_profile
from smr_supply_chain_theme_template import get_supply_chain_template
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "build_phase25_supply_chain_expectation_gap_packet.py"


def build_packet(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    profile = get_supplier_exposure_profile(ticker)
    theme = profile.get("theme") or "ai_optical_interconnect"
    template = get_supply_chain_template("ai_optical_interconnect")
    end_proxy = build_end_demand_proxy(conn, "ai_optical_interconnect")
    sensitivity = build_revenue_sensitivity(conn, ticker, theme=theme, end_demand_proxy=end_proxy)
    gap = build_expectation_gap(conn, ticker, theme=theme, end_demand_proxy=end_proxy, revenue_sensitivity=sensitivity)
    missing_variables = unique_list(
        list((sensitivity.get("revenue_sensitivity") or {}).get("missing_variables") or [])
        + ["official consensus"]
    )
    next_connector_needs = unique_list(list((sensitivity.get("revenue_sensitivity") or {}).get("next_connector_needs") or []))
    if "consensus source" not in next_connector_needs:
        next_connector_needs.append("consensus source")
    packet_status = "needs_more_data" if len(missing_variables) >= 4 else "ready_for_research_review"
    return {
        "ticker": gap.get("ticker"),
        "company_name": profile.get("company_name"),
        "theme": theme,
        "packet_status": packet_status,
        "sections": {
            "theme_template": template,
            "supplier_exposure": profile,
            "end_demand_proxy": end_proxy.get("end_demand_proxy"),
            "revenue_sensitivity": sensitivity.get("revenue_sensitivity"),
            "expectation_gap": gap.get("expectation_gap"),
            "missing_variables": missing_variables,
            "next_connector_needs": next_connector_needs,
        },
        "allowed_usage": "research_candidate_only",
        "promotion_allowed": False,
        "safety": {
            "assumptions_transparent": True,
            "packet_directly_promotes": False,
            "proxy_estimate_treated_as_confirmed": False,
        },
    }


def build_payload(conn: sqlite3.Connection, *, ticker: str | None = None, tickers: str | None = None, watchlist: str | None = None) -> dict[str, Any]:
    resolved = resolve_phase25_tickers(ticker or tickers, watchlist)
    packets = [build_packet(conn, item) for item in resolved]
    payload = {
        "generated_at": now_ts(),
        "summary": {
            "tickers_checked": len(packets),
            "packets_generated": len(packets),
            "ready_for_research_review": sum(1 for packet in packets if packet.get("packet_status") == "ready_for_research_review"),
            "needs_more_data": sum(1 for packet in packets if packet.get("packet_status") == "needs_more_data"),
            "promotion_allowed": sum(1 for packet in packets if packet.get("promotion_allowed")),
        },
        "packets": packets,
    }
    if len(packets) == 1 and ticker and not tickers:
        return {**packets[0], "generated_at": payload["generated_at"]}
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    packet = payload if "sections" in payload else ((payload.get("packets") or [{}])[0])
    sections = packet.get("sections") or {}
    gap = sections.get("expectation_gap") or {}
    sensitivity = sections.get("revenue_sensitivity") or {}
    lines = [
        "# Supply Chain Expectation Gap Packet",
        "",
        f"## Ticker\n{packet.get('ticker')} {packet.get('company_name') or ''}",
        "",
        f"## Theme\n{packet.get('theme')}",
        "",
        f"## End Demand Proxy\nDirection: {(sections.get('end_demand_proxy') or {}).get('overall_direction')} / Confidence: {(sections.get('end_demand_proxy') or {}).get('overall_confidence')}",
        "",
        f"## Supplier Exposure\nRole: {', '.join((sections.get('supplier_exposure') or {}).get('supply_chain_role') or [])}",
        "",
        f"## Revenue Sensitivity\nStatus: {sensitivity.get('status')} / Valuation support: {sensitivity.get('valuation_support')}",
        "",
        f"## Expectation Gap\nStatus: {gap.get('status')} / Score: {gap.get('score')} / Confidence: {gap.get('confidence')}",
        "",
        "## Missing Variables",
    ]
    for item in sections.get("missing_variables") or []:
        lines.append(f"- {item}")
    lines.extend(["", "## Next Connector Needs"])
    for item in sections.get("next_connector_needs") or []:
        lines.append(f"- {item}")
    lines.extend(["", "## Allowed Usage", f"{packet.get('allowed_usage')} / promotion_allowed={packet.get('promotion_allowed')}"])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 25 supply-chain expectation-gap packet")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker")
    parser.add_argument("--tickers")
    parser.add_argument("--watchlist")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, ticker=args.ticker, tickers=args.tickers, watchlist=args.watchlist)
        register_snapshot(conn, "phase25_expectation_gap_packet", args.ticker or args.tickers or args.watchlist or "supply_chain_pilot", "built", SCRIPT_NAME, payload=payload)
        conn.commit()
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase25 expectation-gap packet built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
