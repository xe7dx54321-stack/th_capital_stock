def build_activation_review_input(candidates):
    packets = []
    for c in candidates:
        packets.append({"ticker":c["ticker"],"name":c.get("name",""),"market":c.get("market",""),"admission_score":c.get("composite_score",""),"onboarding_review_status":"ready_for_owner_approval","loop_status":"completed","owner_decision":"pending_owner_review","default_no_auto_approval":True})
    return {"phase156_activation_review_input":{"candidates_for_review":len(packets),"review_packets":packets,"auto_approval_allowed":False,"all_default_to_pending":True,"mock_used":False,"fixture_used":False}}
