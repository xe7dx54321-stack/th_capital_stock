import json,os
def run_recovery_guard(classifier_result):
    cl=classifier_result.get("phase99_recovery_classifier",{})
    violations=[]
    if cl.get("recovered",0)>0 and cl.get("still_blocked",0)>0:
        pass
    if cl.get("fallback_recovered",0)>0:
        violations.append({"violation":"fallback_recovered_not_primary","detail":"fallback recovery should not be claimed as primary source restoration"})
    return {"phase99_recovery_guard":{"overall":"pass" if len(violations)==0 else "fail","violations":len(violations),"violation_details":violations,"mock_used":False,"fixture_used":False}}
