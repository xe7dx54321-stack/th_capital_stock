#!/usr/bin/env python3
"""Phase 67b high-value PDF pool report."""
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_phase67_high_value_pdf_pool_loader import load_high_value_pool as build
def _md(r):
    p=r.get("phase67b_high_value_pdf_pool",r)
    lines=["# High-value PDF Pool",""];lines.append("Candidates: "+str(p.get("candidate_pdfs",0)))
    lines.append("High value: "+str(p.get("high_value_pdfs",0)))
    lines.append("Admin excluded: "+str(p.get("administrative_legal_excluded",0)))
    if p.get("source_type_breakdown"):
        for k,v in p["source_type_breakdown"].items(): lines.append("- "+k+": "+str(v))
    return "\n".join(lines)
def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build(a.ticker)
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
