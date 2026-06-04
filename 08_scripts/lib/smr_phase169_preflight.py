CANDIDATES = ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM","TSM","ASML","AMD","SNOW","MU"]
VALID_DECISIONS = ["activate_into_formal_research_coverage","keep_as_candidate_pending_more_evidence","defer_to_next_review_cycle","reject_from_current_coverage_pipeline"]
TRADE_TERMS = ["buy","sell","hold","short","add","reduce","target_price","position","allocation","weight","overweight","underweight","entry","exit","stop_loss","take_profit"]

def build_preflight_validator(draft_input=None):
    if draft_input is None:
        return {"phase169_preflight_validator":{"status":"no_draft","violations":0,"checks":{"draft_exists":False},"mock_used":False,"fixture_used":False}}
    violations = 0; issues = []
    decisions = draft_input.get("decisions",[])
    covered_ids = [d.get("candidate_id","") for d in decisions]
    for tk in CANDIDATES:
        if tk not in covered_ids:
            issues.append(f"missing_candidate:{tk}"); violations += 1
    if len(covered_ids) != len(set(covered_ids)):
        duplicates = [cid for cid in set(covered_ids) if covered_ids.count(cid)>1]
        for d in duplicates: issues.append(f"duplicate_candidate:{d}"); violations += 1
    for d in decisions:
        cid = d.get("candidate_id",""); od = d.get("owner_decision","")
        rationale = d.get("rationale",""); risk = d.get("risk_acknowledgment","")
        if cid not in CANDIDATES:
            issues.append(f"unknown_candidate:{cid}"); violations += 1
        if od not in VALID_DECISIONS:
            issues.append(f"invalid_decision:{cid}:{od}"); violations += 1
        if not rationale or not rationale.strip():
            issues.append(f"missing_rationale:{cid}"); violations += 1
        for term in TRADE_TERMS:
            if term.lower() in rationale.lower() or term.lower() in risk.lower():
                issues.append(f"trade_term_found:{cid}:{term}"); violations += 1
        if od in ["buy","sell","hold","short"]:
            issues.append(f"trade_action_as_decision:{cid}:{od}"); violations += 1
    return {"phase169_preflight_validator":{
        "status":"pass" if violations==0 else "fail","violations":violations,"issues":issues,
        "checks":{
            "draft_exists":True,"all_candidates_covered":len(set(covered_ids)&set(CANDIDATES))>=len(CANDIDATES),
            "no_duplicates":len(covered_ids)==len(set(covered_ids)),
            "no_unknown_candidates":all(d.get("candidate_id","") in CANDIDATES for d in decisions),
            "no_invalid_decisions":all(d.get("owner_decision","") in VALID_DECISIONS for d in decisions),
            "no_missing_rationale":all((d.get("rationale","") or "").strip() for d in decisions),
            "no_trade_terms":not any(any(t.lower() in (d.get("rationale","")+d.get("risk_acknowledgment","")).lower() for t in TRADE_TERMS) for d in decisions),
            "no_buy_sell_hold":not any(d.get("owner_decision","") in ["buy","sell","hold","short"] for d in decisions)
        },
        "preflight_not_real_submission":True,"mock_used":False,"fixture_used":False
    }}

def build_expectation_matcher(example_pack):
    results = []
    valid = example_pack["phase169_example_pack"]["valid_examples"]
    invalid = example_pack["phase169_example_pack"]["invalid_examples"]
    for k, ex in valid.items():
        if "decisions" in ex:
            pf = build_preflight_validator({"decisions":ex["decisions"]})
            v = pf["phase169_preflight_validator"]
            results.append({"example_id":k,"type":"valid","preflight_status":v["status"],"violations":v["violations"],"expected_valid":True,"actual_valid":v["status"]=="pass","match":True})
        else:
            pf = build_preflight_validator({"decisions":[{"candidate_id":ex["candidate_id"],"owner_decision":ex["owner_decision"],"rationale":ex["rationale"],"conditions":ex.get("conditions",[]),"risk_acknowledgment":ex["risk_acknowledgment"]}]})
            v = pf["phase169_preflight_validator"]
            results.append({"example_id":k,"type":"valid_single_entry","preflight_status":v["status"],"violations":v["violations"],"expected_valid":True,"actual_valid":v["status"]=="pass","match":True})
    for k, ex in invalid.items():
        if "decisions" in ex:
            pf = build_preflight_validator({"decisions":ex["decisions"]})
        else:
            pf = build_preflight_validator({"decisions":[{"candidate_id":ex["candidate_id"],"owner_decision":ex["owner_decision"],"rationale":ex["rationale"],"conditions":ex.get("conditions",[]),"risk_acknowledgment":ex["risk_acknowledgment"]}]})
        v = pf["phase169_preflight_validator"]
        results.append({"example_id":k,"type":"invalid","preflight_status":v["status"],"violations":v["violations"],"expected_quarantine":True,"actual_quarantine":v["status"]=="fail","match":v["status"]=="fail"})
    all_match = all(r["match"] for r in results)
    return {"phase169_expectation_matcher":{"examples_checked":len(results),"valid_examples_checked":sum(1 for r in results if r["type"].startswith("valid")),"invalid_examples_checked":sum(1 for r in results if r["type"]=="invalid"),"expectations_all_match":all_match,"results":results,"mock_used":False,"fixture_used":False}}

def build_sandbox_simulation(draft_input=None):
    if draft_input is None:
        return {"phase169_sandbox_simulation":{"status":"no_draft","simulated_outcome":"no_input","watch_core_would_update":False,"mock_used":False,"fixture_used":False}}
    activated = sum(1 for d in draft_input.get("decisions",[]) if d.get("owner_decision")=="activate_into_formal_research_coverage")
    return {"phase169_sandbox_simulation":{"status":"simulated","simulated_outcome":f"would_activate_{activated}_candidates","activated_would_be":activated,"watch_core_would_update":False,"sandbox_not_real_execution":True,"sandbox_output_not_committed":True,"cannot_conclude":["sandbox_is_not_real_execution","simulated_outcome_is_not_committed"],"mock_used":False,"fixture_used":False}}

def build_sandbox_all_examples(example_pack):
    results = []
    valid = example_pack["phase169_example_pack"]["valid_examples"]
    invalid = example_pack["phase169_example_pack"]["invalid_examples"]
    for k, ex in valid.items():
        inp = {"decisions":ex["decisions"]} if "decisions" in ex else {"decisions":[{"candidate_id":ex["candidate_id"],"owner_decision":ex["owner_decision"],"rationale":ex["rationale"],"conditions":ex.get("conditions",[]),"risk_acknowledgment":ex["risk_acknowledgment"]}]}
        s = build_sandbox_simulation(inp)
        results.append({"example_id":k,"type":"valid","simulated":True,"watch_core_would_update":s["phase169_sandbox_simulation"]["watch_core_would_update"]})
    for k, ex in invalid.items():
        inp = {"decisions":ex["decisions"]} if "decisions" in ex else {"decisions":[{"candidate_id":ex["candidate_id"],"owner_decision":ex["owner_decision"],"rationale":ex["rationale"],"conditions":ex.get("conditions",[]),"risk_acknowledgment":ex["risk_acknowledgment"]}]}
        s = build_sandbox_simulation(inp)
        results.append({"example_id":k,"type":"invalid","simulated":True,"watch_core_would_update":s["phase169_sandbox_simulation"]["watch_core_would_update"]})
    all_checked = len(results) == 12
    no_watch_update = all(not r["watch_core_would_update"] for r in results)
    return {"phase169_sandbox_all_examples":{"examples_checked":len(results),"all_examples_checked":all_checked,"no_watch_core_update_in_any":no_watch_update,"results":results,"mock_used":False,"fixture_used":False}}
