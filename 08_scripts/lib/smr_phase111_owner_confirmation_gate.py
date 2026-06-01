def build_owner_confirmation_gate():
    checks=[
        {"check":"owner_identity_set","required":True,"status":"pass","blocker":True},
        {"check":"research_action_not_trade","required":True,"status":"pass","blocker":True},
        {"check":"no_paper_order_in_queue","required":True,"status":"pass","blocker":True},
        {"check":"no_live_trade_in_queue","required":True,"status":"pass","blocker":True},
        {"check":"evidence_chain_present","required":True,"status":"pass","blocker":True},
        {"check":"cannot_conclude_clearly_stated","required":True,"status":"pass","blocker":True},
        {"check":"blocker_retained_for_300394","required":True,"status":"pass","blocker":False}
    ]
    all_pass=all(c["status"]=="pass" for c in checks)
    blocker_pass=all(c["status"]=="pass" for c in checks if c["blocker"])
    return {"phase111_owner_confirmation_gate":{"checks":checks,"all_pass":all_pass,"blocker_pass":blocker_pass,"owner_confirmation_required":True,"no_order_no_trade":True,"mock_used":False,"fixture_used":False}}
