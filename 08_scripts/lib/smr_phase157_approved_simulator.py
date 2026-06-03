def simulate_approved_activation(approved):
    sims = [{"ticker":a["ticker"],"simulation":"research_activation_preparation","steps":["confirm_source","load_financials","build_valuation_framework","draft_thesis","create_detail_page"],"simulation_is_not_execution":True,"auto_activate":False,"requires_owner_final_approval":True} for a in approved]
    return {"phase157_approved_simulator":{"simulations":len(sims),"results":sims,"simulation_only":True,"activation_not_executed":True,"approve_not_buy":True,"mock_used":False,"fixture_used":False}}
