#!/usr/bin/env python3
"""Build Phase 23 connector availability dashboard."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_source_connector_registry import load_source_connector_registry, summarize_connector_availability
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload() -> dict:
    registry = load_source_connector_registry()
    availability = summarize_connector_availability(registry)
    payload = {
        "generated_at": now_ts(),
        **availability,
        "safety": {
            "official_consensus_implemented": False,
            "tender_procurement_implemented_if_planned": False,
            "planned_connector_usable_as_evidence": False,
            "semantic_ir_mock_marked_implemented": False,
            "semantic_evidence_persistence_direct_promotion": False,
        },
    }
    return payload


def render_markdown(payload: dict) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 23 Connector Availability Dashboard",
        "",
        "## Summary",
        f"- Implemented: {summary.get('implemented_connectors')}",
        f"- Partial: {summary.get('partial_connectors')}",
        f"- Planned: {summary.get('planned_connectors')}",
        f"- Disabled: {summary.get('disabled_connectors')}",
        "",
        "## By Information Type",
        "| Information Type | CN | HK | US | Current Usage |",
        "|---|---|---|---|---|",
    ]
    for row in payload.get("by_information_type") or []:
        def cell(market: str) -> str:
            item = row.get(market) or {}
            return f"{item.get('primary_connector')} / {item.get('status')}"

        lines.append(f"| {row.get('information_type')} | {cell('CN')} | {cell('HK')} | {cell('US')} | {row.get('current_usage')} |")
    lines.extend(["", "## Key Gaps", "| Gap | Current Status | Suggested Next Connector |", "|---|---|---|"])
    for gap in payload.get("key_gaps") or []:
        lines.append(f"| {gap.get('gap')} | {gap.get('current_status')} | {gap.get('suggested_next_connector')} |")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 23 connector availability dashboard")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    payload = build_payload()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
