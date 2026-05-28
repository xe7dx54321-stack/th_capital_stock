#!/usr/bin/env python3
"""Build Phase 48 event trigger schema."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_research_review_lifecycle import TARGET_REVIEW_TICKER
from smr_watchlist_event_trigger import build_event_trigger, EVENT_TYPES, SAMPLE_EVENTS
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(ticker: str = TARGET_REVIEW_TICKER) -> dict:
    events = []
    for sample in SAMPLE_EVENTS:
        if sample["ticker"] == ticker:
            events.append(build_event_trigger(
                ticker=ticker,
                event_type=sample["event_type"],
                event_source=sample["event_source"],
                event_title=sample["event_title"],
                linked_tracking_variables=list(sample["linked_tracking_variables"]),
                event_strength=sample.get("event_strength", "medium"),
            ))
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "event_trigger_schema": {
            "supported_event_types": sorted(EVENT_TYPES),
            "always_forbidden_actions": ["create_pending", "create_paper_order", "create_trade"],
            "sample_events": events,
        },
        "safety": {
            "schema_defines_pending_action": False,
            "schema_defines_order_action": False,
            "schema_defines_trade_action": False,
        },
    }


def render_markdown(payload: dict) -> str:
    schema = payload.get("event_trigger_schema") or {}
    lines = [
        f"# Phase 48 Event Trigger Schema: {payload.get('ticker')}",
        "",
        "## Supported Event Types",
    ]
    for t in schema.get("supported_event_types") or []:
        lines.append(f"- {t}")
    lines.extend(["", "## Sample Events"])
    for e in schema.get("sample_events") or []:
        lines.append(f"- {e.get('event_type')}: {e.get('event_title')}")
    lines.extend(["", "## Forbidden Actions"])
    for a in schema.get("always_forbidden_actions") or []:
        lines.append(f"- {a}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description="Build Phase 48 event trigger schema")
    p.add_argument("--db-path", default="")
    p.add_argument("--ticker", default=TARGET_REVIEW_TICKER)
    p.add_argument("--json", action="store_true")
    p.add_argument("--markdown", action="store_true")
    args = p.parse_args()
    payload = build_payload(args.ticker)
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
