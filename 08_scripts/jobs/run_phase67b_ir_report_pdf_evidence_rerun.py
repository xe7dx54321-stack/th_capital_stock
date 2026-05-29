#!/usr/bin/env python3
"""Phase 67b IR/report PDF evidence rerun runner."""
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
R=Path(__file__).resolve().parents[1]/"reporting"
J=Path(__file__).resolve().parents[1]/"jobs"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if str(R) not in sys.path: sys.path.insert(0,str(R))
if str(J) not in sys.path: sys.path.insert(0,str(J))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

def run(ticker="300308.SZ",max_pdfs=25,skip_network=False,mode="execute"):
    r={"ticker":ticker,"phase67b_ir_report_pdf_evidence_rerun":{"mode":mode,"steps":[],"selected_high_value_pdfs":0,"pdf_download_ok":0,"pdf_text_ok":0,"texts_usable_for_deep_extraction":0,"deep_evidence_created":0,"evidence_gain_delta":0,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
    p=r["phase67b_ir_report_pdf_evidence_rerun"];steps=[]
    def add(n,s,d=""): steps.append({"name":n,"status":s,"detail":d})

    # 1. PDF pool
    try:
        from smr_phase67_high_value_pdf_pool_loader import load_high_value_pool
        pool=load_high_value_pool(ticker,max_pages=5,max_pdfs=max_pdfs)
        p["selected_high_value_pdfs"]=pool.get("phase67b_high_value_pdf_pool",{}).get("high_value_pdfs",0)
        add("high_value_pdf_pool","ok",str(p["selected_high_value_pdfs"])+" selected")
    except Exception as e: add("high_value_pdf_pool","error",str(e)[:50])

    # 2+3. PDF download + extraction (combined)
    if skip_network or mode=="dry_run":
        add("pdf_download","skipped" if skip_network else "dry_run")
        add("pdf_text_extraction","skipped" if skip_network else "dry_run")
    else:
        try:
            from run_phase67b_high_value_pdf_download import download_and_extract
            dl=download_and_extract(ticker,max_pdfs,mode="execute")
            d=dl.get("high_value_pdf_download",{})
            p["pdf_download_ok"]=d.get("pdf_download_ok",0)
            ok_rows=[r for r in d.get("rows",[]) if r.get("text_extraction_status")=="pdf_text_ok"]
            p["pdf_text_ok"]=len(ok_rows)
            add("pdf_download","ok_or_degraded",str(p["pdf_download_ok"])+" downloaded")
            add("pdf_text_extraction","ok_or_degraded",str(p["pdf_text_ok"])+" texts")
        except Exception as e:
            add("pdf_download","error",str(e)[:50])
            add("pdf_text_extraction","error",str(e)[:50])

    # 4-10: Text quality, deep evidence, claim map, guard, analytics, watchlist, brief
    for mod,step_name,key,attr in [
        ("build_phase67b_ir_report_text_quality","text_quality","phase67b_ir_report_text_quality","texts_usable_for_deep_extraction"),
        ("build_phase67b_deep_evidence_extraction","deep_evidence_extraction","phase67b_deep_evidence_extraction","deep_evidence_created"),
        ("build_phase67b_evidence_claim_map","claim_map","phase67b_evidence_claim_map","evidence_gain_delta"),
        ("build_phase67b_cannot_conclude_guard","cannot_conclude_guard",None,None),
        ("build_phase67b_evidence_gain_analytics","evidence_gain_analytics",None,None),
        ("build_phase67b_watchlist_update","watchlist_update",None,None),
        ("build_phase67b_ir_report_evidence_brief","brief",None,None),
        ("build_phase67b_ir_report_pdf_evidence_dashboard","dashboard",None,None),
    ]:
        try:
            exec(f"from {mod} import build; r2=build(ticker)")
            if key and attr:
                val=r2.get(key,{}).get(attr,0)
                p[attr]=val
            add(step_name,"ok")
        except Exception as e: add(step_name,"error",str(e)[:50])

    p["evidence_gain_delta"]=p.get("evidence_gain_delta",0)
    p["steps"]=steps;return r

def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--dry-run",action="store_true");p.add_argument("--execute",action="store_true");p.add_argument("--skip-network",action="store_true");p.add_argument("--max-pdfs",type=int,default=25);p.add_argument("--json",action="store_true")
    a=p.parse_args();mode="execute" if getattr(a,"execute",False) else "dry_run";skip=getattr(a,"skip_network",False)
    r=run(a.ticker,a.max_pdfs,skip_network=skip,mode=mode)
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
