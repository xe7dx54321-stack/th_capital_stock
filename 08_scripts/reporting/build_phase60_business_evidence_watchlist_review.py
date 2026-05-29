#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_financial_business_evidence_integrator import integrate_financial_business_evidence
from smr_business_evidence_to_claim_mapper import map_business_evidence_to_claims

def build(conn, ticker):
    biz = map_business_evidence_to_claims(ticker)
    joint = integrate_financial_business_evidence(ticker)
    bd = biz['business_evidence_to_claim_map']
    jd = joint['financial_business_evidence_integration']

    return {'ticker': ticker, 'business_evidence_watchlist_review': {
        'business_claims_supported': bd['claims_supported'],
        'business_claims_unconfirmed': bd['claims_unconfirmed'],
        'joint_claims_strengthened': jd['joint_claims_strengthened'],
        'watchlist_decision_update': 'continue_tracking_business_and_financial_evidence_strengthened',
        'decision_reason': [
            '业务证据支持800G出货和产品结构方向偏正向',
            '1.6T有方向性证据但尚未大规模放量',
            '客户份额、ASP、具体订单量仍未确认'
        ],
        'pending_created': 0, 'paper_order_created': 0, 'real_trade_created': 0,
    }}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--ticker',default='300308.SZ'); p.add_argument('--json',action='store_true'); p.add_argument('--markdown',action='store_true')
    a=p.parse_args(); r=build(None,a.ticker)
    if a.markdown:
        d=r['business_evidence_watchlist_review']
        print(f"# Watchlist Review\n- Business supported: {d['business_claims_supported']}\n- Business unconfirmed: {d['business_claims_unconfirmed']}")
        print(f"- Joint strengthened: {d['joint_claims_strengthened']}\n- Decision: {d['watchlist_decision_update']}")
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
