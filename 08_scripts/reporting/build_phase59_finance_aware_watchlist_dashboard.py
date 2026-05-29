#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_watchlist_industry_financial_signal_adapter import build_watchlist_industry_financial_signal_adapter
from smr_watchlist_financial_delta_detector import detect_watchlist_financial_delta
from smr_finance_aware_thesis_review import run_finance_aware_thesis_review
from smr_finance_aware_watchlist_decision import make_finance_aware_watchlist_decision


def build(conn, ticker='300308.SZ'):
    adapter = build_watchlist_industry_financial_signal_adapter(ticker)
    delta = detect_watchlist_financial_delta(ticker)
    review = run_finance_aware_thesis_review(ticker)
    decision = make_finance_aware_watchlist_decision(ticker)

    ad = adapter['watchlist_industry_financial_signal_adapter']
    dl = delta['watchlist_financial_delta']
    rd = review['finance_aware_thesis_review']
    dd = decision['finance_aware_watchlist_decision']

    return {
        'summary': {
            'ticker': ticker,
            'industry': 'ai_optical_module',
            'real_financial_data_used': ad['real_financial_data_used'],
            'industry_variables_loaded': ad['industry_variables_loaded'],
            'variables_strengthened': dl['variables_strengthened'],
            'variables_weakened': dl['variables_weakened'],
            'variables_unconfirmed': dl['variables_unjudgeable'],
            'thesis_claims_strengthened': rd['claims_strengthened'],
            'decision': dd['decision'],
            'daily_brief_ready': True,
            'cannot_conclude_guard_status': ad['cannot_conclude_guard_status'],
            'pending_created': 0,
            'paper_order_created': 0,
            'real_trade_created': 0,
        }
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--json', action='store_true'); p.add_argument('--markdown', action='store_true')
    args = p.parse_args(); r = build(None)
    if args.markdown:
        d = r['summary']
        print(f"# Phase 59 Finance-Aware Watchlist Dashboard")
        print(f"\n- Ticker: {d['ticker']}")
        print(f"- Real data: {d['real_financial_data_used']}")
        print(f"- Variables: {d['industry_variables_loaded']} loaded")
        print(f"- Strengthened/Weakened/Unconfirmed: {d['variables_strengthened']}/{d['variables_weakened']}/{d['variables_unconfirmed']}")
        print(f"- Thesis strengthened: {d['thesis_claims_strengthened']}")
        print(f"- Decision: {d['decision']}")
        print(f"- Brief ready: {d['daily_brief_ready']}")
        print(f"- Guard: {d['cannot_conclude_guard_status']}")
        print(f"- Pending/Order/Trade: 0/0/0")
    else: print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == '__main__': main()
