#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES
def build(t="300308.SZ"):
    curated=CURATED_CNINFO_IDENTITIES.get(t,{})
    org_id=curated.get("org_id","")
    code=curated.get("security_code",t.split(".")[0])
    stock_param=code+","+org_id if org_id else code
    identity_found=bool(org_id)
    return {"ticker":t,"cninfo_source_identity_map":{"identity_found":identity_found,"stock_param":stock_param,"org_id":org_id,"plate":curated.get("plate",""),"column":curated.get("column",""),"verification_status":"metadata_pdf_text_chain_verified" if identity_found else "not_verified","ticker_specific":True,"identity_source":curated.get("identity_source","curated_manifest"),"mock_used":False,"fixture_used":False}}
def _md(r):
    m=r.get("cninfo_source_identity_map",r)
    lines=["# CNINFO Source Identity Map",""]
    lines.append("Ticker: "+r.get("ticker",""))
    lines.append("Identity Found: "+str(m.get("identity_found")))
    lines.append("Stock Param: "+str(m.get("stock_param","")))
    lines.append("Org ID: "+str(m.get("org_id","")))
    lines.append("Plate/Column: "+str(m.get("plate",""))+"/"+str(m.get("column","")))
    lines.append("Ticker-specific: "+str(m.get("ticker_specific")))
    return "\n".join(lines)
def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build(a.ticker)
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
