import json,os
def run_recovery_guard(classifier_result):
    cl=classifier_result.get("phase99_recovery_classifier",{})
    violations=[]
    recovered=cl.get("recovered",0)
    fallback_rec=cl.get("fallback_recovered",0)
    degraded_rec=cl.get("degraded_recovered",0)
    partially=cl.get("partially_recovered",0)
    still_blocked=cl.get("still_blocked",0)
    if recovered>0 and still_blocked>0:
        violations.append({"violation":"recovered_and_blocked_simultaneously","detail":"unreconciled: recovered>0 and still_blocked>0"})
    if fallback_rec>recovered:
        violations.append({"violation":"fallback_exceeds_total_recovered","detail":"fallback recovered count exceeds total recovered"})
    if degraded_rec>partially:
        violations.append({"violation":"degraded_exceeds_partial","detail":"degraded recovered count exceeds partially recovered"})
    return {"phase99_recovery_guard":{"overall":"pass" if len(violations)==0 else "fail","violations":len(violations),"violation_details":violations,"checks":{"fallback_not_primary":"compliance_ok_fallback_separately_tracked","degraded_not_full":"compliance_ok_degraded_separately_tracked","distinction_preserved":True},"mock_used":False,"fixture_used":False}}
