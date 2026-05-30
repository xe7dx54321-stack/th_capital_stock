#!/usr/bin/env python3
"""Phase 72 research packet."""
import argparse, json, sys
def build():
    tickers = [{"ticker": "300308.SZ", "research_status": "full_evidence_backed_tracking", "cninfo": "full_chain", "fallback": "optional", "key_supported_claims": ["800G_signal_supported", "1_6T_signal_supported", "product_mix_partially_supported", "shipment_delivery_supported", "order_visibility_partially_supported", "capacity_expansion_supported"], "key_unconfirmed_claims": ["asp_trend_unconfirmed", "customer_share_unconfirmed", "specific_order_volume_unconfirmed"]}, {"ticker": "688041.SH", "research_status": "cninfo_metadata_pdf_blocked_sse_candidate_registered", "cninfo": "metadata_ok_pdf_blocked", "fallback": "sse_page_candidate_curated", "blocker": "cninfo_pdf_download_and_text_extraction_failed_sse_network_execution_pending", "partial_reason": "sse_announcement_page_registered_network_execution_pending", "key_supported_claims": [], "key_unconfirmed_claims": []}, {"ticker": "300394.SZ", "research_status": "cninfo_blocked_fallback_irm_szse_registered", "cninfo": "identity_blocked", "fallback": "irm_szse_company_ir_registered", "blocker": "irm_and_szse_network_execution_pending_company_ir_manual", "key_supported_claims": [], "key_unconfirmed_claims": []}]
    return {"phase72_research_packet": {"tickers": tickers, "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0}}
def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    if a.markdown:
        pkt = r["phase72_research_packet"]
        lines = ["# Phase 72 Research Packet"]
        for t in pkt["tickers"]:
            lines.append(f"\n## {t['ticker']}: {t['research_status']}")
            lines.append(f"- CNINFO: {t['cninfo']}")
            lines.append(f"- Fallback: {t['fallback']}")
            if t.get("blocker"): lines.append(f"- Blocker: {t['blocker']}")
        print("\n".join(lines))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == "__main__": main()
