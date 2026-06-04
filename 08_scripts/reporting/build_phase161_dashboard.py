import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

def main(mode="json"):
    from smr_phase161_config import load_phase161_config
    from smr_phase161_ui_data_model import build_example_pack_ui_model
    from smr_phase161_guard import build_ui_feedback_guard
    from smr_phase161_quality_gate import build_quality_gate
    from smr_phase161_cannot_conclude_guard import build_cannot_conclude_guard

    config = load_phase161_config()
    model = build_example_pack_ui_model()
    guard = build_ui_feedback_guard()
    quality = build_quality_gate()
    cc_guard = build_cannot_conclude_guard()

    sandbox = model["phase161_ui_data_model"]["sandbox_summary"]
    phase159 = model["phase161_ui_data_model"]["phase159_status"]

    output = {
        "phase161_dashboard": {
            "phase": "phase161",
            "strategy": config.get("strategy", ""),
            "research_only": config.get("research_only", True),
            "example_library": {"valid": 5, "invalid": 5, "total": 10},
            "sandbox": sandbox,
            "phase159_status": phase159,
            "guard": guard["phase161_ui_feedback_guard"]["status"],
            "quality_gate": quality["phase161_quality_gate"]["status"],
            "cannot_conclude_guard": cc_guard["phase161_cannot_conclude_guard"]["status"],
            "violations": guard["phase161_ui_feedback_guard"]["violations"],
            "safety": {
                "static_html_only": config.get("static_html_only", True),
                "external_js_allowed": config.get("external_js_allowed", False),
                "execution_button_enabled": config.get("execution_button_enabled", False),
                "trade_button_enabled": config.get("trade_button_enabled", False),
                "form_submit_enabled": config.get("form_submit_enabled", False),
                "mock_used": False,
                "fixture_used": False,
                "raw_saved": False,
                "ocr_used": False,
                "browser_automation_used": False,
                "pending_created": 0,
                "paper_order_created": 0,
                "real_trade_created": 0,
                "target_price_created": 0,
                "position_sizing_created": 0
            }
        }
    }
    if mode == "markdown":
        d = output["phase161_dashboard"]
        print("# Phase161 Dashboard")
        print(f"| Metric | Value |")
        print(f"|--------|-------|")
        print(f"| Guard | {d['guard']} |")
        print(f"| Quality Gate | {d['quality_gate']} |")
        print(f"| Cannot-conclude | {d['cannot_conclude_guard']} |")
        print(f"| Violations | {d['violations']} |")
        print(f"| Sandbox Safe | {sandbox['total_safe']} |")
        print(f"| Sandbox Invalid | {sandbox['total_invalid']} |")
        print(f"| Sandbox Execution | {sandbox['total_execution']} |")
    else:
        print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    mode = "json"
    if "--markdown" in sys.argv:
        mode = "markdown"
    main(mode)
