#!/usr/bin/env python3
"""Phase 72 fallback text quality."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))
def build():
    from smr_fallback_text_quality_classifier import build_text_quality_report
    return build_text_quality_report()
def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    if a.markdown:
        d = r["phase72_fallback_text_quality"]
        lines = ["# Fallback Text Quality", "", f"Checked: {d['texts_checked']}", f"Usable: {d['texts_usable']}", f"Rejected: {d['rejected']}"]
        print("\n".join(lines))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == "__main__": main()
