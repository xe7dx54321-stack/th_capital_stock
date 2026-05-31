import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def probe_source(source_id, mode="dry-run"):
    """Probe whether a source is actually executable."""
    probe_result = {
        "source_id": source_id,
        "probe_mode": mode,
        "probe_status": "not_probed",
        "executable": None,
        "error": None,
        "output_schema_known": False,
        "last_known_success": None,
        "last_known_failure": None
    }
    
    if mode == "dry-run":
        probe_result["probe_status"] = "dry_run_not_executed"
        probe_result["executable"] = "unknown_dry_run"
        return probe_result
    
    if mode == "skip-network":
        probe_result["probe_status"] = "skip_network_not_executed"
        probe_result["executable"] = "unknown_skip_network"
        return probe_result
    
    # In execute mode, check if source adapter exists
    adapter_paths = {
        "akshare_sina_financial": "08_scripts/lib/smr_phase80_structured_financial_metric_loader.py",
        "akshare_hk_financial": "08_scripts/lib/smr_phase83_hk_financial_adapter.py",
        "yfinance_financials": "08_scripts/lib/smr_phase83_us_financial_adapter.py",
        "phase85_cn_valuation": "08_scripts/lib/smr_phase85_cn_valuation_adapter.py",
        "phase85_hk_valuation": "08_scripts/lib/smr_phase85_hk_valuation_adapter.py",
        "phase85_us_valuation": "08_scripts/lib/smr_phase85_us_valuation_adapter.py",
        "phase86_expectation": "08_scripts/lib/smr_phase86_expectation_adapter.py",
        "phase86_pricing": "08_scripts/lib/smr_phase86_pricing_adapter.py",
        "phase87_external": "08_scripts/lib/smr_phase87_external_evidence.py",
        "phase88_connector": "08_scripts/lib/smr_phase88_connector_registry.py",
    }
    
    if source_id in adapter_paths:
        p = PROJECT_ROOT / adapter_paths[source_id]
        probe_result["executable"] = p.exists()
        probe_result["probe_status"] = "executable" if p.exists() else "adapter_missing"
        if p.exists():
            probe_result["output_schema_known"] = True
    else:
        probe_result["probe_status"] = "no_adapter_defined"
        probe_result["executable"] = False
    
    return probe_result

def run_probes(inventory, mode="dry-run"):
    sources = inventory.get("phase91_existing_source_inventory", {}).get("sources", [])
    probe_results = []
    
    stats = {"executable":0, "not_executable":0, "not_probed":0}
    for src in sources:
        r = probe_source(src["source_id"], mode)
        if r["executable"] == True: stats["executable"] += 1
        elif r["executable"] == False: stats["not_executable"] += 1
        else: stats["not_probed"] += 1
        probe_results.append(r)
    
    return {
        "phase91_source_execution_probe": {
            "generated_at": datetime.now().isoformat(),
            "probe_mode": mode,
            "sources_probed": len(probe_results),
            "probe_summary": stats,
            "probe_results": probe_results
        }
    }
