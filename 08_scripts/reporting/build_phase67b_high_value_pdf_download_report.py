#!/usr/bin/env python3
"""Phase 67b PDF download report."""
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
J=Path(__file__).resolve().parents[1]/"jobs"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if str(J) not in sys.path: sys.path.insert(0,str(J))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
def build(t="300308.SZ",mx=25,skip=False):
    try:
        from run_phase67b_high_value_pdf_download import download_and_extract
        return download_and_extract(t,mx,skip_network=skip,mode="execute" if not skip else "skip")
    except ImportError:
        return {"ticker":t,"high_value_pdf_download":{"status":"module_not_found","pdf_download_ok":0,"rows":[]}}
def _md(r):
    d=r.get("high_value_pdf_download",r)
    lines=["# High-value PDF Download",""];lines.append("Selected: "+str(d.get("pdfs_selected",0)))
    lines.append("Download OK: "+str(d.get("pdf_download_ok",0)))
    lines.append("Failed: "+str(d.get("pdf_download_failed",0)))
    for rw in d.get("rows",[])[:5]:
        lines.append("- "+str(rw.get("title",""))[:50]+" ["+str(rw.get("text_extraction_status",""))+"]")
    return "\n".join(lines)
def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--max-pdfs",type=int,default=25);p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true");p.add_argument("--skip-network",action="store_true")
    a=p.parse_args();r=build(a.ticker,a.max_pdfs,skip=getattr(a,"skip_network",False))
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
