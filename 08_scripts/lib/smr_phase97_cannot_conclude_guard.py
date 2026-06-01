import json,os
def run_refresh_guard(delta_result):
    violations=[]
    delta=delta_result.get("phase97_delta",{})
    if delta.get("changed",0)>0:
        for ch in delta.get("changed_records",[]):
            if isinstance(ch,dict) and ch.get("old_value") is not None and ch.get("new_value") is not None:
                pass
    added=delta.get("added_records",[])
    for r in added:
        if isinstance(r,dict) and r.get("data_type")=="peer_context_only":
            violations.append({"record":r.get("record_id",""),"violation":"peer_context_only_marked_as_added","detail":"Peer context records should not be treated as new hard data"})
    return {"phase97_refresh_guard":{"overall":"pass" if len(violations)==0 else "fail","violations":len(violations),"violation_details":violations,"mock_used":False,"fixture_used":False}}
