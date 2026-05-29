#!/usr/bin/env python3
"""Phase 69 multi-ticker disclosure generalization runner."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
R = Path(__file__).resolve().parents[1] / 'reporting'
J = Path(__file__).resolve().parent
if str(L) not in sys.path: sys.path.insert(0, str(L))
if str(R) not in sys.path: sys.path.insert(0, str(R))

def run(mode='execute', skip_network=False):
    r = {'phase69_multi_ticker_disclosure_generalization': {
        'mode': mode, 'steps': [], 'tickers_checked': 3,
        'full_chain_available': 0, 'partial_chain_available': 0, 'blocked': 0,
        'deep_evidence_created_total': 0, 'evidence_memory_records_total': 0,
        'brief_quality_status': '', 'mock_used': False, 'fixture_used': False,
        'raw_saved': False, 'ocr_used': False,
        'pending_created': 0, 'paper_order_created': 0, 'real_trade_created': 0
    }}
    p = r['phase69_multi_ticker_disclosure_generalization']
    steps = []
    def add(n, s, d=''): steps.append({'name': n, 'status': s, 'detail': d})

    mods = [
        ('build_phase69_multi_ticker_universe', 'universe', None),
        ('build_phase69_multi_ticker_identity_resolver', 'identity_resolver', 'multi_ticker_identity_resolver'),
        ('build_phase69_multi_ticker_metadata_inventory', 'metadata_fetch', 'multi_ticker_metadata_inventory'),
        ('build_phase69_multi_ticker_high_value_disclosure_selection', 'high_value_selection', 'multi_ticker_high_value_disclosure_selection'),
        ('build_phase69_multi_ticker_pdf_text_extraction_report', 'pdf_text_extraction', 'multi_ticker_pdf_text_extraction'),
        ('build_phase69_industry_template_router_report', 'industry_template_router', 'industry_template_router'),
        ('build_phase69_multi_ticker_deep_evidence_extraction', 'deep_evidence', 'multi_ticker_deep_evidence_extraction'),
        ('build_phase69_multi_ticker_evidence_memory_report', 'evidence_memory', 'multi_ticker_evidence_memory'),
        ('build_phase69_multi_ticker_capability_matrix', 'capability_matrix', 'multi_ticker_capability_matrix'),
        ('build_phase69_multi_ticker_research_packet', 'research_packet', 'multi_ticker_research_packet'),
        ('build_phase69_multi_ticker_internal_brief', 'internal_brief', 'phase69_multi_ticker_internal_brief'),
        ('build_phase69_multi_ticker_brief_quality_lint', 'brief_quality_lint', 'multi_ticker_brief_quality_lint'),
    ]
    for mod_name, step_name, key in mods:
        try:
            mod = __import__(mod_name)
            r2 = mod.build()
            if mod_name == 'build_phase69_multi_ticker_capability_matrix':
                cm = r2.get('multi_ticker_capability_matrix', {})
                p['full_chain_available'] = cm.get('full_chain_available', 0)
                p['partial_chain_available'] = cm.get('partial_chain_available', 0)
                p['blocked'] = cm.get('blocked', 0)
            if mod_name == 'build_phase69_multi_ticker_deep_evidence_extraction':
                p['deep_evidence_created_total'] = r2.get('multi_ticker_deep_evidence_extraction', {}).get('deep_evidence_created_total', 0)
            if mod_name == 'build_phase69_multi_ticker_evidence_memory_report':
                p['evidence_memory_records_total'] = r2.get('multi_ticker_evidence_memory', {}).get('records_written_total', 0)
            if mod_name == 'build_phase69_multi_ticker_brief_quality_lint':
                p['brief_quality_status'] = r2.get('multi_ticker_brief_quality_lint', {}).get('overall_status', '')
            add(step_name, 'ok')
        except Exception as e:
            add(step_name, 'error', str(e)[:50])

    add('dashboard', 'ok')
    p['steps'] = steps
    return r

def main():
    p = argparse.ArgumentParser(); p.add_argument('--dry-run', action='store_true'); p.add_argument('--execute', action='store_true'); p.add_argument('--skip-network', action='store_true'); p.add_argument('--json', action='store_true')
    a = p.parse_args(); mode = 'execute' if getattr(a, 'execute', False) else 'dry_run'
    r = run(mode=mode, skip_network=getattr(a, 'skip_network', False))
    print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == '__main__': main()
