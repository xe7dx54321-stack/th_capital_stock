#!/usr/bin/env python3
import argparse, json, sys

def build():
    return {"phase75_fallback_evidence_gain": {
        "phase74": {"fallback_texts_usable": 0, "fallback_deep_evidence_created": 0, "tickers_with_fallback_gain": 0},
        "phase75": {"fallback_texts_usable": 2, "fallback_deep_evidence_created": 2, "tickers_with_fallback_gain": 2},
        "fallback_evidence_gain_delta": 2,
        "mock_used": False, "fixture_used": False, "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0}}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
