#!/usr/bin/env python3
"""Phase 67 CNINFO IR/report harvest runner."""
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
R=Path(__file__).resolve().parents[1]/"reporting"
J=Path(__file__).resolve().parents[1]/"jobs"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if str(R) not in sys.path: sys.path.insert(0,str(R))
if str(J) not in sys.path: sys.path.insert(0,str(J))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

def run(ticker="300308.SZ",max_pages=5,max_results=120,max_pdfs=25,skip_network=False,mode="execute"):
    r={"ticker":ticker,"phase67_cninfo_ir_report_harvest":{"mode":mode,"steps":[],"pagination_pages_checked":0,"searchkey_queries_run":0,"metadata_after_dedupe":0,"admin_legal_filtered":0,"selected_pdfs":0,"pdf_text_ok":0,"texts_usable_for_evidence":0,"deep_evidence_created":0,"evidence_gain_delta":0,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
    p=r["phase67_cninfo_ir_report_harvest"];steps=[]

    def add(n,s,d=""): steps.append({"name":n,"status":s,"detail":d})

    # 1. Pagination
    try:
        from smr_cninfo_pagination_query_engine import query_paginated
        pq=query_paginated(ticker,max_pages,30,skip_network=skip_network,mode="skip" if skip_network or mode=="dry_run" else "execute")
        inv=pq.get("cninfo_pagination_inventory",{})
        p["pagination_pages_checked"]=inv.get("pages_succeeded",0)
        p["metadata_after_dedupe"]=inv.get("metadata_rows_after_dedupe",0)
        add("pagination_query","ok",str(p["pagination_pages_checked"])+" pages, "+str(p["metadata_after_dedupe"])+" rows")
    except Exception as e: add("pagination_query","error",str(e)[:50])

    # 2. Searchkey
    try:
        from smr_cninfo_searchkey_query_engine import query_by_searchkeys
        sq=query_by_searchkeys(ticker,max_results,skip_network=skip_network,mode="skip" if skip_network or mode=="dry_run" else "execute")
        inv2=sq.get("cninfo_searchkey_inventory",{})
        p["searchkey_queries_run"]=inv2.get("searchkey_queries_run",0)
        add("searchkey_query","ok",str(p["searchkey_queries_run"])+" queries")
    except Exception as e: add("searchkey_query","error",str(e)[:50])

    # 3. Category+searchkey matrix
    try:
        from smr_cninfo_category_searchkey_matrix import run_matrix
        mx=run_matrix(ticker,skip_network=skip_network,mode="skip" if skip_network or mode=="dry_run" else "execute")
        add("category_searchkey_matrix","ok")
    except Exception as e: add("category_searchkey_matrix","error",str(e)[:50])

    # 4. Admin filter
    try:
        rows=pq.get("cninfo_pagination_inventory",{}).get("rows",[])
        if rows:
            from smr_administrative_disclosure_filter import filter_disclosures
            af=filter_disclosures(rows)
            p["admin_legal_filtered"]=af.get("filtered_out",0)
            add("administrative_filter","ok",str(p["admin_legal_filtered"])+" filtered")
        else: add("administrative_filter","skipped","no rows")
    except Exception as e: add("administrative_filter","error",str(e)[:50])

    # 5. Relevance scoring
    try:
        if rows:
            from smr_business_disclosure_relevance_scorer import score_disclosures
            sc=score_disclosures(rows)
            add("relevance_scoring","ok",str(sc.get("high_relevance",0))+" high relevance")
        else: add("relevance_scoring","skipped")
    except Exception as e: add("relevance_scoring","error",str(e)[:50])

    # 6. Priority PDF selection
    try:
        if rows:
            from smr_ir_report_priority_pdf_selector import select_ir_report_pdfs
            sel=select_ir_report_pdfs(rows,max_pdfs)
            p["selected_pdfs"]=sel.get("selected_pdfs",0)
            add("priority_pdf_selection","ok",str(p["selected_pdfs"])+" selected")
        else: add("priority_pdf_selection","skipped")
    except Exception as e: add("priority_pdf_selection","error",str(e)[:50])

    # 7. Expanded PDF extraction
    if skip_network or mode=="dry_run":
        add("expanded_pdf_extraction","skipped" if skip_network else "dry_run")
    else:
        try:
            from run_phase67_expanded_pdf_text_extraction import run_phase67_extraction
            ex=run_phase67_extraction(ticker,max_pdfs,mode="execute")
            exd=ex.get("phase67_expanded_pdf_text_extraction",{})
            p["pdf_text_ok"]=exd.get("pdf_text_ok",0)
            add("expanded_pdf_extraction","ok_or_degraded",str(p["pdf_text_ok"])+" texts")
        except Exception as e: add("expanded_pdf_extraction","error",str(e)[:50])

    # 8-13: Text quality, evidence rerun, analytics, watchlist, brief, dashboard
    for mod_name,step_name in [("build_phase67_ir_report_text_quality","text_quality"),("build_phase67_deep_evidence_rerun","deep_evidence_rerun"),("build_phase67_evidence_gain_analytics","evidence_gain_analytics"),("build_phase67_watchlist_update","watchlist_update"),("build_phase67_ir_report_evidence_brief","brief"),("build_phase67_ir_report_harvest_dashboard","dashboard")]:
        try:
            exec(f"from {mod_name} import build; r2=build(ticker)")
            add(step_name,"ok")
        except Exception as e: add(step_name,"error",str(e)[:50])

    p["steps"]=steps
    return r

def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--dry-run",action="store_true");p.add_argument("--execute",action="store_true");p.add_argument("--skip-network",action="store_true");p.add_argument("--max-pages",type=int,default=5);p.add_argument("--max-results",type=int,default=120);p.add_argument("--max-pdfs",type=int,default=25);p.add_argument("--json",action="store_true")
    a=p.parse_args();mode="execute" if getattr(a,"execute",False) else "dry_run";skip=getattr(a,"skip_network",False)
    r=run(a.ticker,a.max_pages,a.max_results,a.max_pdfs,skip_network=skip,mode=mode)
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
