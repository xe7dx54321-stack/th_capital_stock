#!/usr/bin/env python3
"""Build Phase 26 industry forecast source routing."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_supply_chain_variable_evidence import build_industry_forecast_routing

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 26 industry forecast source routing")
    parser.add_argument("--theme", default="ai_optical_interconnect")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build_industry_forecast_routing(args.theme), ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
