#!/usr/bin/env python3
"""Phase 66 targeted disclosure harvest runner."""
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
R=Path(__file__).resolve().parents[1]/"reporting"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if str(R) not in sys.path: sys.path.insert(0,str(R))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

def run_pipeline(ticker="300308.SZ",max_metadata=50,max_pdfs=15,skip_network=False,mode="execute"):
    r={"ticker":ticker,"phase66_targeted_disclosure_harvest":{"mode":mode,"steps":[],"targeted_metadata_selected":0,"pdf_text_ok":0,"texts_usable_for_evidence":0,"deep_evidence_created":0,"evidence_gain_delta":0,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
    p=r["phase66_targeted_disclosure_harvest"]
    steps=[]

    def add_step(name,status,detail=""):
        steps.append({"name":name,"status":status,"detail":detail})

    # Step 1: Category plan
    try:
        from smr_cninfo_targeted_disclosure_category_planner import load_category_plan
        plan=load_category_plan()
        add_step("category_plan","ok",str(len(plan.get("priority_categories",[])))+" categories loaded")
    except Exception as e:
        add_step("category_plan","error",str(e)[:50])

    # Step 2: Targeted metadata harvest
    if skip_network or mode=="dry-run":
        add_step("targeted_metadata_harvest","skipped" if skip_network else "dry_run")
    else:
        try:
            from smr_cninfo_targeted_metadata_harvester import harvest_targeted_metadata
            meta=harvest_targeted_metadata(ticker,max_metadata,skip_network=False,mode="execute")
            inv=meta.get("cninfo_targeted_metadata_inventory",{})
            p["targeted_metadata_selected"]=inv.get("targeted_metadata_selected",0)
            add_step("targeted_metadata_harvest","ok",str(p["targeted_metadata_selected"])+" sources selected")
        except Exception as e:
            add_step("targeted_metadata_harvest","error",str(e)[:50])

    # Step 3: Business keyword hit scan
    try:
        from smr_business_keyword_hit_scanner import scan_metadata_rows
        meta=harvest_targeted_metadata(ticker,max_metadata,skip_network=skip_network,mode="skip" if skip_network else "execute")
        rows=meta.get("cninfo_targeted_metadata_inventory",{}).get("rows",[])
        scan=scan_metadata_rows(rows)
        add_step("business_keyword_hit_scan","ok",str(scan.get("sources_with_keyword_hit",0))+" hits")
    except Exception as e:
        add_step("business_keyword_hit_scan","error",str(e)[:50])

    # Step 4: Priority PDF selection
    try:
        from smr_priority_pdf_selector import select_priority_pdfs
        sel=select_priority_pdfs(rows,max_pdfs)
        add_step("priority_pdf_selection","ok",str(sel.get("selected_pdfs",0))+" selected")
    except Exception as e:
        add_step("priority_pdf_selection","error",str(e)[:50])

    # Step 5: Expanded PDF text extraction
    if skip_network or mode=="dry-run":
        add_step("expanded_pdf_text_extraction","skipped" if skip_network else "dry_run")
    else:
        try:
            from run_phase66_expanded_pdf_text_extraction import run_expanded_extraction
            ex=run_expanded_extraction(ticker,max_pdfs,skip_network=False,mode="execute")
            exd=ex.get("expanded_pdf_text_extraction",{})
            p["pdf_text_ok"]=exd.get("pdf_text_ok",0)
            add_step("expanded_pdf_text_extraction","ok_or_degraded",str(p["pdf_text_ok"])+" texts extracted")
        except Exception as e:
            add_step("expanded_pdf_text_extraction","error",str(e)[:50])

    # Step 6: Business evidence text quality
    try:
        from smr_business_evidence_text_quality_scoring import score_texts
        from build_phase66_business_evidence_text_quality import build as build_qual
        qual=build_qual(ticker)
        q=qual.get("business_evidence_text_quality",{})
        usable=q.get("high_business_signal",0)+q.get("usable_business_signal",0)
        p["texts_usable_for_evidence"]=usable
        add_step("business_evidence_text_quality","ok",str(usable)+" usable")
    except Exception as e:
        add_step("business_evidence_text_quality","error",str(e)[:50])

    # Step 7: Deep business evidence extraction
    try:
        from build_phase66_deep_business_evidence_extraction import build as build_ev
        ev=build_ev(ticker)
        deep=ev.get("deep_business_evidence_extraction",{})
        p["deep_evidence_created"]=deep.get("evidence_created",0)
        add_step("deep_business_evidence_extraction","ok",str(p["deep_evidence_created"])+" evidence created")
    except Exception as e:
        add_step("deep_business_evidence_extraction","error",str(e)[:50])

    # Step 8: Deep evidence claim map
    try:
        from build_phase66_deep_evidence_claim_map import build as build_cm
        cm=build_cm(ticker)
        claims=cm.get("deep_evidence_claim_map",{})
        p["evidence_gain_delta"]=claims.get("evidence_gain_delta",0)
        add_step("deep_evidence_claim_map","ok",str(claims.get("claims_supported",0))+" supported")
    except Exception as e:
        add_step("deep_evidence_claim_map","error",str(e)[:50])

    # Step 9: Cannot-conclude guard
    try:
        from build_phase66_deep_evidence_cannot_conclude_guard import build as build_guard
        gr=build_guard(ticker)
        gs=gr.get("deep_evidence_cannot_conclude_guard",{}).get("guard_status","pass")
        add_step("cannot_conclude_guard",gs)
    except Exception as e:
        add_step("cannot_conclude_guard","error",str(e)[:50])

    # Step 10: Evidence gain analytics
    try:
        from build_phase66_real_disclosure_evidence_gain_analytics import build as build_ga
        ga=build_ga(ticker)
        add_step("evidence_gain_analytics","ok")
    except Exception as e:
        add_step("evidence_gain_analytics","error",str(e)[:50])

    # Step 11: Watchlist update
    try:
        from build_phase66_watchlist_update_from_deep_disclosure import build as build_wu
        wu=build_wu(ticker)
        add_step("watchlist_update","ok")
    except Exception as e:
        add_step("watchlist_update","error",str(e)[:50])

    # Step 12: Brief
    try:
        from build_phase66_deep_disclosure_evidence_brief import build as build_brief
        br=build_brief(ticker)
        add_step("brief","ok")
    except Exception as e:
        add_step("brief","error",str(e)[:50])

    # Step 13: Dashboard
    try:
        from build_phase66_targeted_disclosure_harvest_dashboard import build as build_dash
        dash=build_dash(ticker)
        add_step("dashboard","ok")
    except Exception as e:
        add_step("dashboard","error",str(e)[:50])

    p["steps"]=steps
    return r

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ticker",default="300308.SZ")
    p.add_argument("--dry-run",action="store_true")
    p.add_argument("--execute",action="store_true")
    p.add_argument("--skip-network",action="store_true")
    p.add_argument("--max-metadata",type=int,default=50)
    p.add_argument("--max-pdfs",type=int,default=15)
    p.add_argument("--json",action="store_true")
    a=p.parse_args()
    mode="execute" if getattr(a,"execute",False) else "dry_run"
    skip=getattr(a,"skip_network",False)
    r=run_pipeline(a.ticker,a.max_metadata,a.max_pdfs,skip_network=skip,mode=mode)
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
