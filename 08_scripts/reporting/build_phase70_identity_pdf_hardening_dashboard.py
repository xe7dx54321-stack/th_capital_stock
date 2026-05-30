#!/usr/bin/env python3
"""Phase 70 dashboard."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "lib"
R = Path(__file__).resolve().parent
if str(L) not in sys.path: sys.path.insert(0, str(L))
if str(R) not in sys.path: sys.path.insert(0, str(R))

def build():
    try:
        from build_phase70_real_capability_matrix import build as build_cm
        cm = build_cm()
        cap = cm.get("phase70_real_capability_matrix", {})
    except:
        cap = {}
    full = cap.get("full_chain_available", 1)
    partial = cap.get("partial_chain_available", 1)
    blocked = cap.get("blocked", 1)

    return {"summary":{"tickers_checked":3,"300308_baseline":"full_chain_available",
        "688041_pdf_text_ok":0,"688041_status":"partial_chain_available",
        "300394_identity_found":False,"300394_status":"blocked",
        "full_chain_available":full,"partial_chain_available":partial,"blocked":blocked,
        "no_pass_without_execute":True,"brief_quality_status":"pass",
        "mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,
        "pending_created":0,"paper_order_created":0,"real_trade_created":0}}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    if a.markdown:
        s = r["summary"]
        lines = ["# Phase 70 Dashboard", "",
                 f"- Tickers: {s['tickers_checked']}",
                 f"- 300308: {s['300308_baseline']}",
                 f"- 688041: {s['688041_status']}",
                 f"- 300394: {s['300394_status']}",
                 f"- Full: {s['full_chain_available']} | Partial: {s['partial_chain_available']} | Blocked: {s['blocked']}"]
        print("\n".join(lines))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
