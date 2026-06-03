def build_decision_diff(normalized, candidates):
    prev = {c["ticker"]:"pending_owner_review" for c in candidates}
    diffs = []
    for d in normalized.get("decisions",[]):
        t = d["ticker"]; new_dec = d["decision"]; old_dec = prev.get(t,"pending_owner_review")
        if new_dec != old_dec: diffs.append({"ticker":t,"previous":old_dec,"new":new_dec,"changed":True})
    return {"phase159_decision_diff":{"total_changes":len(diffs),"diffs":diffs,"diff_is_not_execution":True,"mock_used":False,"fixture_used":False}}
