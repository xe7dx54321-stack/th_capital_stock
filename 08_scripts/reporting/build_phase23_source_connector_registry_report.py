#!/usr/bin/env python3
"""Build Phase 23 source connector registry report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_source_connector_registry import load_source_connector_registry, summarize_connector_availability, validate_connector_registry
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(path: str | None = None) -> dict:
    registry = load_source_connector_registry(path)
    issues = validate_connector_registry(registry)
    availability = summarize_connector_availability(registry)
    return {
        "generated_at": now_ts(),
        "registry_version": registry.get("version"),
        "updated_at": registry.get("updated_at"),
        "validation_status": "pass" if not any(issue.get("severity") == "error" for issue in issues) else "blocked",
        "information_type_count": len(registry.get("information_types") or {}),
        "issues": issues,
        "summary": availability.get("summary") or {},
        "by_information_type": availability.get("by_information_type") or [],
        "key_gaps": availability.get("key_gaps") or [],
        "safety": {
            "planned_connector_usable_as_evidence": False,
            "official_consensus_implemented": False,
            "promotion_rules_relaxed": False,
        },
    }


def render_markdown(payload: dict) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 23 Source Connector Registry Report",
        "",
        "## Summary",
        f"- Registry version: {payload.get('registry_version')}",
        f"- Information types: {payload.get('information_type_count')}",
        f"- Implemented connectors: {summary.get('implemented_connectors')}",
        f"- Partial connectors: {summary.get('partial_connectors')}",
        f"- Planned connectors: {summary.get('planned_connectors')}",
        f"- Validation status: {payload.get('validation_status')}",
        "",
        "## By Information Type",
        "| Information Type | CN | HK | US | Current Usage |",
        "|---|---|---|---|---|",
    ]
    for row in payload.get("by_information_type") or []:
        def cell(market: str) -> str:
            item = row.get(market) or {}
            return f"{item.get('primary_connector')} / {item.get('status')} / {item.get('allowed_usage')}"

        lines.append(f"| {row.get('information_type')} | {cell('CN')} | {cell('HK')} | {cell('US')} | {row.get('current_usage')} |")
    lines.extend(["", "## Key Gaps", "| Gap | Current Status | Suggested Next Connector |", "|---|---|---|"])
    for gap in payload.get("key_gaps") or []:
        lines.append(f"| {gap.get('gap')} | {gap.get('current_status')} | {gap.get('suggested_next_connector')} |")
    if payload.get("issues"):
        lines.extend(["", "## Validation Issues", "| Severity | Path | Message |", "|---|---|---|"])
        for issue in payload.get("issues") or []:
            lines.append(f"| {issue.get('severity')} | {issue.get('path')} | {issue.get('message')} |")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 23 source connector registry report")
    parser.add_argument("--registry-path")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    payload = build_payload(args.registry_path)
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
