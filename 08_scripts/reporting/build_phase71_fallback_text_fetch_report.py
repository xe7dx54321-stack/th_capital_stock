#!/usr/bin/env python3
"""Phase 71 fallback text fetch report."""
import argparse, json, sys
from pathlib import Path
J = Path(__file__).resolve().parents[1] / "jobs"
if str(J) not in sys.path: sys.path.insert(0, str(J))

def build():
    from run_phase71_fallback_text_fetch import run
    return run(mode="execute")

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    if a.markdown:
        rep = r.get("fallback_text_fetch_report", r)
        lines = ["# Fallback Text Fetch", f"- Texts: {rep['texts_fetched']}", f"- Usable: {rep['texts_usable_for_evidence']}"]
        print("\n".join(lines))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
