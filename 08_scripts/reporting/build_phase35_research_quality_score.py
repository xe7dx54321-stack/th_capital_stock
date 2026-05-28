#!/usr/bin/env python3
"""Build Phase 35 research quality score."""

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
from smr_research_quality_scoring import build_research_quality_score

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, *, ticker: str) -> dict[str, Any]:
    return build_research_quality_score(conn, ticker)


def render_markdown(payload: dict[str, Any]) -> str:
    quality = payload.get("research_quality") or {}
    lines = [
        "# Phase 35 Research Quality Score",
        "",
        f"## Ticker\n{payload.get('ticker')}",
        "",
        "## Score",
        f"- Overall quality: {quality.get('overall_quality')}",
        f"- Evidence coverage: {quality.get('evidence_coverage')}",
        f"- Thesis clarity: {quality.get('thesis_clarity')}",
        f"- Valuation support: {quality.get('valuation_support')}",
        f"- Bear case quality: {quality.get('bear_case_quality')}",
        f"- Research readiness: {quality.get('research_readiness')}",
        "",
        "## Key Quality Gaps",
    ]
    lines.extend(f"- {item}" for item in quality.get("key_quality_gaps") or [])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 35 research quality score")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, ticker=args.ticker)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
