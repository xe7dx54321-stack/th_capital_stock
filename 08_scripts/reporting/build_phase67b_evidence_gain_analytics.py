#!/usr/bin/env python3
"""Phase 67b evidence gain analytics."""
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
def build(t="300308.SZ"):
    r={"ticker":t,"phase67b_evidence_gain_analytics":{"phase66":{"texts_usable":3,"deep_created":5,"gain_delta":0},"phase67":{"ir_found":2,"reports_found":8,"selected_pdfs":0},"phase67b":{"pdf_text_ok":0,"texts_usable":0,"deep_created":0,"gain_delta":0},"incremental":{"texts_vs_66":0,"deep_vs_66":0,"claim_delta":0},"new_claims":[],"mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
    ga=r["phase67b_evidence_gain_analytics"]
    try:
        from build_phase67b_high_value_pdf_text_extraction_report import build as build_tx
        tx=build_tx(t);ga["phase67b"]["pdf_text_ok"]=tx.get("high_value_pdf_text_extraction",{}).get("pdf_text_ok",0)
        from build_phase67b_ir_report_text_quality import build as build_qt
        qt=build_qt(t);ga["phase67b"]["texts_usable"]=qt.get("phase67b_ir_report_text_quality",{}).get("texts_usable_for_deep_extraction",0)
        from build_phase67b_deep_evidence_extraction import build as build_ev
        ev=build_ev(t);ga["phase67b"]["deep_created"]=ev.get("phase67b_deep_evidence_extraction",{}).get("deep_evidence_created",0)
        from build_phase67b_evidence_claim_map import build as build_cm
        cm=build_cm(t);gain=cm.get("phase67b_evidence_claim_map",{}).get("evidence_gain_delta",0)
        ga["phase67b"]["gain_delta"]=gain;ga["incremental"]["texts_vs_66"]=max(0,ga["phase67b"]["texts_usable"]-3)
        ga["incremental"]["deep_vs_66"]=max(0,ga["phase67b"]["deep_created"]-5);ga["incremental"]["claim_delta"]=gain
    except Exception as e: ga["status"]="partial:"+str(e)[:80]
    return r
def _md(r):
    ga=r.get("phase67b_evidence_gain_analytics",r);p=ga.get("phase67b",{})
    lines=["# Evidence Gain Analytics",""];lines.append("Phase 67b: texts="+str(p.get("texts_usable",0))+", deep="+str(p.get("deep_created",0))+", gain="+str(p.get("gain_delta",0)))
    inc=ga.get("incremental",{});lines.append("Delta vs Phase 66: texts="+str(inc.get("texts_vs_66",0))+", deep="+str(inc.get("deep_vs_66",0)))
    return "\n".join(lines)
def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build(a.ticker)
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
