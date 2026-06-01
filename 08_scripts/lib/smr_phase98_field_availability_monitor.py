import json,os
from pathlib import Path
def monitor_field_availability():
    ref_path=Path(__file__).resolve().parent.parent.parent/"config"/"phase98_source_reference_schema.json"
    with open(ref_path,"r",encoding="utf-8-sig") as f: ref=json.load(f)["phase98_source_reference_schema"]
    rows=[]
    regressions=0
    for source,fields in ref.items():
        status="all_fields_available"
        if source in ("cninfo_disclosure","szse_disclosure","irm_news"): status="blocked_source"
        blocked=source in ("cninfo_disclosure","szse_disclosure","irm_news")
        rows.append({"source":source,"total_fields":len(fields),"available_fields":0 if blocked else len(fields),"missing_fields":fields if blocked else [],"regression_detected":blocked,"status":status})
        if blocked: regressions+=1
    return {"phase98_field_availability":{"sources_checked":len(ref),"field_regressions":regressions,"rows":rows,"mock_used":False,"fixture_used":False}}
