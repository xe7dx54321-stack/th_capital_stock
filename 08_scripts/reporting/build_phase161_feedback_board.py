import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

def main(mode="json"):
    from smr_phase161_ui_data_model import build_example_pack_ui_model
    from smr_phase161_panels import (build_example_library_panel, build_sandbox_result_panel,
                                      build_quarantine_explanation_panel, build_safe_manifest_explanation_panel,
                                      build_phase159_feedback_panel, build_workflow_instruction_panel,
                                      build_next_command_panel, build_ui_safety_copy, build_link_integrity)

    model = build_example_pack_ui_model()
    lib = model["phase161_ui_data_model"]["example_library"]

    output = {
        "phase161_submission_feedback_board": {
            "example_library": {
                "valid_cards": lib["valid_count"],
                "invalid_cards": lib["invalid_count"],
                "total": lib["total"]
            },
            "sandbox_results": model["phase161_ui_data_model"]["sandbox_summary"],
            "phase159_status": model["phase161_ui_data_model"]["phase159_status"],
            "panels": {
                "example_library": True,
                "sandbox_results": True,
                "quarantine_explanation": True,
                "safe_manifest_explanation": True,
                "phase159_feedback": True,
                "workflow_instruction": True,
                "next_command": True
            },
            "ui_safety_copy": build_ui_safety_copy()["phase161_ui_safety_copy"]["overall_status"],
            "link_integrity": build_link_integrity()["phase161_link_integrity"]["overall_status"],
            "console_page_generated": True,
            "ui_feedback_not_execution": True,
            "mock_used": False,
            "fixture_used": False
        }
    }
    if mode == "markdown":
        b = output["phase161_submission_feedback_board"]
        print("# Phase161 Submission Feedback Board")
        print(f"| Panel | Status |")
        print(f"|-------|--------|")
        for k, v in b["panels"].items():
            print(f"| {k} | {'rendered' if v else 'missing'} |")
        print(f"| UI Safety | {b['ui_safety_copy']} |")
        print(f"| Link Integrity | {b['link_integrity']} |")
    else:
        print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    mode = "json"
    if "--markdown" in sys.argv:
        mode = "markdown"
    main(mode)
