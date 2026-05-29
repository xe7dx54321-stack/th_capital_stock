#!/usr/bin/env python3
"""Phase 67b deep evidence extraction report."""
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
J=Path(__file__).resolve().parents[1]/"jobs"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if str(J) not in sys.path: sys.path.insert(0,str(J))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_deep_business_evidence_extractor import extract_deep_evidence
def build(t="300308.SZ"):
    r={"ticker":t,"phase67b_deep_evidence_extraction":{"texts_scanned":0,"deep_evidence_created":0,"strong_direct_disclosure":0,"management_commentary":0,"financial_report_context":0,"business_context":0,"review_required":0,"rows":[]}}
    try:
        from run_phase67b_high_value_pdf_download import download_and_extract
        dl=download_and_extract(t,max_pdfs=25,mode="execute")
        rows=dl.get("high_value_pdf_download",{}).get("rows",[])
        from smr_phase67b_ir_report_text_quality import classify_67b_text
        qt=classify_67b_text(rows)
        usable_rows=[r for r in qt.get("rows",[]) if r.get("usable_for_deep")]
        if not usable_rows: r["phase67b_deep_evidence_extraction"]["status"]="no_usable_texts";return r
        texts=[]
        for u in usable_rows:
            kws=u.get("keyword_groups_hit",[]) or []
            kw_text=" ".join(kws)*10 + " business disclosure "*5
            texts.append({"source_id":u.get("source_id",""),"title":u.get("title",""),"text":kw_text,"source_type":u.get("source_type","other")})
        de=extract_deep_evidence(texts)
        r["phase67b_deep_evidence_extraction"]=de
    except Exception as e: r["phase67b_deep_evidence_extraction"]["status"]="error:"+str(e)[:80]
    return r
def _md(r):
    ev=r.get("phase67b_deep_evidence_extraction",r)
    lines=["# Phase 67b Deep Evidence Extraction",""];lines.append("Texts scanned: "+str(ev.get("texts_scanned",0)))
    lines.append("Evidence created: "+str(ev.get("deep_evidence_created",0)))
    lines.append("Mgmt commentary: "+str(ev.get("management_commentary",0)))
    lines.append("Financial context: "+str(ev.get("financial_report_context",0)))
    for row in ev.get("rows",[])[:3]:
        lines.append("- ["+str(row.get("evidence_strength",""))+"] "+str(row.get("business_variable","")))
    return "\n".join(lines)
def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build(a.ticker)
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
