def build_decision_taxonomy():
 types=["watchlist_escalate","watchlist_demote","deep_dive_trigger","signal_override","source_trust_shift","opportunity_priority","risk_tolerance","research_focus","gap_acceptance","manual_override"]
 return {"phase124_taxonomy":{"version":"v1","total":len(types),"types":types,"invalid_types":["buy_decision","sell_decision","position_size","entry_price","exit_price","portfolio_allocation"],"trade_like_rejected":True,"mock_used":False,"fixture_used":False}}
