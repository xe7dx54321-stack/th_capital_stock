#!/usr/bin/env python3
"""Phase 71 fallback route plan."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))

def build():
    from smr_disclosure_fallback_route_engine import build_route_plan
    return build_route_plan()

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build(); plan = r["fallback_route_plan"]
    if a.markdown:
        lines = ["# Fallback Route Plan", ""]
        for row in plan["rows"]: lines.append(f"- {row['ticker']}: {row['cninfo_status']} -> {row['fallback_mode']} ({' | '.join(row['routes'])})")
        print("\n".join(lines))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
