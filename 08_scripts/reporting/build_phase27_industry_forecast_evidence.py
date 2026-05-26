#!/usr/bin/env python3
"""Build Phase 27 industry forecast semantic evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_industry_forecast_semantic_extractor import build_industry_forecast_evidence
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def render_markdown(payload: dict) -> str:
    lines = ["# Phase 27 Industry Forecast Evidence", "", "| Object | Metric | Period | Direction | Usage |", "|---|---|---|---|---|"]
    for row in payload.get("industry_forecast_evidence") or []:
        lines.append(f"| {row.get('forecast_object')} | {row.get('forecast_metric')} | {row.get('forecast_period')} | {row.get('forecast_direction')} | {row.get('allowed_usage')} |")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build industry forecast evidence")
    parser.add_argument("--theme", default="ai_optical_interconnect")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--llm", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    mode = "llm" if args.llm and not args.mock else "mock"
    payload = {"generated_at": now_ts(), **build_industry_forecast_evidence(args.theme, mode=mode)}
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
