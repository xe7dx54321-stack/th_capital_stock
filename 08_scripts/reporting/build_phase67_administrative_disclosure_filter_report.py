#!/usr/bin/env python3
"""Phase 67 admin/legal filter report."""
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_administrative_disclosure_filter import filter_disclosures
from smr_cninfo_pagination_query_engine import query_paginated

def build(t="300308.SZ"):
    r={"ticker":t,"administrative_disclosure_filter":{"metadata_checked":0,"administrative_or_legal_detected":0,"filtered_out":0,"downgraded_to_review_required":0,"business_disclosures_retained":0,"rows":[]}}
    try:
        pq=query_paginated(t,max_pages=3,page_size=30)
        rows=pq.get("cninfo_pagination_inventory",{}).get("rows",[])
        if rows:
            fr=filter_disclosures(rows)
            r["administrative_disclosure_filter"]=fr
        else:
            r["administrative_disclosure_filter"]["status"]="no_metadata_available"
    except Exception as e:
        r["administrative_disclosure_filter"]["status"]="error:"+str(e)[:80]
    return r

def _md(r):
    f=r.get("administrative_disclosure_filter",r)
    lines=["# Administrative/Legal Disclosure Filter",""]
    lines.append("Checked: "+str(f.get("metadata_checked",0)))
    lines.append("Admin/legal detected: "+str(f.get("administrative_or_legal_detected",0)))
    lines.append("Filtered out: "+str(f.get("filtered_out",0)))
    lines.append("Downgraded: "+str(f.get("downgraded_to_review_required",0)))
    lines.append("Retained: "+str(f.get("business_disclosures_retained",0)))
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build(a.ticker)
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
