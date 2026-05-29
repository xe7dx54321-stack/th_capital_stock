#!/usr/bin/env python3
"""Phase 61: Real Business Evidence Watchlist Review.
Integrates real business evidence into watchlist review.
"""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from build_phase61_real_business_evidence_to_claim_map import map_real_evidence_to_claims
from build_phase61_financial_real_business_evidence_integration import integrate_financial_real_business

def build_real_watchlist_review(ticker='300308.SZ'):
    biz = map_real_evidence_to_claims(ticker)
    joint = integrate_financial_real_business(ticker)
    bd = biz['real_business_evidence_to_claim_map']
    jd = joint['financial_real_business_evidence_integration']

    return {'ticker': ticker, 'real_business_evidence_watchlist_review': {
        'business_claims_strengthened': bd['claims_supported'],
        'business_claims_partially_supported': bd['claims_partially_supported'],
        'business_claims_unconfirmed': bd['claims_unconfirmed'],
        'finance_business_joint_claims_strengthened': jd['joint_claims_strengthened'],
        'watchlist_decision_update': 'continue_tracking_real_business_and_financial_evidence_strengthened',
        'decision_reason': [
            '真实财务数据支持收入和利润端兑现',
            '真实业务证据支持产品结构和出货方向仍偏正向',
            '客户份额、ASP、具体订单量仍未确认',
        ],
        'pending_created': 0, 'paper_order_created': 0, 'real_trade_created': 0,
    }}

def build(conn,t=None): return build_real_watchlist_review(t or '300308.SZ')
def main():
    p=argparse.ArgumentParser(); p.add_argument('--ticker',default='300308.SZ'); p.add_argument('--json',action='store_true'); p.add_argument('--markdown',action='store_true')
    a=p.parse_args(); r=build(None,a.ticker)
    if a.markdown:
        d=r['real_business_evidence_watchlist_review']
        print(f"# Real Business Evidence Watchlist Review\n- Ticker: {r['ticker']}")
        print(f"- Biz claims strengthened: {d['business_claims_strengthened']}")
        print(f"- Biz claims unconfirmed: {d['business_claims_unconfirmed']}")
        print(f"- Joint strengthened: {d['finance_business_joint_claims_strengthened']}")
        print(f"- Decision: {d['watchlist_decision_update']}")
        for x in d['decision_reason']: print(f"  - {x}")
        print(f"- P/O/T: 0/0/0")
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
