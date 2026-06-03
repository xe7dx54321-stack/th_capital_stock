def simulate_more_evidence(evidence):
    sims = [{"ticker":e["ticker"],"simulation":"evidence_gathering","assigned_agent":"EvidenceAgent","tasks":["gather_public_filings","check_industry_reports","compile_peer_comparison"],"simulation_is_not_execution":True} for e in evidence]
    return {"phase157_evidence_simulator":{"simulations":len(sims),"results":sims,"simulation_only":True,"mock_used":False,"fixture_used":False}}
