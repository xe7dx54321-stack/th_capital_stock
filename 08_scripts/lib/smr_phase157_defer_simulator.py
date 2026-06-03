def simulate_defer(deferred):
    sims = [{"ticker":d["ticker"],"simulation":"deferred_to_next_review","next_review_in":"7_days","keep_in_queue":True} for d in deferred]
    return {"phase157_defer_simulator":{"simulations":len(sims),"results":sims,"simulation_only":True,"mock_used":False,"fixture_used":False}}
