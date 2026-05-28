#!/usr/bin/env python3
"""Build Phase 48 event trigger detector."""

from __future__ import annotations

import argparse, json, sqlite3, sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path: sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER
from smr_watchlist_event_detector import build_event_detector_result

if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

def build_payload(conn, ticker): return build_event_detector_result(conn, ticker)

def render_markdown(payload):
    det = payload.get("event_trigger_detector") or {}
    lines = [f"# Phase 48 Event Trigger Detector: {payload.get('ticker')}", "",
             f"- events_checked: {det.get('events_checked')}",
             f"- events_detected: {det.get('events_detected')}",
             f"- refresh_required: {det.get('refresh_required')}",
             "", "## Events"]
    for e in det.get("event_rows") or []:
        lines.append(f"- {e.get('event_type')}: {e.get('event_title')} (requires_refresh={e.get('requires_evidence_refresh')})")
    return "\n".join(lines).rstrip() + "\n"

def main():
    p = argparse.ArgumentParser(description="Build Phase 48 event trigger detector")
    p.add_argument("--db-path", default=str(DB_PATH)); p.add_argument("--ticker", default=TARGET_REVIEW_TICKER)
    p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    args = p.parse_args()
    conn = sqlite3.connect(args.db_path)
    try: payload = build_payload(conn, args.ticker)
    finally: conn.close()
    if args.markdown and not args.json: print(render_markdown(payload), end="")
    else: print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0

if __name__ == "__main__": raise SystemExit(main())
