#!/usr/bin/env python3
"""Build Phase 27 semantic IR evidence."""

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
    return {
        "generated_at": now_ts(),
        "mode": mode,
        "summary": pipeline.get("summary"),
        "rows": [
            {
                "ticker": row.get("ticker"),
                "semantic_extractions": row.get("semantic_extractions"),
                "no_extraction_chunks": row.get("no_extraction_chunks"),
                "prompt_guardrails": row.get("prompt_guardrails"),
                "llm_enabled": row.get("llm_enabled"),
            }
            for row in pipeline.get("rows") or []
        ],
        "safety": {
            "llm_default_enabled": False,
            "external_knowledge_allowed": False,
            "customer_names_fabricated": False,
            "confirmed_order_fabricated": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build semantic IR evidence")
    parser.add_argument("--ticker")
    parser.add_argument("--tickers")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--llm", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    mode = "llm" if args.llm and not args.mock else "mock"
    print(json.dumps(build_payload(tickers=args.ticker or args.tickers, mode=mode), ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
