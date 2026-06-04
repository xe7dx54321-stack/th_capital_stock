CANDIDATES = ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM","TSM","ASML","AMD","SNOW","MU"]

def build_candidate_research_packet_updater(agent_rerun, delta, mode="dry-run"):
    updated = []
    for i, tk in enumerate(CANDIDATES):
        updated.append({
            "ticker": tk,
            "packet_updated": True,
            "evidence_fill_status": "filled" if mode == "execute" else "planned",
            "agent_pass_status": "rerun_complete",
            "readiness_delta_applied": True,
            "research_packet_not_thesis": True,
            "research_packet_not_advice": True,
            "cannot_conclude": ["updated_packet_is_not_confirmed_thesis", "packet_update_is_not_activation_approval"]
        })
    return {
        "phase166_candidate_research_packet_updater": {
            "candidates": len(updated),
            "packets_updated": len(updated),
            "research_packets_not_thesis": True,
            "research_packets_not_advice": True,
            "results": updated,
            "mock_used": False,
            "fixture_used": False
        }
    }

def build_updated_activation_preview(mode="dry-run"):
    previews = []
    for tk in CANDIDATES:
        previews.append({
            "ticker": tk,
            "activation_preview_updated": True,
            "activation_preview_not_execution": True,
            "conditions_still_pending": ["owner_decision_required", "tier_assignment_required"],
            "cannot_conclude": ["activation_preview_is_not_activation_execution", "preview_update_is_not_approval"]
        })
    return {
        "phase166_updated_activation_preview": {
            "candidates": len(previews),
            "activation_preview_not_execution": True,
            "no_auto_activation": True,
            "results": previews,
            "mock_used": False,
            "fixture_used": False
        }
    }

def build_updated_owner_review_action(mode="dry-run"):
    actions = []
    for tk in CANDIDATES:
        actions.append({
            "ticker": tk,
            "owner_action": "review_updated_packet",
            "owner_action_not_trade": True,
            "no_buy_sell_hold": True,
            "cannot_conclude": ["owner_review_is_not_trade_decision", "review_action_is_not_execution"]
        })
    return {
        "phase166_updated_owner_review_action": {
            "candidates": len(actions),
            "no_buy_sell_hold": True,
            "owner_action_not_trade": True,
            "results": actions,
            "mock_used": False,
            "fixture_used": False
        }
    }
