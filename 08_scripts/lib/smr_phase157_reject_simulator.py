def simulate_reject_for_now(rejected):
    sims = [{"ticker":r["ticker"],"simulation":"rejected_for_now","archive_from_active_queue":True,"can_revisit_in":"30_days","reject_is_not_sell":True} for r in rejected]
    return {"phase157_reject_simulator":{"simulations":len(sims),"results":sims,"simulation_only":True,"reject_not_sell":True,"mock_used":False,"fixture_used":False}}
