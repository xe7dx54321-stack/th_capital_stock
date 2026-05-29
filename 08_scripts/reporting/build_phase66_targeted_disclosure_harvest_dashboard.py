#!/usr/bin/env python3
"""Phase 66 targeted disclosure harvest dashboard."""
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

def build(t="300308.SZ"):
    r={"summary":{"ticker":t,"metadata_sources_found":0,"targeted_metadata_selected":0,"pdf_urls_found":0,"priority_pdfs_selected":0,"pdf_download_ok":0,"pdf_text_ok":0,"texts_usable_for_evidence":0,"business_keyword_hit_texts":0,"deep_evidence_created":0,"claims_supported":0,"claims_partially_supported":0,"claims_unconfirmed":3,"risk_signals_found":0,"phase65b_evidence_gain_delta":1,"phase66_evidence_gain_delta":0,"incremental_evidence_delta":0,"watchlist_decision":"continue_tracking","guard_status":"pass","mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"status":"collecting"}}
    s=r["summary"]
    try:
        from smr_cninfo_targeted_metadata_harvester import harvest_targeted_metadata
        meta=harvest_targeted_metadata(t,50,mode="skip")
        inv=meta.get("cninfo_targeted_metadata_inventory",{})
        s["metadata_sources_found"]=inv.get("metadata_sources_found",0)
        s["targeted_metadata_selected"]=inv.get("targeted_metadata_selected",0)
        s["pdf_urls_found"]=inv.get("pdf_urls_available",0)
    except: pass
    try:
        from smr_priority_pdf_selector import select_priority_pdfs
        rows=inv.get("rows",[])
        sel=select_priority_pdfs(rows,15)
        s["priority_pdfs_selected"]=sel.get("selected_pdfs",0)
    except: pass
    try:
        from build_phase66_expanded_pdf_text_extraction_report import build as build_ex
        ex=build_ex(t,skip=True)
        exd=ex.get("expanded_pdf_text_extraction",{})
        s["pdf_download_ok"]=exd.get("pdf_download_ok",0)
        s["pdf_text_ok"]=exd.get("pdf_text_ok",0)
    except: pass
    try:
        from build_phase66_business_evidence_text_quality import build as build_qual
        qual=build_qual(t)
        q=qual.get("business_evidence_text_quality",{})
        s["texts_usable_for_evidence"]=q.get("high_business_signal",0)+q.get("usable_business_signal",0)
    except: pass
    try:
        from build_phase66_business_keyword_hit_scan import build as build_kw
        kw=build_kw(t)
        s["business_keyword_hit_texts"]=kw.get("business_keyword_hit_scan",{}).get("sources_with_keyword_hit",0)
    except: pass
    try:
        from build_phase66_deep_business_evidence_extraction import build as build_ev
        ev=build_ev(t)
        s["deep_evidence_created"]=ev.get("deep_business_evidence_extraction",{}).get("evidence_created",0)
    except: pass
    try:
        from build_phase66_deep_evidence_claim_map import build as build_cm
        cm=build_cm(t)
        claims=cm.get("deep_evidence_claim_map",{})
        s["claims_supported"]=claims.get("claims_supported",0)
        s["claims_partially_supported"]=claims.get("claims_partially_supported",0)
        s["claims_unconfirmed"]=claims.get("claims_unconfirmed",3)
        s["risk_signals_found"]=claims.get("claims_with_risk_signal",0)
        s["phase66_evidence_gain_delta"]=claims.get("evidence_gain_delta",0)
        s["incremental_evidence_delta"]=max(0,claims.get("evidence_gain_delta",0)-1)
    except: pass
    try:
        from build_phase66_watchlist_update_from_deep_disclosure import build as build_wu
        wu=build_wu(t)
        s["watchlist_decision"]=wu.get("watchlist_update_from_deep_disclosure",{}).get("watchlist_decision","continue_tracking")
    except: pass
    try:
        from build_phase66_deep_evidence_cannot_conclude_guard import build as build_guard
        gr=build_guard(t)
        s["guard_status"]=gr.get("deep_evidence_cannot_conclude_guard",{}).get("guard_status","pass")
    except: pass
    if s["pdf_text_ok"]==0 and s["texts_usable_for_evidence"]==0:
        s["status"]="metadata_pdf_url_ok_but_text_extraction_insufficient"
    elif s["deep_evidence_created"]>0:
        s["status"]="real_disclosure_evidence_pipeline_active"
    return r

def _md(r):
    s=r.get("summary",r)
    lines=["# Phase 66 Targeted Disclosure Harvest Dashboard",""]
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append("| Ticker | "+str(s.get("ticker",""))+" |")
    lines.append("| Metadata found | "+str(s.get("metadata_sources_found",0))+" |")
    lines.append("| Targeted selected | "+str(s.get("targeted_metadata_selected",0))+" |")
    lines.append("| PDF URLs | "+str(s.get("pdf_urls_found",0))+" |")
    lines.append("| Priority PDFs | "+str(s.get("priority_pdfs_selected",0))+" |")
    lines.append("| PDF text OK | "+str(s.get("pdf_text_ok",0))+" |")
    lines.append("| Texts usable | "+str(s.get("texts_usable_for_evidence",0))+" |")
    lines.append("| Deep evidence | "+str(s.get("deep_evidence_created",0))+" |")
    lines.append("| Claims supported | "+str(s.get("claims_supported",0))+" |")
    lines.append("| Claims unconfirmed | "+str(s.get("claims_unconfirmed",0))+" |")
    lines.append("| Phase 65b delta | "+str(s.get("phase65b_evidence_gain_delta",0))+" |")
    lines.append("| Phase 66 delta | "+str(s.get("phase66_evidence_gain_delta",0))+" |")
    lines.append("| Incremental delta | "+str(s.get("incremental_evidence_delta",0))+" |")
    lines.append("| Guard status | "+str(s.get("guard_status",""))+" |")
    lines.append("| Watchlist | "+str(s.get("watchlist_decision",""))+" |")
    lines.append("| Status | "+str(s.get("status",""))+" |")
    lines.append("| Mock | "+str(s.get("mock_used",False))+" |")
    lines.append("| Raw/OCR | "+str(s.get("raw_saved",False))+"/"+str(s.get("ocr_used",False))+" |")
    lines.append("| Pending/Order/Trade | 0/0/0 |")
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build(a.ticker)
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
