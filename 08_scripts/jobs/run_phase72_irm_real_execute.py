#!/usr/bin/env python3
"""Phase 72: IRM real execute job."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))

def run(mode="execute", skip_network=False):
    if mode in ("dry_run", "dry-run"):
        return {"phase72_irm_real_execute": {"mode": "dry_run", "tickers_checked": 3, "mock_used": False, "fixture_used": False}}
    from smr_irm_interaction_connector import fetch_irm_qa
    tickers = ["300308.SZ", "688041.SH", "300394.SZ"]
    sn = skip_network or mode == "skip_network"
    rows = [fetch_irm_qa(t, skip_network=sn) for t in tickers]
    qa_found = sum(r.get("qa_items_found", 0) for r in rows)
    qa_text = sum(r.get("qa_text_available", 0) for r in rows)
    usable = sum(1 for r in rows for item in r.get("items", []) if item.get("answer") and len(item["answer"]) >= 50)
    supported = sum(1 for r in rows if r.get("irm_supported"))
    return {"phase72_irm_real_execute": {"tickers_checked": 3, "irm_supported": supported, "qa_items_found": qa_found, "qa_text_available": qa_text, "qa_text_usable": usable, "rows": rows, "raw_saved": False, "ocr_used": False, "mock_used": False, "fixture_used": False}}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--dry-run", action="store_true"); p.add_argument("--execute", action="store_true"); p.add_argument("--skip-network", action="store_true"); p.add_argument("--json", action="store_true")
    a = p.parse_args(); mode = "execute" if getattr(a, "execute", False) else "dry_run"
    r = run(mode=mode, skip_network=getattr(a, "skip_network", False))
    print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
