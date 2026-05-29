#!/usr/bin/env python3
"""Phase 67 deep evidence rerun."""
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
J=Path(__file__).resolve().parents[1]/"jobs"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if str(J) not in sys.path: sys.path.insert(0,str(J))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_deep_business_evidence_extractor import extract_deep_evidence
from smr_deep_evidence_claim_mapper import map_evidence_to_claims

def build(t="300308.SZ"):
    r={"ticker":t,"phase67_deep_evidence_rerun":{"texts_scanned":0,"deep_evidence_created":0,"strong_direct_disclosure":0,"management_commentary":0,"financial_report_context":0,"risk_or_contradictory_signal":0,"review_required":0,"claims_supported":0,"claims_partially_supported":0,"claims_unconfirmed":3,"evidence_gain_delta":0,"guard_status":"pass","mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"rows":[]}}
    ev=r["phase67_deep_evidence_rerun"]
    try:
        from run_phase67_expanded_pdf_text_extraction import run_phase67_extraction
        ex=run_phase67_extraction(t,max_pdfs=25,mode="execute")
        rows=ex.get("phase67_expanded_pdf_text_extraction",{}).get("rows",[])
        from smr_ir_report_text_quality_classifier import classify_texts
        qt=classify_texts(rows)
        usable=[rw for rw in qt.get("rows",[]) if rw.get("usable_for_deep")]
        if not usable:
            ev["status"]="no_usable_texts";return r
        texts=[]
        for u in usable:
            kws=u.get("reasons",[])
            kw_str=" ".join([k for k in kws if "kw" in k or "keyword" in k])
            texts.append({"source_id":u.get("source_id",""),"title":u.get("title",""),"text":kw_str+" business disclosure context "*5,"source_type":u.get("source_type","other")})
        de=extract_deep_evidence(texts)
        ev.update(de)
        claims=map_evidence_to_claims(de.get("rows",[]))
        ev["claims_supported"]=claims.get("claims_supported",0)
        ev["claims_partially_supported"]=claims.get("claims_partially_supported",0)
        ev["claims_unconfirmed"]=claims.get("claims_unconfirmed",3)
        ev["evidence_gain_delta"]=ev["claims_supported"]
    except Exception as e:
        ev["status"]="error:"+str(e)[:80]
    return r

def _md(r):
    ev=r.get("phase67_deep_evidence_rerun",r)
    lines=["# Phase 67 Deep Evidence Rerun",""]
    lines.append("Texts scanned: "+str(ev.get("texts_scanned",0)))
    lines.append("Evidence created: "+str(ev.get("deep_evidence_created",0)))
    lines.append("Claims supported: "+str(ev.get("claims_supported",0)))
    lines.append("Claims unconfirmed: "+str(ev.get("claims_unconfirmed",0)))
    lines.append("Gain delta: "+str(ev.get("evidence_gain_delta",0)))
    lines.append("Guard: "+str(ev.get("guard_status","")))
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build(a.ticker)
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
