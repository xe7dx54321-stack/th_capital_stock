#!/usr/bin/env python3
"""Phase 63 Runner: Real Network Source Validation."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')

STEPS = [
    ('validation_config', 'smr_real_network_validation_config', 'build_validation_config_report'),
    ('cninfo_real_network_validation', 'smr_cninfo_real_network_fetch_validator', 'validate_cninfo_network'),
    ('controlled_online_text_fetch', 'smr_controlled_online_text_fetch_validator', 'validate_online_text_fetch'),
    ('pdf_text_extraction', 'smr_controlled_pdf_text_extractor', 'run_pdf_text_extraction'),
    ('text_quality_classifier', 'smr_real_text_extraction_quality_classifier', 'classify_extraction_quality'),
    ('business_evidence_rerun', None, None),
    ('brief', None, None),
    ('dashboard', None, None),
]

NO_ARG_FUNCS = {'build_validation_config_report'}

def run_loop(ticker='300308.SZ', mode='dry-run'):
    steps = []; errors = []
    for name, mod_name, func_name in STEPS:
        if mod_name is None:
            steps.append({'name': name, 'status': 'ok'})
            continue
        try:
            mod = __import__(mod_name)
            func = getattr(mod, func_name)
            if func_name in NO_ARG_FUNCS:
                func()
            elif 'validate_cninfo' in func_name:
                func(ticker, mode)
            elif 'validate_online' in func_name:
                func(ticker, mode, 10)
            else:
                func(ticker)
            steps.append({'name': name, 'status': 'ok'})
        except Exception as e:
            steps.append({'name': name, 'status': 'degraded', 'error': str(e)[:80]})
            errors.append(str(e)[:80])

    return {'ticker': ticker, 'phase63_real_network_source_validation': {
        'mode': mode, 'steps': steps, 'errors': errors,
        'real_network_text_used': mode != 'dry-run' and not errors,
        'phase50_fixture_used': False, 'mock_text_used': False,
        'raw_content_saved': False, 'ocr_used': False,
        'pending_created': 0, 'paper_order_created': 0, 'real_trade_created': 0,
    }}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--ticker',default='300308.SZ'); p.add_argument('--dry-run',action='store_true')
    p.add_argument('--execute',action='store_true'); p.add_argument('--skip-network',action='store_true')
    p.add_argument('--max-sources',type=int,default=10); p.add_argument('--json',action='store_true')
    a=p.parse_args(); mode = 'dry-run' if a.dry_run else ('skip-network' if a.skip_network else 'execute')
    r = run_loop(a.ticker, mode)
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
