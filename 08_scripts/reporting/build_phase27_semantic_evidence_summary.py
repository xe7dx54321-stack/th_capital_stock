#!/usr/bin/env python3
"""Build Phase 27 semantic evidence summary."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_phase27_semantic_pipeline import build_semantic_pipeline
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(*, tickers: str | None = None, mode: str = "mock") -> dict:
    pipeline = build_semantic_pipeline(tickers, mode=mode)
    by_variable: dict[str, int] = {}
    rows = []
    for row in pipeline.get("rows") or []:
        passed = [gate for gate in row.get("gate_results") or [] if gate.get("evidence_status") != "blocked"]
        variables = list(dict.fromkeys(str(gate.get("variable_type")) for gate in passed if gate.get("variable_type")))
        for variable in variables:
            by_variable[variable] = by_variable.get(variable, 0) + 1
        rows.append(
            {
                "ticker": row.get("ticker"),
                "extractions": len(row.get("semantic_extractions") or []),
                "passed_gate": len(passed),
                "main_variables": variables[:5],
                "limitations": ["no supplier share", "no ASP", "no customer allocation", "no official consensus"],
            }
        )
    summary = dict(pipeline.get("summary") or {})
    summary.update(
        {
            "variable_packs_updated": sum(1 for row in rows if row.get("passed_gate")),
            "new_pending_created": 0,
        }
    )
    return {
        "generated_at": now_ts(),
        "mode": mode,
        "summary": summary,
        "by_variable_type": by_variable,
        "rows": rows,
        "safety": {
            "semantic_evidence_alone_pending": False,
            "promotion_rules_relaxed": False,
            "raw_large_files_written": False,
        },
    }


def render_markdown(payload: dict) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 27 Semantic Evidence Summary",
        "",
        "## Overall",
        f"- Sources found: {summary.get('sources_found')}",
        f"- Candidate chunks: {summary.get('candidate_chunks')}",
        f"- Semantic extractions: {summary.get('semantic_extractions')}",
        f"- Passed gate: {summary.get('passed_gate')}",
        f"- Variable packs updated: {summary.get('variable_packs_updated')}",
        f"- New pending: {summary.get('new_pending_created')}",
        "",
        "## By Variable",
        "| Variable | Count |",
        "|---|---|",
    ]
    for variable, count in sorted((payload.get("by_variable_type") or {}).items()):
        lines.append(f"| {variable} | {count} |")
    lines.extend(["", "## By Ticker", "| Ticker | Extractions | Passed Gate | Main Variables | Limitations |", "|---|---|---|---|---|"])
    for row in payload.get("rows") or []:
        lines.append(f"| {row.get('ticker')} | {row.get('extractions')} | {row.get('passed_gate')} | {', '.join(row.get('main_variables') or [])} | {'; '.join(row.get('limitations') or [])} |")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build semantic evidence summary")
    parser.add_argument("--tickers")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--llm", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    mode = "llm" if args.llm and not args.mock else "mock"
    payload = build_payload(tickers=args.tickers, mode=mode)
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
