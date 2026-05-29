#!/usr/bin/env python3
"""Phase 63b: Real Network Verification Dashboard."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_real_network_execution_audit import run_real_network_audit

def build(conn, ticker=None):
    ticker = ticker or '300308.SZ'
    audit = run_real_network_audit(ticker)
    d = audit['phase63b_real_network_execution_audit']

    text_ok = sum(1 for r in d['network_rows'] if r['text_extracted'])
    pdf_ok = sum(1 for r in d['pdf_rows'] if r['text_extracted'])
    failed = d['sources_failed']
    metadata_only = d['sources_success'] - text_ok

    return {'summary': {
        'ticker': ticker, 'phase': '63b',
        'network_attempted': d['network_attempted'],
        'network_available': d['network_available_for_any_source'],
        'cninfo_reachable': d['cninfo_reachable'],
        'irm_reachable': d['irm_reachable'],
        'szse_reachable': d['szse_reachable'],
        'sources_checked': d['sources_checked'],
        'metadata_found': d['sources_success'],
        'text_ok': text_ok,
        'pdf_text_ok': pdf_ok,
        'metadata_only': max(0, metadata_only),
        'failed': failed,
        'business_evidence_created': text_ok + pdf_ok,
        'mock_used': d['mock_used'],
        'fixture_used': d['fixture_used'],
        'raw_content_saved': d['raw_content_saved'],
        'ocr_used': d['ocr_used'],
        'pending_created': d['pending_created'],
        'paper_order_created': 0,
        'real_trade_created': 0,
    }}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--json',action='store_true'); p.add_argument('--markdown',action='store_true')
    a=p.parse_args(); r=build(None); d=r['summary']

    if a.markdown:
        print(f"# Phase 63b Real Network Dashboard\n- Ticker: {d['ticker']} | Phase: {d['phase']}")
        print(f"- Network: {d['network_available']} | CNINFO: {d['cninfo_reachable']} | IRM: {d['irm_reachable']}")
        print(f"- Checked: {d['sources_checked']} | Metadata: {d['metadata_found']}")
        print(f"- Text OK: {d['text_ok']} | PDF OK: {d['pdf_text_ok']} | Meta only: {d['metadata_only']} | Failed: {d['failed']}")
        print(f"- Evidence: {d['business_evidence_created']} | Mock: {d['mock_used']} | Fixture: {d['fixture_used']}")
        print(f"- Raw/OCR: {d['raw_content_saved']}/{d['ocr_used']} | P/O/T: 0/0/0")
        print(f"\n## 结论")
        if d['cninfo_reachable']:
            print("- CNINFO API 可达，可获取metadata和PDF链接。")
        else:
            print("- CNINFO API 不可达（当前网络环境受限）。")
        if d['irm_reachable']:
            print("- IRM互动易可访问但返回HTML，API可能需要调整。")
        else:
            print("- IRM互动易不可达。")
    else:
        print(json.dumps(r,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
