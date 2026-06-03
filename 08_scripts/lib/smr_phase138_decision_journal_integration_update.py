def build_decision_journal_integration_update():
 candidates=[{"ticker":"688041.SH","decision":"accept_derived_valuation_for_thesis_or_seek_direct","status":"pending_owner","not_trade":True},{"ticker":"300394.SZ","decision":"accept_eastmoney_alternative_for_thesis_or_continue_cninfo","status":"pending_owner","not_trade":True}]
 return {"phase138_decision_journal_integration_update":{"candidates":candidates,"total":len(candidates),"all_not_trade":True,"mock_used":False,"fixture_used":False}}
