#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_priority_pdf_selector import select_priority_pdfs
from smr_cninfo_targeted_metadata_harvester import harvest_targeted_metadata
def build(t="300308.SZ",mx_pdf=15,skip=False):
    meta=harvest_targeted_metadata(t,50,skip_network=skip)
    rows=meta.get("cninfo_targeted_metadata_inventory",{}).get("rows",[])
    sel=select_priority_pdfs(rows,mx_pdf)
    return {"ticker":t,"priority_pdf_selection":sel}
def _md(r):
    s=r.get("priority_pdf_selection",r)
    lines=["# Priority PDF Selection",""]
    lines.append("Candidates: "+str(s.get("candidate_pdfs",0)))
    lines.append("Selected: "+str(s.get("selected_pdfs",0)))
    for row in s.get("rows",[])[:5]:
        lines.append("- "+str(row.get("title",""))[:50]+" score:"+str(row.get("priority_score")))
    return "\n".join(lines)
def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--max-pdfs",type=int,default=15);p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true");p.add_argument("--skip-network",action="store_true")
    a=p.parse_args();r=build(a.ticker,a.max_pdfs,skip=getattr(a,"skip_network",False))
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
