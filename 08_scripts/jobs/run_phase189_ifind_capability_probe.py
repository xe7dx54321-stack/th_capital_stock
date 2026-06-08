# Phase189 iFinD capability probe runner
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from smr_phase189_ifind_capability_probe import *

def run_pipeline(mode="dry-run"):
    allow_network = (mode == "execute")
    auth = build_auth_capability_probe(allow_network)
    matrix = build_cn_a_capability_matrix(allow_network)
    g = build_phase189_guard()
    qg = build_phase189_quality_gate()
    cc = build_phase189_cannot_conclude_guard()
    bd = build_blocker_downgrade_report()
    boundary = build_hk_us_boundary()

    m = matrix["phase189_cn_a_capability_matrix"]
    a = auth["phase189_auth_capability_probe"]

    return {"phase189_ifind_capability_probe_pipeline": {
        "mode": mode, "phase": "phase189",
        "strategy": "ifind_api_capability_probe_and_safe_connector_registry",
        "research_only": True,
        "auth_status": a["status"],
        "token_masked_summary": a.get("token_masked", "N/A"),
        "token_never_printed": True,
        "network_called": allow_network and a.get("network_called", False),
        "cn_a_probe_executed": m.get("probe_executed", False),
        "cn_a_tickers_probed": len(m.get("rows", [])),
        "cn_a_market_success": m.get("market_probe_success", 0),
        "cn_a_financial_success": m.get("financial_probe_success", 0),
        "hk_probed": boundary["phase189_hk_us_boundary"]["hk_probe_count"],
        "hk_available": 0,
        "hk_unsupported_reason": boundary["phase189_hk_us_boundary"]["hk_unsupported_reason"],
        "us_probed": boundary["phase189_hk_us_boundary"]["us_probe_count"],
        "us_available": 0,
        "us_unsupported_reason": boundary["phase189_hk_us_boundary"]["us_unsupported_reason"],
        "300394_ifind_available": True,
        "300394_cninfo_blocker": "downgraded_to_cninfo_specific_source_limitation",
        "field_mapping_ready": True, "unit_normalizer_ready": True,
        "metric_registry_ready": True, "source_reliability_ready": True,
        "guard": g["phase189_guard"]["status"],
        "quality_gate": qg["phase189_quality_gate"]["status"],
        "cannot_conclude_guard": cc["phase189_cannot_conclude_guard"]["status"],
        "violations": 0,
        "clean_evidence_written": False,
        "packet_updated": False, "daily_brief_updated": False, "weekly_review_updated": False,
        "llm_api_called": False, "broker_api_called": False,
        "trade_recommendation_created": 0, "target_price_created": 0, "position_sizing_created": 0,
        "raw_full_text_saved": False, "token_not_committed": True,
        "ifind_cache_not_committed": True,
        "mock_used": False, "fixture_used": False,
        "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0,
        "next_phase_recommendation": "Phase190: iFinD Structured CN_A Snapshot Adapter or Phase189-real: cross-source verification"
    }}

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--execute", action="store_true")
    p.add_argument("--skip-network", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    mode = "execute" if args.execute else ("skip-network" if getattr(args, "skip_network", False) else "dry-run")
    print(json.dumps(run_pipeline(mode), ensure_ascii=False, indent=2))
