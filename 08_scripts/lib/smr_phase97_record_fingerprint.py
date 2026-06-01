import json,os,hashlib
def fingerprint_record(record):
    keys=["ticker","hard_data_category","field_name","source_phase","period"]
    fp_str="|".join(str(record.get(k,"")) for k in keys)
    return hashlib.sha256(fp_str.encode()).hexdigest()[:16]
def dedup_records(records):
    seen={};unique=[]
    for r in records:
        fp=fingerprint_record(r)
        if fp not in seen: seen[fp]=r;unique.append(r)
        else:
            existing=seen[fp]
            if r.get("as_of_date","") > existing.get("as_of_date",""): seen[fp]=r;unique=[x for x in unique if fingerprint_record(x)!=fp];unique.append(r)
    return {"phase97_dedup":{"original_count":len(records),"unique_count":len(unique),"duplicates_removed":len(records)-len(unique),"records":unique,"mock_used":False,"fixture_used":False}}
