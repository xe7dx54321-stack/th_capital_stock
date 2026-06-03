def validate_owner_decisions(parsed):
    valid = ["approve_research_activation","defer_to_next_review","request_more_evidence","request_identity_confirmation","request_source_route_confirmation","reject_for_now"]
    forbidden = ["buy","sell","target_price","position_sizing","trade_action","short","add","reduce"]
    results = []
    for d in parsed.get("decisions",[]):
        dec = d.get("decision","")
        rat = d.get("rationale","")
        is_valid = dec in valid
        has_forbidden = any(fw in rat.lower() for fw in forbidden)
        results.append({"ticker":d["ticker"],"decision":dec,"decision_valid":is_valid,"no_forbidden_terms":not has_forbidden,"trade_language_rejected":has_forbidden})
    return {"phase157_decision_validator":{"validated":len(results),"all_valid":all(r["decision_valid"] for r in results),"no_trade_language":all(r["no_forbidden_terms"] for r in results),"results":results,"mock_used":False,"fixture_used":False}}
