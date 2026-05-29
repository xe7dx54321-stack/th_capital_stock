#!/usr/bin/env python3
"""Phase 67 IR/report priority PDF selection."""
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_ir_report_priority_pdf_selector import select_ir_report_pdfs
from smr_cninfo_pagination_query_engine import query_paginated

def build(t="300308.SZ",mx=25):
    r={"ticker":t,"ir_report_priority_pdf_selection":{"candidate_pdfs":0,"selected_pdfs":0,"selected_breakdown":{},"administrative_legal_filtered":0,"rows":[]}}
    try:
        pq=query_paginated(t,max_pages=3,page_size=30)
        rows=pq.get("cninfo_pagination_inventory",{}).get("rows",[])
        if rows:
            sel=select_ir_report_pdfs(rows,mx)
            r["ir_report_priority_pdf_selection"]=sel
        else:
            r["ir_report_priority_pdf_selection"]["status"]="no_metadata"
    except Exception as e:
        r["ir_report_priority_pdf_selection"]["status"]="error:"+str(e)[:80]
    return r

def _md(r):
    s=r.get("ir_report_priority_pdf_selection",r)
    lines=["# IR/Report Priority PDF Selection",""]
    lines.append("Candidates: "+str(s.get("candidate_pdfs",0)))
    lines.append("Selected: "+str(s.get("selected_pdfs",0)))
    lines.append("Admin/legal filtered: "+str(s.get("administrative_legal_filtered",0)))
    if s.get("selected_breakdown"):
        for k,v in s["selected_breakdown"].items(): lines.append("- "+k+": "+str(v))
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--max-pdfs",type=int,default=25);p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build(a.ticker,a.max_pdfs)
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
