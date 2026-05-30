#!/usr/bin/env python3
"""Phase 71 alternative source registry report."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))

def build():
    from smr_alternative_disclosure_source_registry import build_registry_report
    return build_registry_report()

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build(); reg = r["alternative_source_registry"]
    if a.markdown:
        lines = ["# Alternative Source Registry", "", f"Sources: {reg['sources_count']}"]
        for s in reg["sources"]: lines.append(f"- {s['source_id']} ({s['source_type']}) P={s['priority']}")
        print("\n".join(lines))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
