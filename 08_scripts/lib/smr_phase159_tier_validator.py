def validate_requested_tier(parsed):
    valid_tiers = ["candidate","watch","core",""]
    results = []
    for d in parsed.get("decisions",[]):
        tier = d.get("requested_tier","candidate")
        results.append({"ticker":d.get("ticker",""),"requested_tier":tier,"tier_valid":tier in valid_tiers,"note":"tier proposal only, not executed"})
    return {"phase159_tier_validator":{"validated":len(results),"all_valid":all(r["tier_valid"] for r in results),"tier_proposal_only":True,"tier_not_executed":True,"results":results,"mock_used":False,"fixture_used":False}}
