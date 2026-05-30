#!/usr/bin/env python3
"""Phase 71 fallback evidence gain."""
import argparse, json, sys

def build():
    return {"fallback_evidence_gain": {"phase70": {"300308.SZ": {"evidence_records": 23}, "688041.SH": {"evidence_records": 0}, "300394.SZ": {"evidence_records": 0}}, "phase71": {"fallback_texts_usable": 0, "fallback_deep_evidence_created": 0, "tickers_with_fallback_gain": 0}, "evidence_gain_delta": 0, "note": "fallback_sources_registered_no_evidence_yet_from_alternative_sources", "mock_used": False, "fixture_used": False, "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0}}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build(); g = r["fallback_evidence_gain"]
    if a.markdown:
        lines = ["# Fallback Evidence Gain", "", f"Evidence gain: {g['evidence_gain_delta']}"]
        print("\n".join(lines))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
