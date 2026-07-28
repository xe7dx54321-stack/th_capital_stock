from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from smr_app.acquisition.contracts import AcquisitionMode
from smr_app.research.data_requirements_v3 import build_stock_data_requirement_manifest
from smr_app.research.research_plan_v3 import build_stock_research_plan
from smr_app.tools.research_data import ResearchDataTools


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run live acquisition acceptance for one stock.")
    parser.add_argument("--ticker", default="300308.SZ")
    parser.add_argument("--market", default="A")
    parser.add_argument("--db-path", default=".tmp/live-data-acceptance.db")
    parser.add_argument("--output", default=".tmp/live-data-acceptance.json")
    parser.add_argument("--data-type", action="append", dest="data_types")
    return parser.parse_args()


def main() -> int:
    args = _args()
    db_path = Path(args.db_path)
    output_path = Path(args.output)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    tools = ResearchDataTools(db_path)
    manifest = build_stock_data_requirement_manifest(
        args.ticker,
        args.market,
        build_stock_research_plan(args.ticker, args.market),
    )
    acquisition = tools.acquire_manifest(
        manifest,
        mode=AcquisitionMode.FORCE_REFRESH,
        workflow_run_id=f"live_data_acceptance_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        only_data_types=args.data_types,
    )
    status = tools.provider_status(probe_local_firecrawl=True)
    results = acquisition["results"]
    critical_types = {
        str(item["data_type"])
        for item in manifest["requirements"]
        if item.get("critical") and (not args.data_types or item["data_type"] in args.data_types)
    }
    failed_critical = [
        data_type
        for data_type in critical_types
        if results.get(f"{args.ticker}:{data_type}", {}).get("status")
        not in {"acquired", "cache_hit"}
    ]
    failed_data_types = [
        requirement_id.split(":", 1)[1]
        for requirement_id, result in results.items()
        if result.get("status") not in {"acquired", "cache_hit"}
    ]
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ticker": args.ticker,
        "market": args.market,
        "provider_status": status,
        "acquisition": acquisition,
        "failed_critical": failed_critical,
        "failed_data_types": failed_data_types,
        "passed": (
            not failed_critical
            and not failed_data_types
            and status["local_firecrawl_reachable"]
        ),
    }
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
