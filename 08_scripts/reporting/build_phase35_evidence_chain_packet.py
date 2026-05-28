#!/usr/bin/env python3
"""Build Phase 35 evidence-chain packet."""

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
from smr_research_evidence_chain import build_research_evidence_chain

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, *, ticker: str) -> dict[str, Any]:
    return build_research_evidence_chain(conn, ticker)


def render_markdown(payload: dict[str, Any]) -> str:
    chain = payload.get("evidence_chain") or {}
    lines = [
        "# Phase 35 Evidence Chain Packet",
        "",
        f"## Ticker\n{payload.get('ticker')} / {payload.get('company_name')}",
        "",
        "## Summary",
        f"- Total evidence: {chain.get('total_evidence')}",
        f"- Reviewed evidence: {chain.get('reviewed_evidence')}",
        f"- Approved evidence: {chain.get('approved_evidence')}",
        f"- Downgraded evidence: {chain.get('downgraded_evidence')}",
        f"- Context-only evidence: {chain.get('context_only_evidence')}",
        f"- Review required: {chain.get('review_required')}",
        "",
        "## Key Evidence",
        "| Evidence | Topic | Source Type | Usage | Review | Source | Quote |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in chain.get("key_evidence") or []:
        quote = " ".join(str(row.get("quoted_span") or "").split())[:160]
        lines.append(
            f"| {row.get('evidence_id')} | {row.get('topic')} | {row.get('source_type')} | "
            f"{row.get('allowed_usage')} | {row.get('review_status')} | {row.get('source_url')} | {quote} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 35 evidence-chain packet")
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
