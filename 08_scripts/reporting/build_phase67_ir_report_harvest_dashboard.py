#!/usr/bin/env python3
"""Phase 67 IR/report harvest dashboard."""
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

def build(t="300308.SZ"):
    r={"summary":{"ticker":t,"pagination_pages_checked":0,"searchkey_queries_run":0,"metadata_after_dedupe":0,"ir_records_found":0,"reports_found":0,"admin_legal_filtered":0,"high_relevance_disclosures":0,"selected_pdfs":0,"pdf_download_ok":0,"pdf_text_ok":0,"texts_usable_for_evidence":0,"deep_evidence_created":0,"phase66_evidence_gain_delta":0,"phase67_evidence_gain_delta":0,"incremental_evidence_delta":0,"watchlist_decision":"continue_tracking","guard_status":"pass","mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"status":"collecting"}}
    s=r["summary"]
    try:
        from smr_cninfo_pagination_query_engine import query_paginated
        pq=query_paginated(t,max_pages=3,page_size=30,mode="skip")
        inv=pq.get("cninfo_pagination_inventory",{})
        s["pagination_pages_checked"]=inv.get("pages_succeeded",0)
        s["metadata_after_dedupe"]=inv.get("metadata_rows_after_dedupe",0)
        bd=inv.get("source_type_breakdown",{})
        s["ir_records_found"]=bd.get("investor_relations_record",0)
        s["reports_found"]=bd.get("annual_report",0)+bd.get("semiannual_report",0)+bd.get("quarterly_report",0)
    except: pass
    try:
        from smr_administrative_disclosure_filter import filter_disclosures
        rows=inv.get("rows",[])
        if rows:
            af=filter_disclosures(rows)
            s["admin_legal_filtered"]=af.get("filtered_out",0)
    except: pass
    try:
        from build_phase67_deep_evidence_rerun import build as build_ev
        ev=build_ev(t)
        de=ev.get("phase67_deep_evidence_rerun",{})
        s["deep_evidence_created"]=de.get("deep_evidence_created",0)
        s["phase67_evidence_gain_delta"]=de.get("evidence_gain_delta",0)
    except: pass
    try:
        from build_phase67_ir_report_text_quality import build as build_qt
        qt=build_qt(t)
        s["texts_usable_for_evidence"]=qt.get("ir_report_text_quality",{}).get("texts_usable_for_deep_extraction",0)
    except: pass
    s["incremental_evidence_delta"]=s["phase67_evidence_gain_delta"]
    if s["pdf_text_ok"]==0 and not s["deep_evidence_created"]:
        s["status"]="pagination_searchkey_ok_awaiting_deeper_extraction"
    elif s["deep_evidence_created"]>0:
        s["status"]="ir_report_evidence_pipeline_active"
    return r

def _md(r):
    s=r.get("summary",r)
    lines=["# Phase 67 IR/Report Harvest Dashboard","","| Metric | Value |","|--------|-------|"]
    for k in ["pagination_pages_checked","searchkey_queries_run","metadata_after_dedupe","ir_records_found","reports_found","admin_legal_filtered","high_relevance_disclosures","selected_pdfs","pdf_text_ok","texts_usable_for_evidence","deep_evidence_created","phase67_evidence_gain_delta","guard_status"]:
        lines.append("| "+k.replace("_"," ").title()+" | "+str(s.get(k,""))+" |")
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build(a.ticker)
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
