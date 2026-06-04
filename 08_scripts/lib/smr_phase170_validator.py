CANDIDATES = ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM","TSM","ASML","AMD","SNOW","MU"]
VALID_DECISIONS = ["activate_into_formal_research_coverage","keep_as_candidate_pending_more_evidence","defer_to_next_review_cycle","reject_from_current_coverage_pipeline"]
TRADE_TERMS = ["buy","sell","hold","short","add","reduce","target_price","position_size","allocation","overweight","underweight","entry","exit","stop_loss","take_profit"]

def validate_owner_input(owner_input):
    if owner_input is None:
        return {"phase170_schema_validator":{"status":"no_input","violations":0,"valid_entries":0,"quarantined_entries":0,"missing_entries":13,"manifest":[],"quarantined":[],"valid":[],"safety_validation":"pass","mock_used":False,"fixture_used":False}}
    decisions = owner_input.get("decisions",[])
    valid_entries = []
    quarantined = []
    for d in decisions:
        cid = d.get("candidate_id",""); od = d.get("owner_decision","")
        rationale = d.get("rationale",""); risk = d.get("risk_acknowledgment","")
        issues = []
        if cid not in CANDIDATES: issues.append("unknown_candidate")
        if od not in VALID_DECISIONS: issues.append("invalid_decision")
        if not (rationale or "").strip(): issues.append("missing_rationale")
        for t in TRADE_TERMS:
            if t.lower() in rationale.lower() or t.lower() in risk.lower():
                issues.append(f"trade_term:{t}")
        if od in ["buy","sell","hold","short"]: issues.append("trade_action_as_decision")
        entry = {"candidate_id":cid,"owner_decision":od,"rationale":rationale,"conditions":d.get("conditions",[]),"risk_acknowledgment":risk}
        if issues:
            entry["quarantine_reasons"] = issues; quarantined.append(entry)
        else:
            valid_entries.append(entry)
    covered = set(e["candidate_id"] for e in valid_entries)
    missing = [tk for tk in CANDIDATES if tk not in covered]
    manifest = [{"candidate_id":e["candidate_id"],"decision":e["owner_decision"],"status":"valid"} for e in valid_entries]
    for e in quarantined: manifest.append({"candidate_id":e["candidate_id"],"decision":e["owner_decision"],"status":"quarantined","reasons":e["quarantine_reasons"]})
    for tk in missing: manifest.append({"candidate_id":tk,"decision":"missing","status":"missing"})
    violations = len(quarantined) + len(missing)
    return {"phase170_schema_validator":{
        "status":"pass" if violations==0 else ("partial" if len(valid_entries)>0 else "fail"),
        "violations":violations,"valid_entries":len(valid_entries),"quarantined_entries":len(quarantined),"missing_entries":len(missing),
        "manifest":manifest,"quarantined":quarantined,"valid":valid_entries,
        "safety_validation":"pass" if len([e for e in quarantined if any("trade" in r for r in e.get("quarantine_reasons",[]))])==0 else "trade_terms_blocked",
        "mock_used":False,"fixture_used":False
    }}

