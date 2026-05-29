#!/usr/bin/env python3
"""Phase 67b IR/report PDF evidence dashboard."""
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
def build(t="300308.SZ"):
    r={"summary":{"ticker":t,"selected_high_value_pdfs":0,"pdf_download_ok":0,"pdf_download_failed":0,"pdf_text_ok":0,"pdf_text_failed":0,"texts_usable_for_deep_extraction":0,"deep_evidence_created":0,"claims_supported":0,"claims_unconfirmed":3,"phase66_gain":0,"phase67b_gain":0,"incremental_delta":0,"watchlist_decision":"continue_tracking","guard_status":"pass","mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"status":"collecting"}}
    s=r["summary"]
    try:
        from smr_phase67_high_value_pdf_pool_loader import load_high_value_pool
        pool=load_high_value_pool(t,max_pages=5)
        s["selected_high_value_pdfs"]=pool.get("phase67b_high_value_pdf_pool",{}).get("high_value_pdfs",0)
    except: pass
    try:
        from build_phase67b_ir_report_text_quality import build as build_qt
        qt=build_qt(t);s["texts_usable_for_deep_extraction"]=qt.get("phase67b_ir_report_text_quality",{}).get("texts_usable_for_deep_extraction",0)
    except: pass
    try:
        from build_phase67b_deep_evidence_extraction import build as build_ev
        ev=build_ev(t);s["deep_evidence_created"]=ev.get("phase67b_deep_evidence_extraction",{}).get("deep_evidence_created",0)
    except: pass
    try:
        from build_phase67b_evidence_claim_map import build as build_cm
        cm=build_cm(t);s["phase67b_gain"]=cm.get("phase67b_evidence_claim_map",{}).get("evidence_gain_delta",0)
    except: pass
    s["incremental_delta"]=s["phase67b_gain"]
    if s["deep_evidence_created"]>0: s["status"]="ir_report_evidence_pipeline_active"
    elif s["selected_high_value_pdfs"]>0: s["status"]="pdf_pool_loaded_awaiting_execution"
    return r
def _md(r):
    s=r.get("summary",r)
    lines=["# Phase 67b IR/Report PDF Evidence Dashboard","","| Metric | Value |","|--------|-------|"]
    for k in ["selected_high_value_pdfs","pdf_text_ok","texts_usable_for_deep_extraction","deep_evidence_created","phase67b_gain","guard_status","status"]:
        lines.append("| "+k.replace("_"," ").title()+" | "+str(s.get(k,""))+" |")
    return "\n".join(lines)
def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build(a.ticker)
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
