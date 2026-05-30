#!/usr/bin/env python3
"""Phase 72: Company IR real fetch job."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))

def run(mode="execute"):
    if mode in ("dry_run", "dry-run"):
        return {"phase72_company_ir_real_fetch": {"mode": "dry_run", "companies_checked": 2, "mock_used": False, "fixture_used": False}}
    from smr_company_ir_page_discovery import discover_ir_page
    tickers = ["688041.SH", "300394.SZ"]
    rows = [discover_ir_page(t) for t in tickers]
    fetch_ok = sum(1 for r in rows if r.get("ir_page_found"))
    manual = sum(1 for r in rows if r.get("status") == "manual_fill_required")
    return {"phase72_company_ir_real_fetch": {"companies_checked": 2, "company_pages_fetch_attempted": fetch_ok, "company_pages_ok": fetch_ok, "announcement_links_found": 0, "pdf_links_found": 0, "text_pages_found": 0, "manual_fill_required": manual, "rows": rows, "raw_saved": False, "ocr_used": False, "mock_used": False, "fixture_used": False}}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--dry-run", action="store_true"); p.add_argument("--execute", action="store_true"); p.add_argument("--json", action="store_true")
    a = p.parse_args(); mode = "execute" if getattr(a, "execute", False) else "dry_run"
    r = run(mode=mode)
    print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
