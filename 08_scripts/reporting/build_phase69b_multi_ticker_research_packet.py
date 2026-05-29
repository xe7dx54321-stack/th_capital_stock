#!/usr/bin/env python3
"""Phase 69b multi-ticker research packet."""
import argparse, json, sys
def build():
    return {'phase69b_multi_ticker_research_packet': {'tickers': [
        {'ticker': '300308.SZ', 'research_status': 'full_evidence_backed_tracking', 'key_supported_claims': ['800G_signal_supported','1_6T_signal_supported','product_mix_partially_supported','shipment_delivery_supported','order_visibility_partially_supported','capacity_expansion_supported'], 'key_unconfirmed_claims': ['asp_trend_unconfirmed','customer_share_unconfirmed','specific_order_volume_unconfirmed']},
        {'ticker': '688041.SH', 'research_status': 'identity_verified_metadata_available_pdf_pending', 'key_supported_claims': [], 'key_unconfirmed_claims': [], 'partial_reason': 'pdf_download_text_extraction_pending'},
        {'ticker': '300394.SZ', 'research_status': 'blocked_identity_missing', 'blocker': 'org_id_not_in_curated_identities_manual_required'}
    ], 'pending_created': 0, 'paper_order_created': 0, 'real_trade_created': 0}}
def main():
    p = argparse.ArgumentParser(); p.add_argument('--json', action='store_true'); p.add_argument('--markdown', action='store_true')
    a = p.parse_args(); r = build()
    if a.json: print(json.dumps(r, ensure_ascii=False, indent=2))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == '__main__': main()
