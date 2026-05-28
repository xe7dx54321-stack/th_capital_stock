#!/usr/bin/env python3
"""Build Phase 47 tracking variable snapshot."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_research_review_lifecycle import TARGET_REVIEW_TICKER
from smr_tracking_variable_snapshot import build_tracking_variable_snapshot
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(ticker: str = TARGET_REVIEW_TICKER) -> dict:
    return build_tracking_variable_snapshot(ticker)


def render_markdown(payload: dict) -> str:
    snap = payload.get("tracking_variable_snapshot") or {}
    summary = snap.get("summary") or {}
    rows = snap.get("snapshot_rows") or []
    lines = [
        f"# Phase 47 Tracking Variable Snapshot: {payload.get('ticker')}",
        "",
        f"- variables_checked: {snap.get('variables_checked')}",
        "",
        "## Summary",
        f"- strengthened: {summary.get('strengthened_variables')}",
        f"- weakened: {summary.get('weakened_variables')}",
        f"- unchanged_positive: {summary.get('unchanged_positive')}",
        f"- unchanged_gaps: {summary.get('unchanged_gaps')}",
        f"- needs_more_evidence: {summary.get('needs_more_evidence')}",
        "",
        "## Variables",
    ]
    for r in rows:
        lines.append(f"- {r['variable']}: {r['current_status']} ({r['delta']})")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 47 tracking variable snapshot")
    parser.add_argument("--db-path", default="", help="Accepted for CLI consistency")
    parser.add_argument("--ticker", default=TARGET_REVIEW_TICKER)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    payload = build_payload(args.ticker)
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
