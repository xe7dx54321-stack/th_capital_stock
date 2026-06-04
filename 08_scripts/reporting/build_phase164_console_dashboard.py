import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
def main(mode="json"):
    from smr_phase164_config import load_phase164_config
    from smr_phase164_guard import build_console_guard
    from smr_phase164_quality_gate import build_quality_gate
    from smr_phase164_cannot_conclude_guard import build_cannot_conclude_guard
    config = load_phase164_config()
    output = {"phase164_dashboard": {"phase": "phase164", "strategy": config.get("strategy",""), "research_only": True, "static_html_only": True, "guard": build_console_guard()["phase164_console_guard"]["status"], "quality_gate": build_quality_gate()["phase164_quality_gate"]["status"], "cannot_conclude_guard": build_cannot_conclude_guard()["phase164_cannot_conclude_guard"]["status"], "violations": 0, "safety": {"activation_execution_allowed": False, "llm_api_enabled": False, "target_price_output_allowed": False, "mock_used": False, "fixture_used": False, "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0, "target_price_created": 0}}}
    if mode == "markdown":
        d = output["phase164_dashboard"]
        print("# Phase164 Dashboard")
        print(f"| Guard | {d['guard']} |"); print(f"| Quality Gate | {d['quality_gate']} |"); print(f"| CC Guard | {d['cannot_conclude_guard']} |")
    else: print(json.dumps(output, ensure_ascii=False, indent=2))
if __name__ == "__main__": main("markdown" if "--markdown" in sys.argv else "json")
