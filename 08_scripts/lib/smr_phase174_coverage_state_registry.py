# Phase174 coverage state registry
import json, os

CANDIDATES = ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM","TSM","ASML","AMD","SNOW","MU"]
VALID_DECISIONS = ["activate_into_formal_research_coverage","keep_as_candidate_pending_more_evidence","defer_to_next_review_cycle","reject_from_current_coverage_pipeline"]
DECISION_TO_TIER = {
    "activate_into_formal_research_coverage":"formal_research_coverage",
    "keep_as_candidate_pending_more_evidence":"candidate_pending",
    "defer_to_next_review_cycle":"deferred_review",
    "reject_from_current_coverage_pipeline":"rejected"
}

def load_owner_decision_input():
    p = "09_runbooks/generated/phase168_owner_decision_manual_submission/owner_decision_input.json"
    if not os.path.exists(p):
        return None
    with open(p,"r",encoding="utf-8") as f:
        return json.load(f)

def build_coverage_state_registry():
    owner_input = load_owner_decision_input()
    if owner_input is None:
        return {"phase174_coverage_state_registry":{
            "status":"no_owner_input_found","coverage_state_count":0,"activated_count":0,
            "kept_count":0,"deferred_count":0,"rejected_count":0,
            "state_path_ignored":True,"coverage_state_only":True,
            "entries":[],"mock_used":False,"fixture_used":False
        }}
    decisions = owner_input.get("decisions",[])
    entries = []
    activated = kept = deferred = rejected = 0
    for d in decisions:
        cid = d.get("candidate_id","")
        od = d.get("owner_decision","")
        tier = DECISION_TO_TIER.get(od,"unknown")
        entry = {
            "candidate_id":cid,"owner_decision":od,"coverage_tier":tier,
            "rationale":d.get("rationale",""),
            "conditions":d.get("conditions",[]),
            "risk_acknowledgment":d.get("risk_acknowledgment",""),
            "daily_monitoring_eligible":tier=="formal_research_coverage",
            "weekly_review_eligible":tier in ["formal_research_coverage","candidate_pending"],
            "agent_task_eligible":tier in ["formal_research_coverage","candidate_pending","deferred_review"],
            "manual_adjustment_allowed":True
        }
        if tier == "formal_research_coverage": activated += 1
        elif tier == "candidate_pending": kept += 1
        elif tier == "deferred_review": deferred += 1
        elif tier == "rejected": rejected += 1
        entries.append(entry)
    return {"phase174_coverage_state_registry":{
        "status":"state_loaded","coverage_state_count":len(entries),
        "activated_count":activated,"kept_count":kept,
        "deferred_count":deferred,"rejected_count":rejected,
        "state_path_ignored":True,"coverage_state_only":True,
        "coverage_state_not_trade":True,
        "entries":entries,"mock_used":False,"fixture_used":False
    }}

def write_coverage_state_to_generated():
    registry = build_coverage_state_registry()
    os.makedirs("09_runbooks/generated/phase174_coverage_state",exist_ok=True)
    p = "09_runbooks/generated/phase174_coverage_state/coverage_state_registry.json"
    with open(p,"w",encoding="utf-8") as f:
        json.dump(registry,f,ensure_ascii=False,indent=2)
    return {"written":True,"path":p,"path_ignored":True}
