#!/usr/bin/env python3
"""Phase 71: IRM interaction fetch job."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))

def run(mode="execute", skip_network=False):
    from smr_irm_interaction_connector import fetch_irm_qa
    tickers = ["300308.SZ", "688041.SH", "300394.SZ"]
    if mode in ("dry_run", "dry-run"):
        return {"mode": "dry_run", "tickers": tickers, "status": "dry_run"}
    sn = skip_network or mode == "skip_network"
    rows = [fetch_irm_qa(t, skip_network=sn) for t in tickers]
    return {"irm_interaction_report": {"tickers_checked": 3, "rows": rows, "raw_saved": False, "ocr_used": False, "mock_used": False, "fixture_used": False}}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--dry-run", action="store_true"); p.add_argument("--execute", action="store_true"); p.add_argument("--skip-network", action="store_true"); p.add_argument("--json", action="store_true")
    a = p.parse_args(); mode = "execute" if getattr(a, "execute", False) else "dry_run"
    r = run(mode=mode, skip_network=getattr(a, "skip_network", False))
    print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
