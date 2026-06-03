def build_research_activation_plan(decisions):
    plans = []
    for d in decisions:
        if d.get("owner_decision") == "approve_research_activation":
            plans.append({"ticker":d["ticker"],"activation_plan":"prepare_research_onboarding","steps":["confirm_source","load_financials","build_valuation_framework","draft_thesis"],"activation_is_not_trade_activation":True,"auto_execute":False,"requires_owner_sign_off":True})
    return {"phase156_activation_plan":{"plans_generated":len(plans),"activation_plans":plans,"activation_queue_is_not_watchlist":True,"mock_used":False,"fixture_used":False}}
