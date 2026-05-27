#!/usr/bin/env python3
"""Audit semantic evidence links to supply-chain variable packs."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_evidence_lifecycle import list_semantic_evidence_candidates
from smr_sensitive_variable_guard import is_sensitive_variable
from smr_supply_chain_variable_evidence import SEMANTIC_VARIABLE_MAP
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def link_for_candidate(candidate: dict) -> dict:
    variable_type = str(candidate.get("variable_type") or "")
    variable_pack = SEMANTIC_VARIABLE_MAP.get(variable_type)
    sensitive = is_sensitive_variable(variable_type)
    if not variable_pack:
        status = "unlinked"
        reason = "variable_type has no mapped variable pack; not used for expectation gap impact"
    elif candidate.get("usable_for_promotion"):
        status = "invalid"
        reason = "semantic evidence cannot be promotion-enabled"
    else:
        status = "valid"
        reason = f"{variable_type} maps to {variable_pack}"
    return {
        "evidence_id": candidate.get("evidence_id"),
        "ticker": candidate.get("ticker"),
        "variable_type": variable_type,
        "variable_pack": variable_pack,
        "link_status": status,
        "requires_review": sensitive,
        "reason": reason,
        "source_url": candidate.get("source_url"),
    }


def build_payload(conn: sqlite3.Connection) -> dict:
    candidates = list_semantic_evidence_candidates(conn)
    links = [link_for_candidate(candidate) for candidate in candidates]
    linked = [link for link in links if link.get("variable_pack")]
    invalid = [link for link in links if link.get("link_status") == "invalid"]
    requiring_review = [link for link in links if link.get("requires_review")]
    return {
        "generated_at": now_ts(),
        "summary": {
            "linked_evidence_count": len(linked),
            "unlinked_evidence_count": len(links) - len(linked),
            "sensitive_links": len(requiring_review),
            "invalid_links": len(invalid),
            "links_requiring_review": len(requiring_review),
        },
        "links": links,
        "safety": {
            "invalid_link_affects_expectation_gap": False,
            "semantic_evidence_direct_promotion": False,
        },
    }


def render_markdown(payload: dict) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 31 Variable Pack Link Audit",
        "",
        "## Overall",
        f"- Linked evidence count: {summary.get('linked_evidence_count')}",
        f"- Unlinked evidence count: {summary.get('unlinked_evidence_count')}",
        f"- Sensitive links: {summary.get('sensitive_links')}",
        f"- Invalid links: {summary.get('invalid_links')}",
        f"- Links requiring review: {summary.get('links_requiring_review')}",
        "",
        "## Links",
        "| Ticker | Evidence | Variable | Pack | Status | Requires Review |",
        "|---|---|---|---|---|---|",
    ]
    for link in payload.get("links") or []:
        lines.append(
            f"| {link.get('ticker')} | {link.get('evidence_id')} | {link.get('variable_type')} | {link.get('variable_pack')} | {link.get('link_status')} | {link.get('requires_review')} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 31 variable pack link audit")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
