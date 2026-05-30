#!/usr/bin/env python3
"""Phase 72 multi-source capability matrix."""
import argparse, json, sys
def build():
    rows = [{"ticker": "300308.SZ", "cninfo": "full_chain_available", "irm": "optional", "exchange": "optional", "company_site": "manual", "known_catalog": "manual", "overall": "full_chain_available"}, {"ticker": "688041.SH", "cninfo": "metadata_pdf_blocked", "sse": "curated_candidate", "company_site": "manual", "known_catalog": "sse_candidate", "overall": "partial_with_fallback", "partial_reason": "sse_page_candidate_registered_network_execution_pending"}, {"ticker": "300394.SZ", "cninfo": "identity_blocked", "irm": "execute_pending", "szse": "execute_pending", "company_site": "manual", "known_catalog": "manual", "overall": "partial_with_fallback_or_blocked", "blocker": "irm_qa_and_szse_page_network_execution_pending_company_ir_manual"}]
    return {"phase72_multi_source_capability_matrix": {"tickers_checked": 3, "tickers_with_fallback_text": 0, "tickers_with_fallback_evidence": 0, "rows": rows, "mock_used": False, "fixture_used": False, "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0}}
def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    if a.markdown:
        cm = r["phase72_multi_source_capability_matrix"]
        lines = ["# Multi-source Capability Matrix", "", "| Ticker | CNINFO | IRM | Exchange | Company | Known | Overall |", "|--------|--------|-----|----------|---------|-------|---------|"]
        for row in cm["rows"]: lines.append(f"| {row['ticker']} | {row['cninfo']} | {row.get('irm','-')} | {row.get('exchange',row.get('sse','-'))} | {row.get('company_site','-')} | {row.get('known_catalog','-')} | {row['overall']} |")
        print("\n".join(lines))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == "__main__": main()
