#!/usr/bin/env python3
"""Phase 71 fallback evidence extraction."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))

def build():
    from smr_fallback_text_fetcher import fetch_fallback_texts
    from smr_fallback_evidence_extractor import extract_fallback_evidence
    ft = fetch_fallback_texts()
    return extract_fallback_evidence(ft)

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    if a.markdown:
        rep = r["fallback_evidence_extraction"]
        lines = ["# Fallback Evidence Extraction", f"- Texts scanned: {rep['texts_scanned']}", f"- Evidence created: {rep['deep_evidence_created']}"]
        print("\n".join(lines))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
