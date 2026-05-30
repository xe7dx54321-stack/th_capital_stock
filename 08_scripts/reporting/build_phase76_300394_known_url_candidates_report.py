#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))
from smr_phase76_known_url_breakthrough import load_candidates, verify_candidates

def build():
    candidates = load_candidates("300394.SZ")
    verified = verify_candidates(candidates)
    vc = sum(1 for c in verified if c["verification_status"] == "verified")
    mf = sum(1 for c in verified if c.get("candidate_status") == "manual_fill_required")
    return {"phase76_300394_known_url_candidates": {
        "ticker": "300394.SZ", "candidates_checked": len(verified),
        "verified_candidates": vc, "manual_fill_required_remaining": mf,
        "rows": verified, "mock_used": False, "fixture_used": False
    }}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
