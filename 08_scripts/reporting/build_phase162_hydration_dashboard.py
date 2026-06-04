import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

def main(mode="json"):
    from smr_phase162_config import load_phase162_config
    from smr_phase162_guard import build_hydration_guard
    from smr_phase162_quality_gate import build_quality_gate
    from smr_phase162_cannot_conclude_guard import build_cannot_conclude_guard

    config = load_phase162_config()
    guard = build_hydration_guard()
    quality = build_quality_gate()
    cc_guard = build_cannot_conclude_guard()

    output = {
        "phase162_dashboard": {
            "phase": "phase162",
            "strategy": config.get("strategy", ""),
            "research_only": config.get("research_only", True),
            "targets": config.get("preferred_targets", 13),
            "free_sources_only": config.get("free_sources_only", True),
            "skip_network_compatible": config.get("skip_network_compatible", True),
            "guard": guard["phase162_hydration_guard"]["status"],
            "quality_gate": quality["phase162_quality_gate"]["status"],
            "cannot_conclude_guard": cc_guard["phase162_cannot_conclude_guard"]["status"],
            "violations": guard["phase162_hydration_guard"]["violations"],
            "safety": {
                "activation_execution_allowed": False,
                "tier_update_execution_allowed": False,
                "auto_add_to_watchlist_allowed": False,
                "target_price_output_allowed": False,
                "mock_used": False,
                "fixture_used": False,
                "pending_created": 0,
                "paper_order_created": 0,
                "real_trade_created": 0,
                "target_price_created": 0,
                "position_sizing_created": 0
            }
        }
    }
    if mode == "markdown":
        d = output["phase162_dashboard"]
        print("# Phase162 Dashboard")
        print(f"| Metric | Value |")
        print(f"|--------|-------|")
        print(f"| Targets | {d['targets']} |")
        print(f"| Guard | {d['guard']} |")
        print(f"| Quality Gate | {d['quality_gate']} |")
        print(f"| Cannot-conclude | {d['cannot_conclude_guard']} |")
        print(f"| Violations | {d['violations']} |")
    else:
        print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main("markdown" if "--markdown" in sys.argv else "json")
