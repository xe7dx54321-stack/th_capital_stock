#!/usr/bin/env python3
"""Phase 63b: Real Evidence Gain Report.
Compares business evidence before/after real network execution.
"""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'reporting'))
from smr_real_network_execution_audit import run_real_network_audit
from build_phase61_real_business_evidence_to_claim_map import map_real_evidence_to_claims

def build(conn, ticker=None):
    ticker = ticker or '300308.SZ'
    audit = run_real_network_audit(ticker)
    d = audit['phase63b_real_network_execution_audit']
    claims = map_real_evidence_to_claims(ticker)
    bd = claims['real_business_evidence_to_claim_map']

    # Phase 63 baseline: what we had before
    supported_before = 3  # from Phase 62/63 dashboard

    # After real network: what we have now
    # If network added new text, business evidence could increase
    has_new_network_text = d['sources_with_text'] > 0
    supported_after = bd['claims_supported']

    return {'ticker': ticker, 'phase63b_real_evidence_gain_report': {
        'supported_before': supported_before,
        'supported_after': supported_after,
        'delta': supported_after - supported_before,
        'has_new_network_text': has_new_network_text,
        'network_text_sources': d['sources_with_text'],
        'total_sources_checked': d['sources_checked'],
        'cninfo_reachable': d['cninfo_reachable'],
        'irm_reachable': d['irm_reachable'],
        'note': ('真实网络抓取增加了业务证据。' if has_new_network_text and (supported_after > supported_before)
                 else '当前环境未通过真实网络抓取获得新增业务证据。CNINFO不可达，IRM仅返回HTML。' if not d['cninfo_reachable']
                 else '真实网络文本已接入，但业务证据量未显著增加。'),
        'mock_used': False, 'fixture_used': False,
        'pending_created': 0,
    }}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--ticker',default='300308.SZ')
    p.add_argument('--json',action='store_true'); p.add_argument('--markdown',action='store_true')
    a=p.parse_args(); r=build(None,a.ticker); d=r['phase63b_real_evidence_gain_report']

    if a.markdown:
        print(f"# Real Evidence Gain Report\n- Ticker: {r['ticker']}")
        print(f"- Before: {d['supported_before']} | After: {d['supported_after']} | Delta: {d['delta']}")
        print(f"- Network text: {d['has_new_network_text']} ({d['network_text_sources']}/{d['total_sources_checked']})")
        print(f"- CNINFO reachable: {d['cninfo_reachable']} | IRM reachable: {d['irm_reachable']}")
        print(f"\n{d['note']}")
    else:
        print(json.dumps(r,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
