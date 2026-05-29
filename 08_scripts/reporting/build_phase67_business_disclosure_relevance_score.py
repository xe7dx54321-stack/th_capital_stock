#!/usr/bin/env python3
"""Phase 67 business disclosure relevance score report."""
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_business_disclosure_relevance_scorer import score_disclosures
from smr_cninfo_pagination_query_engine import query_paginated
from smr_cninfo_searchkey_query_engine import query_by_searchkeys

def build(t="300308.SZ"):
    r={"ticker":t,"business_disclosure_relevance_score":{"disclosures_scored":0,"high_relevance":0,"medium_relevance":0,"low_relevance":0,"score_breakdown":{},"top_ranked":[]}}
    try:
        pq=query_paginated(t,max_pages=3,page_size=30)
        rows=pq.get("cninfo_pagination_inventory",{}).get("rows",[])
        if rows:
            sc=score_disclosures(rows)
            r["business_disclosure_relevance_score"]=sc
        else:
            r["business_disclosure_relevance_score"]["status"]="no_metadata"
    except Exception as e:
        r["business_disclosure_relevance_score"]["status"]="error:"+str(e)[:80]
    return r

def _md(r):
    s=r.get("business_disclosure_relevance_score",r)
    lines=["# Business Disclosure Relevance Score",""]
    lines.append("Scored: "+str(s.get("disclosures_scored",0)))
    lines.append("High: "+str(s.get("high_relevance",0)))
    lines.append("Medium: "+str(s.get("medium_relevance",0)))
    lines.append("Low: "+str(s.get("low_relevance",0)))
    for tr in s.get("top_ranked",[])[:5]:
        lines.append("- ["+str(tr.get("relevance",""))+"] "+str(tr.get("title",""))[:50]+" score:"+str(tr.get("relevance_score",0)))
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build(a.ticker)
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
