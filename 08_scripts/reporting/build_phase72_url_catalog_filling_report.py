#!/usr/bin/env python3
"""Phase 72 URL catalog filling report."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))
def build():
    from smr_fallback_url_catalog_filling import build_catalog_filling_report
    return build_catalog_filling_report()
def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build(); d = r["phase72_url_catalog_filling"]
    if a.markdown:
        lines = ["# URL Catalog Filling", "", f"Manual before: {d['manual_fill_required_before']}", f"After: {d['manual_fill_required_after']}"]
        print("\n".join(lines))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == "__main__": main()
