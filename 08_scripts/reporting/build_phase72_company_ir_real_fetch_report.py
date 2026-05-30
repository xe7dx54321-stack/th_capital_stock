#!/usr/bin/env python3
"""Phase 72 company IR real fetch report."""
import argparse, json, sys
from pathlib import Path
J = Path(__file__).resolve().parents[1] / "jobs"
if str(J) not in sys.path: sys.path.insert(0, str(J))
def build():
    from run_phase72_company_ir_real_fetch import run
    return run(mode="execute")
def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build(); d = r["phase72_company_ir_real_fetch"]
    if a.markdown:
        lines = ["# Company IR Real Fetch", "", f"Pages attempted: {d['company_pages_fetch_attempted']}", f"Manual required: {d['manual_fill_required']}"]
        print("\n".join(lines))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == "__main__": main()
