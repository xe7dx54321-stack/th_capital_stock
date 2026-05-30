#!/usr/bin/env python3
"""Phase 72 fallback evidence gain."""
import argparse, json, sys
def build():
    return {"phase72_fallback_evidence_gain": {"phase71": {"fallback_texts_usable": 0, "fallback_deep_evidence_created": 0, "tickers_with_fallback_gain": 0}, "phase72": {"fallback_texts_usable": 0, "fallback_deep_evidence_created": 0, "tickers_with_fallback_gain": 0}, "fallback_evidence_gain_delta": 0, "note": "evidence_gain_depends_on_real_text_acquisition_from_fallback_sources", "source_blockers": [{"ticker": "688041.SH", "source": "sse_page", "stage": "text_acquisition", "blocker": "sse_page_curated_network_execution_pending"}, {"ticker": "300394.SZ", "source": "irm", "stage": "text_acquisition", "blocker": "irm_qa_network_execution_pending"}, {"ticker": "300394.SZ", "source": "company_ir", "stage": "url_filling", "blocker": "manual_fill_required"}], "mock_used": False, "fixture_used": False, "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0}}
def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    if a.markdown:
        d = r["phase72_fallback_evidence_gain"]
        lines = ["# Fallback Evidence Gain", "", f"Delta: {d['fallback_evidence_gain_delta']}"]
        for b in d.get("source_blockers", []): lines.append(f"- {b['ticker']} {b['source']}: {b['blocker']}")
        print("\n".join(lines))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == "__main__": main()
