def simulate_execution_plan(approved_sims):
    plans = [{"ticker":a["ticker"],"execution_plan":"pending_owner_final_sign_off","do_not_execute_automatically":True,"required_sign_offs":["owner_final_approval","source_verified","financials_loaded","thesis_drafted"]} for a in approved_sims.get("results",[])]
    return {"phase157_execution_simulator":{"execution_plan_generated":True,"plans":len(plans),"execution_plans":plans,"simulation_only":True,"execution_not_allowed":True,"requires_owner_explicit_sign_off":True,"mock_used":False,"fixture_used":False}}
