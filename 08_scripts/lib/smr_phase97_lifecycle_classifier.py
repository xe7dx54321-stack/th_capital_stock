import json,os
from datetime import datetime,timedelta
def classify_lifecycle(records):
    now=datetime.now();now_str=now.isoformat()[:10]
    fresh=[];stale=[];expired=[]
    for r in records:
        as_of=r.get("as_of_date","")
        if not as_of: stale.append(r);continue
        try:
            dt=datetime.fromisoformat(as_of) if "T" not in as_of else datetime.fromisoformat(as_of.split("T")[0])
            days=(now-dt).days
        except: stale.append(r);continue
        if days<=7: fresh.append(r)
        elif days<=90: stale.append(r)
        else: expired.append(r)
    return {"phase97_lifecycle":{"fresh":len(fresh),"stale":len(stale),"expired":len(expired),"fresh_records":fresh,"stale_records":stale,"expired_records":expired,"mock_used":False,"fixture_used":False}}
