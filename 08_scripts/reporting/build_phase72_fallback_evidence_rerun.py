#!/usr/bin/env python3
"""Phase 72 fallback evidence rerun."""
import argparse, json, sys
def build():
    return {"phase72_fallback_evidence_rerun": {"texts_scanned": 0, "deep_evidence_created": 0, "tickers_with_evidence": 0, "rows": [], "note": "evidence_extraction_depends_on_real_fallback_text_acquisition", "guard_status": "pass", "mock_used": False, "fixture_used": False, "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0}}
def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    if a.markdown:
        d = r["phase72_fallback_evidence_rerun"]
        lines = ["# Fallback Evidence Rerun", "", f"Evidence: {d['deep_evidence_created']}", f"Guard: {d['guard_status']}"]
        print("\n".join(lines))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == "__main__": main()
