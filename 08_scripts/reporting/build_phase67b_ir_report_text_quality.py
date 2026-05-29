#!/usr/bin/env python3
"""Phase 67b IR/report text quality report."""
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
J=Path(__file__).resolve().parents[1]/"jobs"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if str(J) not in sys.path: sys.path.insert(0,str(J))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_phase67b_ir_report_text_quality import classify_67b_text
def build(t="300308.SZ"):
    r={"ticker":t,"phase67b_ir_report_text_quality":{"texts_checked":0,"high_signal_ir_text":0,"usable_ir_text":0,"usable_report_text":0,"texts_usable_for_deep_extraction":0,"rows":[]}}
    try:
        from run_phase67b_high_value_pdf_download import download_and_extract
        dl=download_and_extract(t,max_pdfs=25,mode="execute")
        rows=dl.get("high_value_pdf_download",{}).get("rows",[])
        if rows: r["phase67b_ir_report_text_quality"]=classify_67b_text(rows)
    except Exception as e: r["phase67b_ir_report_text_quality"]["status"]="error:"+str(e)[:80]
    return r
def _md(r):
    q=r.get("phase67b_ir_report_text_quality",r)
    lines=["# Phase 67b IR/Report Text Quality",""];lines.append("Checked: "+str(q.get("texts_checked",0)))
    lines.append("High IR: "+str(q.get("high_signal_ir_text",0)))
    lines.append("Usable IR: "+str(q.get("usable_ir_text",0)))
    lines.append("Usable report: "+str(q.get("usable_report_text",0)))
    lines.append("Usable for deep: "+str(q.get("texts_usable_for_deep_extraction",0)))
    return "\n".join(lines)
def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build(a.ticker)
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
