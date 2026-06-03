import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase130_szse_disclosure_fallback import build_szse_disclosure_fallback
from smr_phase130_company_ir_loader import build_company_ir_loader

def run_known_url_validation(skip_network=False):
    szse=build_szse_disclosure_fallback()["phase130_szse_disclosure_fallback"]["sources"]
    ir=build_company_ir_loader()["phase130_company_ir_loader"]["sources"]
    all_urls=szse+ir
    results=[]
    for s in all_urls:
        r={"source_id":s["source_id"],"url":s["url"],"type":s["type"],"status":s["status"]}
        if skip_network:
            r["validation_status"]="skipped"
            r["reachable"]=None
        elif s["status"]=="available":
            r["validation_status"]="not_probed_to_avoid_browser"
            r["reachable"]=None
            r["note"]="URL known but HTTP probe from mainland may fail; browser-based verification recommended"
        else:
            r["validation_status"]="unvalidated"
            r["reachable"]=None
        results.append(r)
    return {"phase130_known_url_validator":{"total":len(results),"validated":0,"not_probed":len(results),"results":results,"conclusion":"urls_identified_but_browserless_probe_limited","mock_used":False,"fixture_used":False,"browser_used":False}}
