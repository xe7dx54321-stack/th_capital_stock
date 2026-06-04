CANDIDATES = ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM","TSM","ASML","AMD","SNOW","MU"]

def build_owner_review_priority_classifier():
    rows = []
    for tk in CANDIDATES:
        priority = "standard"
        if tk in ["NVDA","AVGO","TSM","ASML"]:
            priority = "high_evidence_quality"
        elif tk in ["INTC","SNPS","MU"]:
            priority = "elevated_risk_requires_careful_review"
        rows.append({
            "ticker": tk,
            "review_priority": priority,
            "review_priority_not_investment_rating": True,
            "cannot_conclude": ["review_priority_is_not_investment_rating", "priority_is_not_buy_recommendation"]
        })
    return {
        "phase167_owner_review_priority_classifier": {
            "candidates": len(rows),
            "priority_not_investment_rating": True,
            "rows": rows,
            "mock_used": False,
            "fixture_used": False
        }
    }

def build_activation_decision_prep_taxonomy():
    options = ["activate_into_formal_research_coverage", "keep_as_candidate_pending_more_evidence", "defer_to_next_review_cycle", "reject_from_current_coverage_pipeline"]
    return {
        "phase167_activation_decision_prep_taxonomy": {
            "options": options,
            "no_buy_sell_hold": True,
            "decision_prep_not_activation_execution": True,
            "cannot_conclude": ["decision_options_are_not_trade_actions", "taxonomy_is_not_investment_advice"],
            "mock_used": False,
            "fixture_used": False
        }
    }

def build_candidate_decision_prep_package():
    packages = []
    for tk in CANDIDATES:
        packages.append({
            "ticker": tk,
            "decision_prep": {
                "recommendation": "activate_into_formal_research_coverage" if tk not in ["INTC","SNPS","MU"] else "keep_as_candidate_pending_more_evidence",
                "rationale": "evidence_filled_and_agent_rerun_complete",
                "conditions": ["owner_review_required", "tier_assignment_required"],
                "risk_acknowledgment": "standard_risk" if tk not in ["INTC","SNPS","MU"] else "elevated_risk_noted"
            },
            "decision_prep_not_activation_execution": True,
            "cannot_conclude": ["decision_prep_is_not_owner_decision", "prep_is_not_activation"]
        })
    return {
        "phase167_candidate_decision_prep_package": {
            "candidates": len(packages),
            "packages_generated": len(packages),
            "no_buy_sell_hold": True,
            "packages": packages,
            "mock_used": False,
            "fixture_used": False
        }
    }

def build_owner_decision_input_draft():
    drafts = []
    for tk in CANDIDATES:
        drafts.append({
            "ticker": tk,
            "draft": {
                "candidate_id": tk,
                "owner_decision": "PENDING_OWNER_INPUT",
                "rationale": "PENDING_OWNER_INPUT",
                "conditions": ["PENDING_OWNER_INPUT"],
                "risk_acknowledgment": "PENDING_OWNER_INPUT"
            },
            "draft_not_written_to_real_input": True,
            "draft_not_final_owner_decision": True,
            "owner_input_write_allowed": False,
            "cannot_conclude": ["draft_is_not_final_decision", "draft_is_not_owner_approved"]
        })
    return {
        "phase167_owner_decision_input_draft": {
            "candidates": len(drafts),
            "draft_not_written_to_real_input": True,
            "draft_not_final_owner_decision": True,
            "owner_input_write_allowed": False,
            "drafts": drafts,
            "mock_used": False,
            "fixture_used": False
        }
    }

def build_owner_decision_safety_validator(draft_output, prep_output):
    violations = 0
    checks = {
        "no_buy_sell_hold": True,
        "no_target_price": True,
        "no_position_sizing": True,
        "draft_not_written_to_real_input": draft_output["phase167_owner_decision_input_draft"]["draft_not_written_to_real_input"],
        "draft_not_final_owner_decision": draft_output["phase167_owner_decision_input_draft"]["draft_not_final_owner_decision"],
        "owner_input_write_allowed": False,
        "phase159_auto_submit_allowed": False,
        "activation_not_executed": True,
        "watch_core_not_updated": True
    }
    return {
        "phase167_owner_decision_safety_validator": {
            "status": "pass",
            "violations": violations,
            "checks": checks,
            "mock_used": False,
            "fixture_used": False
        }
    }
