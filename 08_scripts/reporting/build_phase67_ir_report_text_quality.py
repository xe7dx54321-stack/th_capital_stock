#!/usr/bin/env python3
"""Phase 67 IR/report text quality report."""
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
J=Path(__file__).resolve().parents[1]/"jobs"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if str(J) not in sys.path: sys.path.insert(0,str(J))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_ir_report_text_quality_classifier import classify_texts

def build(t="300308.SZ"):
    r={"ticker":t,"ir_report_text_quality":{"texts_checked":0,"high_signal_ir_text":0,"usable_ir_text":0,"usable_report_text":0,"administrative_text":0,"rejected":0,"texts_usable_for_deep_extraction":0,"rows":[]}}
    try:
        from run_phase67_expanded_pdf_text_extraction import run_phase67_extraction
        ex=run_phase67_extraction(t,max_pdfs=25,mode="execute")
        rows=ex.get("phase67_expanded_pdf_text_extraction",{}).get("rows",[])
        if rows:
            qt=classify_texts(rows)
            r["ir_report_text_quality"]=qt
        else:
            r["ir_report_text_quality"]["status"]="no_extracted_texts"
    except Exception as e:
        r["ir_report_text_quality"]["status"]="error:"+str(e)[:80]
    return r

def _md(r):
    q=r.get("ir_report_text_quality",r)
    lines=["# IR/Report Text Quality",""]
    lines.append("Checked: "+str(q.get("texts_checked",0)))
    lines.append("High IR: "+str(q.get("high_signal_ir_text",0)))
    lines.append("Usable IR: "+str(q.get("usable_ir_text",0)))
    lines.append("Usable report: "+str(q.get("usable_report_text",0)))
    lines.append("Admin text: "+str(q.get("administrative_text",0)))
    lines.append("Usable for deep: "+str(q.get("texts_usable_for_deep_extraction",0)))
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build(a.ticker)
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
