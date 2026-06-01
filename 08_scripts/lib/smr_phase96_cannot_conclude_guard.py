import json,os
def run_peer_benchmark_cannot_conclude_guard(records):
    """Guard against over-claiming: peer data != own data, text evidence != confirmed, proxy != reported."""
    violations=[]
    for r in records:
        dt=r.get("data_type","")
        if dt=="peer_context_only":
            if r.get("confidence")=="high": violations.append({"record_id":r.get("record_id",""),"violation":"peer_context_only_with_high_confidence","detail":"Peer context data should not have high confidence"})
        if dt=="proxy_estimate":
            if r.get("field_name","").startswith("reported_"): violations.append({"record_id":r.get("record_id",""),"violation":"proxy_labeled_as_reported","detail":"Proxy estimate labeled as reported field"})
        if dt=="text_evidence":
            if r.get("confidence")=="high": violations.append({"record_id":r.get("record_id",""),"violation":"text_evidence_with_high_confidence","detail":"Text evidence should be medium or low confidence"})
    return {"phase96_peer_benchmark_cannot_conclude_guard":{"overall":"pass" if len(violations)==0 else "fail","violations":len(violations),"violation_details":violations,"mock_used":False,"fixture_used":False}}
