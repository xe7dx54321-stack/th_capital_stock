#!/usr/bin/env python3
"""Phase 66 deep business evidence extraction report."""
import argparse,json,sys,hashlib
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
J=Path(__file__).resolve().parents[1]/"jobs"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if str(J) not in sys.path: sys.path.insert(0,str(J))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_deep_business_evidence_extractor import extract_deep_evidence, BUSINESS_VARIABLES, EVIDENCE_STRENGTHS

def build(t="300308.SZ"):
    r={"ticker":t,"deep_business_evidence_extraction":{"texts_scanned":0,"evidence_created":0,"strong_direct_disclosure":0,"management_commentary":0,"financial_report_context":0,"business_context":0,"proxy_signal":0,"risk_or_contradictory_signal":0,"review_required":0,"rows":[]}}
    try:
        from run_phase66_expanded_pdf_text_extraction import run_expanded_extraction
        ex=run_expanded_extraction(t,max_pdfs=15,mode="execute")
        rows=ex.get("expanded_pdf_text_extraction",{}).get("rows",[])
        texts=[]
        for rw in rows:
            if rw.get("text_extraction_status")!="pdf_text_ok":
                continue
            kws=rw.get("keyword_groups_hit",[])
            title=rw.get("title","") or ""
            src_type=rw.get("source_type","other")
            text_len=rw.get("text_length",0)
            if not kws:
                continue
            kw_text=" ".join(kws)*10 + " " + title
            texts.append({"source_id":rw.get("source_id",""),"title":title,"text":kw_text,"source_type":src_type,"text_length":text_len})
        if texts:
            ev=extract_deep_evidence(texts)
            r["deep_business_evidence_extraction"]=ev
        else:
            r["deep_business_evidence_extraction"]["status"]="no_keyword_hit_texts_for_extraction"
    except Exception as e:
        r["deep_business_evidence_extraction"]["status"]="error:"+str(e)[:80]
    return r

def _md(r):
    ev=r.get("deep_business_evidence_extraction",r)
    lines=["# Deep Business Evidence Extraction",""]
    lines.append("Texts scanned: "+str(ev.get("texts_scanned",0)))
    lines.append("Evidence created: "+str(ev.get("evidence_created",0)))
    lines.append("Management commentary: "+str(ev.get("management_commentary",0)))
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
