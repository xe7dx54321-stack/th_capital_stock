import json, sys, os
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))

def build():
    from smr_phase156_loaders import load_ready_for_owner_candidates, load_phase152_scores
    from smr_phase156_activation_review_input import build_activation_review_input
    from smr_phase156_decision_intake import build_owner_decision_intake
    from smr_phase156_decision_validator import validate_owner_decisions
    from smr_phase156_decision_classifier import classify_owner_decisions
    from smr_phase156_activation_plan import build_research_activation_plan
    from smr_phase156_post_approval_tasks import build_post_approval_tasks
    from smr_phase156_evidence_followup import build_evidence_followup_tasks
    from smr_phase156_risk_followup import build_risk_followup_tasks
    from smr_phase156_judge_final_review import build_judge_final_review
    from smr_phase156_tier_update_proposal import build_tier_update_proposal
    from smr_phase156_watch_core_guard import run_watch_core_update_guard
    from smr_phase156_audit_log import build_audit_log

    candidates = load_ready_for_owner_candidates()
    scores = {s["ticker"]:s["composite_score"] for s in load_phase152_scores()}
    enriched = [{"ticker":c["ticker"],"name":c["name"],"market":c["market"],"composite_score":scores.get(c["ticker"],0)} for c in candidates]
    review_input = build_activation_review_input(enriched)
    intake = build_owner_decision_intake(enriched)
    validator = validate_owner_decisions(intake["phase156_decision_intake"]["templates"])
    classified = classify_owner_decisions(review_input["phase156_activation_review_input"])
    activation_plan = build_research_activation_plan(intake["phase156_decision_intake"]["templates"])
    post_approval = build_post_approval_tasks(activation_plan["phase156_activation_plan"])
    ev_followup = build_evidence_followup_tasks(classified["phase156_decision_classifier"]["summary"])
    risk_followup = build_risk_followup_tasks(classified["phase156_decision_classifier"]["summary"])
    judge = build_judge_final_review(classified)
    tier_prop = build_tier_update_proposal(classified)
    wc_guard = run_watch_core_update_guard()
    audit = build_audit_log(intake["phase156_decision_intake"]["templates"])

    return {"phase156_activation_board":{
        "review_input":review_input["phase156_activation_review_input"],
        "decision_intake":intake["phase156_decision_intake"],
        "decision_classifier":classified["phase156_decision_classifier"],
        "activation_plan":activation_plan["phase156_activation_plan"],
        "post_approval":post_approval["phase156_post_approval_tasks"],
        "evidence_followup":ev_followup["phase156_evidence_followup"],
        "risk_followup":risk_followup["phase156_risk_followup"],
        "judge_review":judge["phase156_judge_final_review"],
        "tier_proposal":tier_prop["phase156_tier_update_proposal"],
        "watch_core_guard":wc_guard["phase156_watch_core_guard"],
        "audit_log":audit["phase156_audit_log"],
        "research_only":True,"owner_decision_required":True,"auto_approval_allowed":False,
        "watch_core_updated":False,"candidate_auto_activated":False,
        "mock_used":False,"fixture_used":False,
    }}

if __name__ == "__main__":
    print(json.dumps(build(), indent=2, ensure_ascii=False, default=str))
