import json,os
def classify_recovery_results(retry, fallback, degraded, field_map, stale, replacement):
    total=0; recovered=0; partially=0; still_blocked=0; manual=0; fallback_rec=0; degraded_rec=0
    rt=retry.get("phase99_primary_retry",{})
    if rt.get("retry_recovered",0)>0: recovered+=rt["retry_recovered"]
    fb=fallback.get("phase99_fallback_execution",{})
    if fb.get("fallback_recovered",0)>0: fallback_rec+=fb["fallback_recovered"]; recovered+=fb["fallback_recovered"]
    dg=degraded.get("phase99_degraded_parser",{})
    if dg.get("degraded_recovered",0)>0: degraded_rec+=dg["degraded_recovered"]; partially+=dg["degraded_recovered"]
    fm=field_map.get("phase99_alternative_field_mapping",{})
    if fm.get("fields_recovered",0)>0: partially+=fm["fields_recovered"]
    st=stale.get("phase99_stale_refresh",{})
    if st.get("stale_refresh_recovered",0)>0: recovered+=st["stale_refresh_recovered"]
    rp=replacement.get("phase99_blocked_replacement",{})
    if rp.get("replacement_recovered",0)>0: recovered+=rp["replacement_recovered"]
    still=rp.get("still_blocked",0)
    if still>0: still_blocked+=still
    total=recovered+partially+still_blocked
    return {"phase99_recovery_classifier":{"total_recovery_actions":total,"recovered":recovered,"partially_recovered":partially,"fallback_recovered":fallback_rec,"degraded_recovered":degraded_rec,"still_blocked":still_blocked,"manual_required":manual,"mock_used":False,"fixture_used":False}}
