CANDIDATES = ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM","TSM","ASML","AMD","SNOW","MU"]

def build_owner_decision_diff_engine(submitted_input=None):
    diffs = []
    for tk in CANDIDATES:
        drafted = "PENDING_OWNER_INPUT"
        submitted = drafted
        if submitted_input:
            for d in submitted_input.get("decisions", []):
                if d.get("candidate_id") == tk:
                    submitted = d.get("owner_decision", drafted)
        diffs.append({
            "ticker": tk,
            "draft_decision": drafted,
            "submitted_decision": submitted,
            "diff_status": "unchanged" if drafted == submitted else "owner_updated",
            "diff_not_auto_execution": True,
            "cannot_conclude": ["diff_is_not_approval","diff_requires_owner_confirmation"]
        })
    return {"phase168_owner_decision_diff_engine":{"candidates":len(diffs),"diffs":diffs,"diff_not_auto_execution":True,"mock_used":False,"fixture_used":False}}
