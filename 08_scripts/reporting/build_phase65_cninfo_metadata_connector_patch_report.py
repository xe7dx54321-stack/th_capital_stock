#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES
from smr_cninfo_stock_identity_resolver import resolve_cninfo_identity

def build(t="300308.SZ", skip=False):
    curated = CURATED_CNINFO_IDENTITIES.get(t, {})
    resolver = resolve_cninfo_identity(t, skip)
    r = resolver.get("cninfo_stock_identity_resolver", {})
    working = r.get("best_parameter_set") is not None
    return {"ticker":t,"cninfo_metadata_connector_patch":{
        "patch_applied":working,
        "curated_org_id":curated.get("org_id",""),
        "working_parameter_set_used":r.get("best_parameter_set"),
        "metadata_sources_found":r.get("best_result_count",0),
        "raw_content_saved":False,"ocr_used":False,
        "mock_used":False,"fixture_used":False,
        "reason":None if working else "no_working_parameter_set_found",
        "fallback_recommended":None if working else "szse_or_irm"
    }}
def _md(r):
    p=r.get("cninfo_metadata_connector_patch",r)
    lines=["# CNINFO Metadata Connector Patch",""]
    lines.append("Patch Applied: "+str(p.get("patch_applied")))
    lines.append("Curated Org ID: "+str(p.get("curated_org_id","")))
    lines.append("Metadata Found: "+str(p.get("metadata_sources_found",0)))
    if p.get("reason"): lines.append("Reason: "+p["reason"])
    lines.append("Raw/OCR: "+str(p.get("raw_content_saved"))+"/"+str(p.get("ocr_used")))
    return "\n".join(lines)
def main():
    p=argparse.ArgumentParser(); p.add_argument("--ticker",default="300308.SZ"); p.add_argument("--json",action="store_true"); p.add_argument("--markdown",action="store_true"); p.add_argument("--skip-network",action="store_true")
    a=p.parse_args(); r=build(a.ticker,getattr(a,"skip_network",False))
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
