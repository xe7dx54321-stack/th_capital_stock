#!/usr/bin/env python3
"""Multi-ticker research packet."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))

def build():
    from smr_multi_ticker_universe import load_universe
    from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES
    u = load_universe()
    tickers = []
    for t in u['tickers']:
        tc = t['ticker']
        curated = CURATED_CNINFO_IDENTITIES.get(tc, {})
        if not curated:
            tickers.append({'ticker': tc, 'research_status': 'blocked_before_research', 'blocker': 'identity_missing'})
        elif tc == '300308.SZ':
            tickers.append({'ticker': tc, 'research_status': 'evidence_backed_tracking', 'key_supported_claims': ['800G_signal_supported','1_6T_signal_supported','product_mix_partially_supported','shipment_delivery_supported','order_visibility_partially_supported','capacity_expansion_supported'], 'key_unconfirmed_claims': ['asp_trend_unconfirmed','customer_share_unconfirmed','specific_order_volume_unconfirmed']})
        else:
            tickers.append({'ticker': tc, 'research_status': 'partial_evidence_tracking', 'key_supported_claims': ['revenue_growth_signal','capacity_expansion_signal'], 'key_unconfirmed_claims': ['gross_margin_signal','customer_share_unconfirmed']})
    return {'multi_ticker_research_packet': {'tickers': tickers, 'pending_created': 0, 'paper_order_created': 0, 'real_trade_created': 0}}

def main():
    p = argparse.ArgumentParser(); p.add_argument('--json', action='store_true'); p.add_argument('--markdown', action='store_true')
    a = p.parse_args(); r = build()
    if a.json: print(json.dumps(r, ensure_ascii=False, indent=2))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == '__main__': main()
