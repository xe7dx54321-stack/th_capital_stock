CANDIDATES = ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM","TSM","ASML","AMD","SNOW","MU"]
VALID_DECISIONS = ["activate_into_formal_research_coverage","keep_as_candidate_pending_more_evidence","defer_to_next_review_cycle","reject_from_current_coverage_pipeline"]

def build_owner_decision_input_validator(submitted_input=None):
    if submitted_input is None:
        return {"phase168_owner_decision_input_validator":{"status":"no_input_submitted","violations":0,"checks":{"input_exists":False,"all_candidates_covered":False,"decisions_valid":False,"no_trade_language":True,"input_path_ignored":True},"mock_used":False,"fixture_used":False}}
    violations = 0
    decisions = submitted_input.get("decisions", [])
    covered = [d.get("candidate_id") for d in decisions]
    valid_decisions = all(d.get("owner_decision") in VALID_DECISIONS for d in decisions)
    no_trade = not any(d.get("owner_decision","") in ["buy","sell","hold"] for d in decisions)
    all_covered = set(covered) == set(CANDIDATES)
    return {"phase168_owner_decision_input_validator":{"status":"pass" if (all_covered and valid_decisions and no_trade) else "fail","violations":0 if (all_covered and valid_decisions and no_trade) else 1,"checks":{"input_exists":True,"all_candidates_covered":all_covered,"decisions_valid":valid_decisions,"no_trade_language":no_trade,"no_buy_sell_hold_found":no_trade,"input_path_ignored":True},"mock_used":False,"fixture_used":False}}
