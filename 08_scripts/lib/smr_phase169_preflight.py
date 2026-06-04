CANDIDATES = ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM","TSM","ASML","AMD","SNOW","MU"]
VALID_DECISIONS = ["activate_into_formal_research_coverage","keep_as_candidate_pending_more_evidence","defer_to_next_review_cycle","reject_from_current_coverage_pipeline"]
TRADE_TERMS = ["buy","sell","hold","short","add","reduce","target_price","position","allocation","weight","overweight","underweight","entry","exit","stop_loss","take_profit"]

def build_preflight_validator(draft_input=None):
    if draft_input is None:
        return {"phase169_preflight_validator":{"status":"no_draft","violations":0,"checks":{"draft_exists":False},"mock_used":False,"fixture_used":False}}
    violations = 0
    issues = []
    decisions = draft_input.get("decisions",[])
    covered_ids = [d.get("candidate_id","") for d in decisions]
    for tk in CANDIDATES:
        if tk not in covered_ids:
            issues.append(f"missing_candidate:{tk}")
            violations += 1
    for d in decisions:
        cid = d.get("candidate_id","")
        od = d.get("owner_decision","")
        rationale = d.get("rationale","")
        risk = d.get("risk_acknowledgment","")
        if od not in VALID_DECISIONS:
            issues.append(f"invalid_decision:{cid}:{od}")
            violations += 1
        for term in TRADE_TERMS:
            if term.lower() in rationale.lower() or term.lower() in risk.lower():
                issues.append(f"trade_term_found:{cid}:{term}")
                violations += 1
        if od in ["buy","sell","hold","short"]:
            issues.append(f"trade_action_as_decision:{cid}:{od}")
            violations += 1
    return {"phase169_preflight_validator":{
        "status":"pass" if violations==0 else "fail",
        "violations":violations,"issues":issues,
        "checks":{
            "draft_exists":True,
            "all_candidates_covered":len(covered_ids)>=len(CANDIDATES),
            "no_invalid_decisions":all(d.get("owner_decision","") in VALID_DECISIONS for d in decisions),
            "no_trade_terms":not any(any(t.lower() in d.get("rationale","").lower() or t.lower() in d.get("risk_acknowledgment","").lower() for t in TRADE_TERMS) for d in decisions),
            "no_buy_sell_hold":not any(d.get("owner_decision","") in ["buy","sell","hold","short"] for d in decisions)
        },
        "preflight_not_real_submission":True,"mock_used":False,"fixture_used":False
    }}

def build_sandbox_simulation(draft_input=None):
    if draft_input is None:
        return {"phase169_sandbox_simulation":{"status":"no_draft","simulated_outcome":"no_input","watch_core_would_update":False,"mock_used":False,"fixture_used":False}}
    activated = sum(1 for d in draft_input.get("decisions",[]) if d.get("owner_decision")=="activate_into_formal_research_coverage")
    return {"phase169_sandbox_simulation":{
        "status":"simulated","simulated_outcome":f"would_activate_{activated}_candidates",
        "activated_would_be":activated,"watch_core_would_update":False,
        "sandbox_not_real_execution":True,"sandbox_output_not_committed":True,
        "cannot_conclude":["sandbox_is_not_real_execution","simulated_outcome_is_not_committed"],
        "mock_used":False,"fixture_used":False
    }}
