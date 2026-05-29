#!/usr/bin/env python3
"""Phase 63b: Source Coverage Report."""
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

    coverage = {}
    for row in d['network_rows']:
        cat = row['source_type'].split('_')[0] if '_' in row['source_type'] else row['source_type']
        cat_map = {'cninfo': 'CNINFO', 'irm': 'IRM', 'exchange': 'SZSE', 'company': 'COMPANY'}
        cat_name = cat_map.get(cat, cat.upper())
        if cat_name not in coverage:
            coverage[cat_name] = {'metadata_found': 0, 'text_found': 0, 'usable_text': 0}
        if row['network_success']:
            coverage[cat_name]['metadata_found'] += 1
        if row['text_extracted']:
            coverage[cat_name]['text_found'] += 1
            coverage[cat_name]['usable_text'] += 1

    for row in d['pdf_rows']:
        if 'CNINFO' not in coverage:
            coverage['CNINFO_PDF'] = {'metadata_found': 0, 'text_found': 0, 'usable_text': 0}
        if row['download_success']:
            coverage['CNINFO_PDF']['metadata_found'] += 1
        if row['text_extracted']:
            coverage['CNINFO_PDF']['text_found'] += 1

    return {'ticker': ticker, 'phase63b_source_coverage_report': {
        'sources_checked': d['sources_checked'],
        'sources_success': d['sources_success'],
        'sources_failed': d['sources_failed'],
        'cninfo_reachable': d['cninfo_reachable'],
        'irm_reachable': d['irm_reachable'],
        'szse_reachable': d['szse_reachable'],
        'coverage_by_source': coverage,
        'mock_used': False, 'fixture_used': False,
        'pending_created': 0,
    }}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--ticker',default='300308.SZ')
    p.add_argument('--json',action='store_true'); p.add_argument('--markdown',action='store_true')
    a=p.parse_args(); r=build(None,a.ticker); d=r['phase63b_source_coverage_report']

    if a.markdown:
        print(f"# Source Coverage Report\n- Ticker: {r['ticker']}")
        print(f"- Checked: {d['sources_checked']} | Success: {d['sources_success']} | Failed: {d['sources_failed']}")
        print(f"- CNINFO: {d['cninfo_reachable']} | IRM: {d['irm_reachable']} | SZSE: {d['szse_reachable']}")
        print(f"\n## 各源覆盖")
        for cat, stats in d['coverage_by_source'].items():
            print(f"### {cat}")
            print(f"- Metadata: {stats['metadata_found']} | Text: {stats['text_found']} | Usable: {stats['usable_text']}")
    else:
        print(json.dumps(r,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
