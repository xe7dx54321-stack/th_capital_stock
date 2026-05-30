#!/usr/bin/env python3
"""Phase 71 company IR page report."""
import argparse, json, sys
from pathlib import Path
J = Path(__file__).resolve().parents[1] / "jobs"
if str(J) not in sys.path: sys.path.insert(0, str(J))

def build():
    from run_phase71_company_ir_page_discovery import run
    return run(mode="execute")

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    if a.markdown:
        rep = r.get("company_ir_page_report", r)
        lines = ["# Company IR Page Report", f"- Tickers: {rep['tickers_checked']}", f"- Found: {rep['ir_pages_found']}", f"- Manual required: {rep['manual_fill_required']}"]
        print("\n".join(lines))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
