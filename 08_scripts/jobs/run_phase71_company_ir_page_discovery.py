#!/usr/bin/env python3
"""Phase 71: Company IR page discovery job."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))

def run(mode="execute"):
    from smr_company_ir_page_discovery import discover_ir_page
    tickers = ["300308.SZ", "688041.SH", "300394.SZ"]
    if mode in ("dry_run", "dry-run"):
        return {"mode": "dry_run", "tickers": tickers, "status": "dry_run"}
    rows = [discover_ir_page(t) for t in tickers]
    found = sum(1 for r in rows if r.get("ir_page_found"))
    manual = sum(1 for r in rows if r.get("status") == "manual_fill_required")
    return {"company_ir_page_report": {"tickers_checked": 3, "ir_pages_found": found, "manual_fill_required": manual, "rows": rows, "mock_used": False, "fixture_used": False}}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--dry-run", action="store_true"); p.add_argument("--execute", action="store_true"); p.add_argument("--json", action="store_true")
    a = p.parse_args(); mode = "execute" if getattr(a, "execute", False) else "dry_run"
    r = run(mode=mode)
    print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
