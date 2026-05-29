#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_business_keyword_hit_scanner import scan_metadata_rows
from smr_cninfo_targeted_metadata_harvester import harvest_targeted_metadata
def build(t="300308.SZ",mx=50,skip=False):
    meta=harvest_targeted_metadata(t,mx,skip_network=skip)
    rows=meta.get("cninfo_targeted_metadata_inventory",{}).get("rows",[])
    scan=scan_metadata_rows(rows)
    return {"ticker":t,"business_keyword_hit_scan":scan}
def _md(r):
    s=r.get("business_keyword_hit_scan",r)
    lines=["# Business Keyword Hit Scan",""]
    lines.append("Scanned: "+str(s.get("sources_scanned",0)))
    lines.append("Hits: "+str(s.get("sources_with_keyword_hit",0)))
    if s.get("keyword_group_breakdown"):
        for k,v in s["keyword_group_breakdown"].items(): lines.append("- "+k+": "+str(v))
    for row in s.get("rows",[])[:5]:
        lines.append("- "+str(row.get("title",""))[:50]+" ["+",".join(row.get("keyword_groups_hit",[]))+"]")
    return "\n".join(lines)
def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true");p.add_argument("--skip-network",action="store_true")
    a=p.parse_args();r=build(a.ticker,skip=getattr(a,"skip_network",False))
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
