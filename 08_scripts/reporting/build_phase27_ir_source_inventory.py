#!/usr/bin/env python3
"""Build Phase 27 IR source inventory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_ir_source_inventory import build_ir_source_inventory
from smr_phase25_utils import resolve_phase25_tickers
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(*, ticker: str | None = None, tickers: str | None = None) -> dict:
    resolved = resolve_phase25_tickers(ticker or tickers)
    rows = [build_ir_source_inventory(item) for item in resolved]
    payload = {
        "generated_at": now_ts(),
        "summary": {
            "tickers_checked": len(rows),
            "sources_found": sum((row.get("source_inventory") or {}).get("sources_found", 0) for row in rows),
            "source_missing": sum(1 for row in rows if (row.get("source_inventory") or {}).get("source_missing")),
        },
        "rows": rows,
    }
    if len(rows) == 1 and ticker and not tickers:
        return {**rows[0], "generated_at": payload["generated_at"]}
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 27 IR source inventory")
    parser.add_argument("--ticker")
    parser.add_argument("--tickers")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build_payload(ticker=args.ticker, tickers=args.tickers), ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
