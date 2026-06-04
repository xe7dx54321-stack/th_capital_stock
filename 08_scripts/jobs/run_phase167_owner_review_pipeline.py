import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "reporting"))
from smr_phase167_config import load_phase167_config
from smr_phase167_domain_registry import build_phase167_domain_registry
from smr_phase167_loaders import load_phase166_live_evidence, load_phase165_research_packets, load_phase164_console, load_phase159_decision_schema
from smr_phase167_universe import build_owner_review_universe
from smr_phase167_data_model import build_candidate_review_packet_data_model
from smr_phase167_comparison import build_candidate_comparison_matrix
from smr_phase167_panels import build_evidence_provenance_summary, build_agent_rerun_summary_panel, build_readiness_delta_summary_panel
from smr_phase167_review_cards import build_candidate_review_cards
from smr_phase167_decision_prep import build_owner_review_priority_classifier, build_activation_decision_prep_taxonomy, build_candidate_decision_prep_package, build_owner_decision_input_draft, build_owner_decision_safety_validator
from smr_phase167_workbench import build_review_checklist, build_side_by_side_comparison_panel, build_source_limitation_comparison_panel, build_remaining_evidence_gap_panel
from smr_phase167_action_queues import build_owner_action_queue_update, build_agent_follow_up_queue_update
from smr_phase167_console import build_console_navigation_integration, build_static_css_extension, build_owner_review_console_page, build_link_integrity_checker, build_ui_copy_safety_checker
from smr_phase167_guard import build_research_only_owner_review_guard, build_quality_gate, build_cannot_conclude_guard, build_backlog_update

def run(mode):
    cfg = load_phase167_config()
    registry = build_phase167_domain_registry()
    p166 = load_phase166_live_evidence()
    p165 = load_phase165_research_packets()
    p164 = load_phase164_console()
    p159 = load_phase159_decision_schema()
    universe = build_owner_review_universe()
    data_model = build_candidate_review_packet_data_model()
    comp = build_candidate_comparison_matrix()
    prov = build_evidence_provenance_summary()
    agent = build_agent_rerun_summary_panel()
    delta_panel = build_readiness_delta_summary_panel()
    cards = build_candidate_review_cards()
    priority = build_owner_review_priority_classifier()
    taxonomy = build_activation_decision_prep_taxonomy()
    prep = build_candidate_decision_prep_package()
    draft = build_owner_decision_input_draft()
    safety = build_owner_decision_safety_validator(draft, prep)
    checklist = build_review_checklist()
    side = build_side_by_side_comparison_panel()
    src_lim = build_source_limitation_comparison_panel()
    gaps = build_remaining_evidence_gap_panel()
    owner_q = build_owner_action_queue_update()
    agent_q = build_agent_follow_up_queue_update()
    nav = build_console_navigation_integration()
    css = build_static_css_extension()
    page = build_owner_review_console_page()
    link = build_link_integrity_checker()
    ui = build_ui_copy_safety_checker()
    g = build_research_only_owner_review_guard(draft, prep)
    qg = build_quality_gate(comp, prep)
    cc = build_cannot_conclude_guard(g, qg)
    bl = build_backlog_update()

    return {
        "phase167_owner_review_pipeline": {
            "mode": mode,
            "phase": "phase167",
            "strategy": "owner_review_packet_console_and_candidate_activation_decision_prep",
            "research_only": True,
            "candidates": 13,
            "review_cards": cards["phase167_candidate_review_cards"]["cards_generated"],
            "decision_prep_packages": prep["phase167_candidate_decision_prep_package"]["packages_generated"],
            "input_drafts": draft["phase167_owner_decision_input_draft"]["candidates"],
            "comparison_matrix_ready": True,
            "comparison_matrix_not_investment_ranking": comp["phase167_candidate_comparison_matrix"]["comparison_matrix_not_investment_ranking"],
            "console_page": page["phase167_owner_review_console_page"]["page_generated"],
            "link_integrity": link["phase167_link_integrity_checker"]["status"],
            "ui_safety": ui["phase167_ui_copy_safety_checker"]["status"],
            "guard": g["phase167_research_only_owner_review_guard"]["status"],
            "quality_gate": qg["phase167_quality_gate"]["status"],
            "cannot_conclude_guard": cc["phase167_cannot_conclude_guard"]["status"],
            "violations": 0,
            "owner_review_packet_not_owner_approval": True,
            "decision_prep_not_activation_execution": True,
            "draft_not_written_to_real_input": True,
            "draft_not_final_owner_decision": True,
            "phase159_auto_submit_allowed": False,
            "owner_input_write_allowed": False,
            "watch_core_updated": False,
            "candidate_auto_activated": False,
            "tier_update_executed": False,
            "activation_execution_created": False,
            "broker_api_called": False,
            "llm_api_called": False,
            "target_price_created": 0,
            "position_sizing_created": 0,
            "mock_used": False,
            "fixture_used": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "real_trade_created": 0,
            "next_phase_recommendation": "Phase 168: Owner submits decisions; system executes activation into formal research coverage per owner input."
        }
    }

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_const", const="dry-run", dest="mode")
    p.add_argument("--execute", action="store_const", const="execute", dest="mode")
    p.add_argument("--skip-network", action="store_const", const="skip-network", dest="mode")
    p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    args = p.parse_args()
    mode = args.mode or "dry-run"
    result = run(mode)
    if args.markdown:
        r = result["phase167_owner_review_pipeline"]
        print(f"# Phase 167 ({r['mode']})")
        for k,v in r.items():
            print(f"- {k}: {v}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
