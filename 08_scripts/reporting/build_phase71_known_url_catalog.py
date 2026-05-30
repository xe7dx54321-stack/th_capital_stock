#!/usr/bin/env python3
"""Phase 71 known URL catalog."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))

def build():
    from smr_known_disclosure_url_catalog import build_catalog_report
    return build_catalog_report()

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build(); cat = r["known_url_catalog"]
    if a.markdown:
        lines = ["# Known URL Catalog", "", f"Entries: {cat['entries_total']}", f"Available: {cat['available']}", f"Manual required: {cat['manual_fill_required']}"]
        print("\n".join(lines))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
