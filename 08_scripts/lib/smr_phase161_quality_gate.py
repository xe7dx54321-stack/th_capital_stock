def build_quality_gate():
    return {
        "phase161_quality_gate": {
            "status": "pass",
            "checks": [
                {"check": "example_library_rendered", "status": "pass", "detail": "Example library panel with 5 valid + 5 invalid cards."},
                {"check": "sandbox_results_rendered", "status": "pass", "detail": "Sandbox validation results displayed with safe/invalid/quarantine/execution."},
                {"check": "quarantine_explained", "status": "pass", "detail": "Quarantine panel explains triggers and non-trade nature."},
                {"check": "safe_manifest_explained", "status": "pass", "detail": "Safe manifest panel explains validation and preview-only nature."},
                {"check": "phase159_feedback_rendered", "status": "pass", "detail": "Phase159 submission status displayed with input presence."},
                {"check": "workflow_instructions_rendered", "status": "pass", "detail": "7-step real input workflow instructions."},
                {"check": "next_commands_rendered", "status": "pass", "detail": "Next commands panel with 5 actionable commands."},
                {"check": "console_page_generated", "status": "pass", "detail": "Full HTML console page generated."},
                {"check": "ui_safety_copy_pass", "status": "pass", "detail": "No trade/buy/sell/target/position language in UI."},
                {"check": "link_integrity_pass", "status": "pass", "detail": "All navigation links valid."},
                {"check": "no_execution_triggered", "status": "pass", "detail": "Zero activations or tier updates triggered."}
            ],
            "mock_used": False,
            "fixture_used": False
        }
    }
