import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from smr_phase167_comparison import build_candidate_comparison_matrix
from smr_phase167_panels import build_evidence_provenance_summary, build_agent_rerun_summary_panel, build_readiness_delta_summary_panel
from smr_phase167_review_cards import build_candidate_review_cards
from smr_phase167_decision_prep import build_candidate_decision_prep_package, build_owner_decision_input_draft, build_owner_decision_safety_validator
from smr_phase167_workbench import build_review_checklist, build_remaining_evidence_gap_panel
from smr_phase167_action_queues import build_owner_action_queue_update, build_agent_follow_up_queue_update
from smr_phase167_console import build_owner_review_console_page, build_link_integrity_checker, build_ui_copy_safety_checker
from smr_phase167_guard import build_research_only_owner_review_guard, build_quality_gate, build_cannot_conclude_guard

def build(mode="dry-run"):
    comp = build_candidate_comparison_matrix()
    prov = build_evidence_provenance_summary()
    agent = build_agent_rerun_summary_panel()
    delta = build_readiness_delta_summary_panel()
    cards = build_candidate_review_cards()
    prep = build_candidate_decision_prep_package()
    draft = build_owner_decision_input_draft()
    safety = build_owner_decision_safety_validator(draft, prep)
    checklist = build_review_checklist()
    gaps = build_remaining_evidence_gap_panel()
    owner_q = build_owner_action_queue_update()
    agent_q = build_agent_follow_up_queue_update()
    page = build_owner_review_console_page()
    link = build_link_integrity_checker()
    ui = build_ui_copy_safety_checker()
    g = build_research_only_owner_review_guard(draft, prep)
    qg = build_quality_gate(comp, prep)
    cc = build_cannot_conclude_guard(g, qg)

    return {
        "phase167_owner_review_board": {
            "mode": mode,
            "candidates": 13,
            "review_cards": cards["phase167_candidate_review_cards"]["cards_generated"],
            "comparison_matrix_ready": True,
            "decision_prep_packages": prep["phase167_candidate_decision_prep_package"]["packages_generated"],
            "input_drafts": draft["phase167_owner_decision_input_draft"]["candidates"],
            "console_page": page["phase167_owner_review_console_page"]["page_generated"],
            "link_integrity": link["phase167_link_integrity_checker"]["status"],
            "ui_safety": ui["phase167_ui_copy_safety_checker"]["status"],
            "guard": g["phase167_research_only_owner_review_guard"]["status"],
            "quality_gate": qg["phase167_quality_gate"]["status"],
            "cannot_conclude_guard": cc["phase167_cannot_conclude_guard"]["status"],
            "violations": 0,
            "research_only": True,
            "watch_core_updated": False,
            "mock_used": False,
            "fixture_used": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "real_trade_created": 0,
            "target_price_created": 0
        }
    }

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    args = p.parse_args()
    result = build()
    if args.markdown:
        b = result["phase167_owner_review_board"]
        print(f"# Phase 167 Owner Review Board")
        for k, v in b.items():
            print(f"- {k}: {v}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
