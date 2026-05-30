#!/usr/bin/env python3
"""Phase 72 known URL real fetch report."""
import argparse, json, sys
from pathlib import Path
J = Path(__file__).resolve().parents[1] / "jobs"
if str(J) not in sys.path: sys.path.insert(0, str(J))
def build():
    from run_phase72_known_url_real_fetch import run
    return run(mode="execute")
def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build(); d = r["phase72_known_url_real_fetch"]
    if a.markdown:
        lines = ["# Known URL Real Fetch", "", f"URLs checked: {d['known_urls_checked']}", f"Verified: {d['known_urls_verified']}"]
        print("\n".join(lines))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == "__main__": main()
