import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
def main(mode="json"):
    from smr_phase163_config import load_phase163_config
    from smr_phase163_guard import build_live_hydration_guard
    from smr_phase163_quality_gate import build_quality_gate
    from smr_phase163_cannot_conclude_guard import build_cannot_conclude_guard
    config = load_phase163_config()
    output = {"phase163_dashboard": {"phase": "phase163", "strategy": config.get("strategy", ""), "research_only": True, "targets": config.get("preferred_targets", 13), "execute_network_allowed": config.get("execute_network_allowed", False), "skip_network_supported": True, "free_sources_only": True, "guard": build_live_hydration_guard()["phase163_live_hydration_guard"]["status"], "quality_gate": build_quality_gate()["phase163_quality_gate"]["status"], "cannot_conclude_guard": build_cannot_conclude_guard()["phase163_cannot_conclude_guard"]["status"], "violations": 0, "safety": {"activation_execution_allowed": False, "target_price_output_allowed": False, "raw_save_allowed": False, "mock_used": False, "fixture_used": False, "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0, "target_price_created": 0, "position_sizing_created": 0}}}
    if mode == "markdown":
        d = output["phase163_dashboard"]
        print("# Phase163 Dashboard")
        print(f"| Metric | Value |")
        print(f"|--------|-------|")
        print(f"| Targets | {d['targets']} |"); print(f"| Guard | {d['guard']} |"); print(f"| Quality Gate | {d['quality_gate']} |"); print(f"| Cannot-conclude | {d['cannot_conclude_guard']} |")
    else: print(json.dumps(output, ensure_ascii=False, indent=2))
if __name__ == "__main__": main("markdown" if "--markdown" in sys.argv else "json")
