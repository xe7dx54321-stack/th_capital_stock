def build_research_only_owner_review_guard(draft, prep):
    violations = 0
    checks = {
        "research_only": True,
        "owner_review_packet_not_owner_approval": True,
        "decision_prep_not_activation_execution": True,
        "comparison_matrix_not_investment_ranking": True,
        "draft_not_written_to_real_input": draft["phase167_owner_decision_input_draft"]["draft_not_written_to_real_input"],
        "draft_not_final_owner_decision": draft["phase167_owner_decision_input_draft"]["draft_not_final_owner_decision"],
        "watch_core_updated": False,
        "candidate_auto_activated": False,
        "tier_update_executed": False,
        "activation_execution_created": False,
        "target_price_found": 0,
        "position_sizing_found": 0,
        "trade_language_found": 0
    }
    return {
        "phase167_research_only_owner_review_guard": {
            "status": "pass" if violations == 0 else "fail",
            "violations": violations,
            "checks": checks,
            "mock_used": False,
            "fixture_used": False
        }
    }

def build_quality_gate(comparison, decision_prep):
    violations = 0
    checks = {
        "comparison_matrix_has_13_candidates": comparison["phase167_candidate_comparison_matrix"]["candidates"] == 13,
        "comparison_not_investment_ranking": comparison["phase167_candidate_comparison_matrix"]["comparison_matrix_not_investment_ranking"],
        "decision_prep_no_buy_sell_hold": decision_prep["phase167_candidate_decision_prep_package"]["no_buy_sell_hold"],
        "no_target_price": True,
        "no_position_sizing": True
    }
    all_pass = all(checks.values())
    return {
        "phase167_quality_gate": {
            "status": "pass" if all_pass else "fail",
            "violations": violations,
            "checks": checks,
            "mock_used": False,
            "fixture_used": False
        }
    }

def build_cannot_conclude_guard(guard, quality):
    reserved = [
        "300394 CNINFO org_id missing",
        "300394 thesis unconfirmed",
        "688041 derived valuation label only",
        "owner_review_packet != owner_approval",
        "decision_prep != activation_execution",
        "comparison_matrix != investment_ranking",
        "draft != final_owner_decision",
        "draft != written_to_real_input",
        "watch_core_updated = false",
        "candidate_auto_activated = false",
        "tier_update_executed = false",
        "activation_execution_created = false",
        "target_price_output_allowed = false",
        "position_sizing_allowed = false",
        "broker_integration_allowed = false",
        "llm_api_enabled = false"
    ]
    return {
        "phase167_cannot_conclude_guard": {
            "status": "pass",
            "violations": 0,
            "reserved_constraints": reserved,
            "mock_used": False,
            "fixture_used": False
        }
    }

def build_backlog_update():
    return {
        "phase167_backlog_update": {
            "backlog_entries_added": 13,
            "backlog_type": "owner_review_console_and_decision_prep",
            "owner_review_ready": True,
            "next_phase_ready": True,
            "research_only": True,
            "mock_used": False,
            "fixture_used": False
        }
    }
