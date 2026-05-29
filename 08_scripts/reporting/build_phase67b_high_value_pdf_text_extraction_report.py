#!/usr/bin/env python3
"""Phase 67b text extraction report."""
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
        dl=download_and_extract(t,mx,skip_network=skip,mode="execute" if not skip else "skip")
        rows=dl.get("high_value_pdf_download",{}).get("rows",[])
        ok=[r for r in rows if r.get("text_extraction_status")=="pdf_text_ok"]
        bd={}
        for r in ok:
            st=r.get("source_type","other");bd[st]=bd.get(st,0)+1
        return {"ticker":t,"high_value_pdf_text_extraction":{"pdfs_checked":len(rows),"pdf_text_ok":len(ok),"pdf_text_failed":len(rows)-len(ok),"texts_written":len(ok),"source_type_text_ok":bd,"raw_pdf_saved":False,"ocr_used":False,"rows":ok}}
    except Exception as e:
        return {"ticker":t,"high_value_pdf_text_extraction":{"status":"error:"+str(e)[:80],"pdf_text_ok":0,"rows":[]}}
def _md(r):
    ex=r.get("high_value_pdf_text_extraction",r)
    lines=["# High-value PDF Text Extraction",""];lines.append("Checked: "+str(ex.get("pdfs_checked",0)))
    lines.append("Text OK: "+str(ex.get("pdf_text_ok",0)))
    lines.append("Failed: "+str(ex.get("pdf_text_failed",0)))
    if ex.get("source_type_text_ok"):
        for k,v in ex["source_type_text_ok"].items(): lines.append("- "+k+": "+str(v))
    return "\n".join(lines)
def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--max-pdfs",type=int,default=25);p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true");p.add_argument("--skip-network",action="store_true")
    a=p.parse_args();r=build(a.ticker,a.max_pdfs,skip=getattr(a,"skip_network",False))
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
