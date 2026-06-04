import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

def run(mode="dry-run"):
    from smr_phase161_config import load_phase161_config
    from smr_phase161_domain_registry import build_phase161_domain_registry
    from smr_phase161_loaders import load_phase160_context, load_phase159_context, load_phase158_context, load_phase156_context, load_phase153_context
    from smr_phase161_ui_data_model import build_example_pack_ui_model
    from smr_phase161_panels import (build_example_library_panel, build_sandbox_result_panel,
                                      build_quarantine_explanation_panel, build_safe_manifest_explanation_panel,
                                      build_phase159_feedback_panel, build_workflow_instruction_panel,
                                      build_next_command_panel, build_ui_safety_copy, build_link_integrity)
    from smr_phase161_console import build_console_page_html, build_nav_integration, build_css_extension
    from smr_phase161_guard import build_ui_feedback_guard
    from smr_phase161_quality_gate import build_quality_gate
    from smr_phase161_cannot_conclude_guard import build_cannot_conclude_guard
    from smr_phase161_backlog import build_backlog_update

    config = load_phase161_config()
    domain = build_phase161_domain_registry()
    ctx160 = load_phase160_context()
    ctx159 = load_phase159_context()
    ctx158 = load_phase158_context()
    ctx156 = load_phase156_context()
    ctx153 = load_phase153_context()

    model = build_example_pack_ui_model()
    example_panel = build_example_library_panel(model)
    sandbox_panel = build_sandbox_result_panel(model)
    quarantine_panel = build_quarantine_explanation_panel()
    safe_manifest_panel = build_safe_manifest_explanation_panel()
    phase159_panel = build_phase159_feedback_panel(model)
    workflow_panel = build_workflow_instruction_panel()
    command_panel = build_next_command_panel()
    safety_copy = build_ui_safety_copy()
    link_integrity = build_link_integrity()

    console = build_console_page_html()
    nav = build_nav_integration()
    css = build_css_extension()

    guard = build_ui_feedback_guard()
    quality = build_quality_gate()
    cc_guard = build_cannot_conclude_guard()
    backlog = build_backlog_update()

    if mode == "execute":
        from pathlib import Path
        out_path = Path(__file__).resolve().parent.parent.parent / "09_runbooks" / "generated" / "phase161_submission_feedback_console.html"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(console["phase161_console_page"]["page_html"])

    sandbox = model["phase161_ui_data_model"]["sandbox_summary"]
    phase159_status = model["phase161_ui_data_model"]["phase159_status"]

    output = {
        "phase161_ui_feedback_pipeline": {
            "mode": mode,
            "phase": "phase161",
            "strategy": config.get("strategy", ""),
            "research_only": True,
            "example_library": {"valid": 5, "invalid": 5, "total": 10},
            "sandbox_safe": sandbox["total_safe"],
            "sandbox_invalid": sandbox["total_invalid"],
            "sandbox_quarantine": sandbox["total_quarantine"],
            "sandbox_execution": sandbox["total_execution"],
            "phase159_input_present": phase159_status["owner_input_present"],
            "ui_safety_copy": safety_copy["phase161_ui_safety_copy"]["overall_status"],
            "link_integrity": link_integrity["phase161_link_integrity"]["overall_status"],
            "console_page_generated": True,
            "console_html_saved": mode == "execute",
            "console_path_ignored": True,
            "guard": guard["phase161_ui_feedback_guard"]["status"],
            "quality_gate": quality["phase161_quality_gate"]["status"],
            "cannot_conclude_guard": cc_guard["phase161_cannot_conclude_guard"]["status"],
            "violations": guard["phase161_ui_feedback_guard"]["violations"],
            "static_html_only": True,
            "external_js_allowed": False,
            "execution_button_enabled": False,
            "trade_button_enabled": False,
            "form_submit_enabled": False,
            "ui_feedback_not_execution": True,
            "example_not_approval": True,
            "safe_manifest_not_activation": True,
            "quarantine_not_opinion": True,
            "watch_core_updated": False,
            "candidate_auto_activated": False,
            "tier_update_executed": False,
            "activation_execution_created": False,
            "mock_used": False,
            "fixture_used": False,
            "raw_saved": False,
            "ocr_used": False,
            "browser_automation_used": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "real_trade_created": 0,
            "target_price_created": 0,
            "position_sizing_created": 0,
            "trade_recommendation_created": 0,
            "broker_api_called": False,
            "next_phase_recommendation": backlog["phase161_backlog"]["next_phase_recommendation"]
        }
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return output

if __name__ == "__main__":
    mode = "dry-run"
    if "--execute" in sys.argv:
        mode = "execute"
    elif "--skip-network" in sys.argv:
        mode = "skip-network"
    run(mode)
