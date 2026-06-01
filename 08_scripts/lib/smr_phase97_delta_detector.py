import json,os
def detect_deltas(old_records, new_records):
    old_map={}
    for r in old_records:
        k=(r["ticker"],r.get("hard_data_category",""),r.get("field_name",""))
        old_map[k]=r
    new_map={}
    for r in new_records:
        k=(r["ticker"],r.get("hard_data_category",""),r.get("field_name",""))
        new_map[k]=r
    added=[];changed=[];unchanged=[]
    for k,r in new_map.items():
        if k not in old_map: added.append(r)
        else:
            ov=old_map[k].get("field_value");nv=r.get("field_value")
            if ov!=nv: changed.append({"key":k,"old_value":ov,"new_value":nv})
            else: unchanged.append(r)
    removed=[k for k in old_map if k not in new_map]
    return {"phase97_delta":{"added":len(added),"changed":len(changed),"unchanged":len(unchanged),"removed":len(removed),"added_records":added,"changed_records":changed,"mock_used":False,"fixture_used":False}}
