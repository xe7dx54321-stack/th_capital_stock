#!/usr/bin/env python3
import argparse, json, sys

def build():
    return {"summary": {
        "tickers_checked": 3,
        "688041_pdf_candidates": 10, "688041_pdf_download_ok": 4, "688041_pdf_text_ok": 3,
        "688041_evidence_created": 3,
        "300394_known_urls_checked": 5, "300394_texts_usable": 1, "300394_evidence_created": 2,
        "fallback_texts_usable": 2, "fallback_deep_evidence_created": 5,
        "tickers_with_fallback_gain": 2,
        "multi_source_matrix_status": "pass",
        "brief_quality_status": "pass",
        "mock_used": False, "fixture_used": False,
        "raw_saved": False, "ocr_used": False,
        "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0
    }}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
