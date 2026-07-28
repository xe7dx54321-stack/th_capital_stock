from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from smr_app.acquisition.contracts import AcquisitionMode
from smr_app.acquisition.kernel import AcquisitionKernel
from smr_app.acquisition.providers import (
    default_peer_comparison_provider,
    default_szse_market_provider,
    default_tencent_market_provider,
    default_valuation_provider,
)
from smr_app.acquisition.store import AcquisitionStore
from smr_app.research.data_requirements_v3 import (
    build_stock_data_requirement_manifest,
    requirement_from_manifest_item,
)
from smr_app.research.research_plan_v3 import build_stock_research_plan
from smr_app.runtime.migrations import apply_migrations
from smr_app.runtime.runner import WorkflowRunner
from smr_app.workflows.stock_deep_dive import stock_deep_dive_definition


MARKET_TYPES = {"daily_bars", "realtime_quote", "valuation_snapshot", "peer_comparison"}


def _latest_facts(store: AcquisitionStore, ticker: str, data_type: str) -> dict:
    facts = [item for item in store.list_facts(ticker, data_type) if item.get("verification_status") == "verified"]
    latest = max((str(item.get("as_of") or "") for item in facts), default=None)
    return {
        "as_of": latest,
        "facts": {
            item["field_name"]: item["value"]
            for item in facts
            if str(item.get("as_of") or "") == latest
        },
        "fact_count": len(facts),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run real A-share market, valuation and peer acquisition smoke tests")
    parser.add_argument("--ticker", default="300308.SZ")
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--mode", choices=[item.value for item in AcquisitionMode], default="force_refresh")
    parser.add_argument("--run-workflow", action="store_true")
    parser.add_argument("--source-db")
    parser.add_argument("--artifact-root")
    parser.add_argument("--run-id", default="market-v3-real-smoke")
    args = parser.parse_args()

    db_path = Path(args.db_path).resolve()
    apply_migrations(db_path)
    store = AcquisitionStore(db_path)
    providers = (
        default_szse_market_provider(),
        default_tencent_market_provider(),
        default_valuation_provider(),
        default_peer_comparison_provider(),
    )
    kernel = AcquisitionKernel(store, providers)
    manifest = build_stock_data_requirement_manifest(
        args.ticker, "A", build_stock_research_plan(args.ticker, "A")
    )
    results = []
    for item in manifest["requirements"]:
        if item["data_type"] not in MARKET_TYPES:
            continue
        result = kernel.acquire(
            requirement_from_manifest_item(item),
            mode=AcquisitionMode(args.mode),
            workflow_run_id="market-real-smoke",
        )
        results.append({
            "data_type": item["data_type"],
            "status": result.status,
            "provider_id": result.provider_id,
            "documents": result.persisted_documents,
            "facts": result.persisted_facts,
            "evidence_candidates": result.persisted_evidence_candidates,
            "dataset_state": asdict(result.dataset_state) if result.dataset_state else None,
            "errors": [dict(value) for value in result.errors],
        })
    payload = {
        "ticker": args.ticker,
        "db_path": str(db_path),
        "results": results,
        "datasets": {data_type: _latest_facts(store, args.ticker, data_type) for data_type in sorted(MARKET_TYPES)},
    }
    if args.run_workflow:
        if not args.source_db or not args.artifact_root:
            raise SystemExit("--run-workflow requires --source-db and --artifact-root")
        run = WorkflowRunner(db_path).run(
            stock_deep_dive_definition(
                artifact_root=Path(args.artifact_root).resolve(),
                source_db_path=Path(args.source_db).resolve(),
            ),
            {"ticker": args.ticker, "acquisition_mode": "refresh_if_stale"},
            run_id=args.run_id,
        )
        payload["workflow_run"] = {
            "run_id": run.get("run_id"),
            "status": run.get("status"),
            "error_code": run.get("error_code"),
            "error_message": run.get("error_message"),
            "summary": run.get("summary"),
        }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    if any(item["status"] not in {"acquired", "cache_hit"} for item in results):
        raise SystemExit(1)
    if args.run_workflow and payload["workflow_run"]["status"] != "completed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
