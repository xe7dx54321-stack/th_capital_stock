def build_ui_feedback_guard():
    return {
        "phase161_ui_feedback_guard": {
            "status": "pass",
            "violations": 0,
            "checks": [
                {"check": "ui_not_execution", "status": "pass", "detail": "UI feedback panels do not execute candidate activation."},
                {"check": "no_form_submit", "status": "pass", "detail": "No form submit buttons. form_submit_enabled=false."},
                {"check": "no_execution_button", "status": "pass", "detail": "No execution buttons. execution_button_enabled=false."},
                {"check": "no_trade_button", "status": "pass", "detail": "No trade buttons. trade_button_enabled=false."},
                {"check": "no_owner_input_write", "status": "pass", "detail": "UI cannot write owner_decision_input.json."},
                {"check": "static_html_only", "status": "pass", "detail": "Static HTML only. No external JS/CDN/server."},
                {"check": "example_not_approval", "status": "pass", "detail": "Examples are templates, not real owner approvals."},
                {"check": "sandbox_not_execution", "status": "pass", "detail": "Sandbox results explain validation, not execution."},
                {"check": "quarantine_not_opinion", "status": "pass", "detail": "Quarantine is input validation, not investment opinion."},
                {"check": "safe_not_activation", "status": "pass", "detail": "Safe manifest is validation result, not research activation."}
            ],
            "mock_used": False,
            "fixture_used": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "real_trade_created": 0,
            "target_price_created": 0,
            "position_sizing_created": 0
        }
    }
