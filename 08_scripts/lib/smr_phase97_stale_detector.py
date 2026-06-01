import json,os
from datetime import datetime,timedelta
def detect_stale_expired(records):
    now=datetime.now();now_str=now.isoformat()[:10]
    stale=[];expired=[];valid=[]
    for r in records:
        as_of=r.get("as_of_date","")
        if not as_of: stale.append({"record_id":r.get("record_id",""),"reason":"no_as_of_date"});continue
        try:
            dt=datetime.fromisoformat(as_of) if "T" not in as_of else datetime.fromisoformat(as_of.split("T")[0])
            days=(now-dt).days
        except: stale.append({"record_id":r.get("record_id",""),"reason":"invalid_date"});continue
        if days>90: expired.append({"record_id":r.get("record_id",""),"ticker":r["ticker"],"field":r.get("field_name",""),"days_since_update":days,"reason":"expired_90d"})
        elif days>7: stale.append({"record_id":r.get("record_id",""),"ticker":r["ticker"],"field":r.get("field_name",""),"days_since_update":days,"reason":"stale_7d"})
        else: valid.append({"record_id":r.get("record_id",""),"days_since_update":days})
    return {"phase97_stale_detector":{"valid":len(valid),"stale":len(stale),"expired":len(expired),"stale_records":stale,"expired_records":expired,"mock_used":False,"fixture_used":False}}
