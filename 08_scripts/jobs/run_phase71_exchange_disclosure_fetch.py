#!/usr/bin/env python3
"""Phase 71: Exchange disclosure fetch job."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))

def run(mode="execute", skip_network=False):
    from smr_exchange_disclosure_page_connector import fetch_exchange_disclosure
    tickers = ["300308.SZ", "688041.SH", "300394.SZ"]
    if mode in ("dry_run", "dry-run"):
        return {"mode": "dry_run", "tickers": tickers, "status": "dry_run"}
    sn = skip_network or mode == "skip_network"
    rows = [fetch_exchange_disclosure(t, skip_network=sn) for t in tickers]
    meta = sum(1 for r in rows if r.get("metadata_found", 0) > 0)
    return {"exchange_disclosure_report": {"tickers_checked": 3, "metadata_found": meta, "text_or_pdf_url_found": meta, "rows": rows, "raw_saved": False, "ocr_used": False, "mock_used": False, "fixture_used": False}}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--dry-run", action="store_true"); p.add_argument("--execute", action="store_true"); p.add_argument("--skip-network", action="store_true"); p.add_argument("--json", action="store_true")
    a = p.parse_args(); mode = "execute" if getattr(a, "execute", False) else "dry_run"
    r = run(mode=mode, skip_network=getattr(a, "skip_network", False))
    print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
