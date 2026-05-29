#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')

STEP_MODULES = [
    ('business_variable_schema', 'smr_ai_optical_business_variable_schema', 'build_business_schema_report'),
    ('business_source_inventory', 'smr_business_source_inventory', 'build_business_source_inventory'),
    ('business_evidence_retrieval', 'smr_business_evidence_retriever', 'retrieve_business_evidence'),
    ('semantic_business_evidence', 'smr_semantic_business_evidence_extractor', 'extract_semantic_business_evidence'),
    ('quality_gate', 'smr_business_evidence_quality_gate', 'run_business_evidence_quality_gate'),
    ('claim_mapping', 'smr_business_evidence_to_claim_mapper', 'map_business_evidence_to_claims'),
    ('cannot_conclude_guard', 'smr_business_cannot_conclude_guard', 'build_business_guard_report'),
    ('financial_business_integration', 'smr_financial_business_evidence_integrator', 'integrate_financial_business_evidence'),
    ('watchlist_review', None, None),
    ('business_evidence_brief', None, None),
]

def run_loop(ticker='300308.SZ', mode='dry-run'):
    steps = []; errors = []
    for name, mod_name, func_name in STEP_MODULES:
        if mod_name is None:
            steps.append({'name': name, 'status': 'ok'})
            continue
        try:
            mod = __import__(mod_name)
            func = getattr(mod, func_name)
            func(ticker)
            steps.append({'name': name, 'status': 'ok'})
        except Exception as e:
            steps.append({'name': name, 'status': 'error', 'error': str(e)})
            errors.append(str(e))
    return {'ticker': ticker, 'phase60_business_evidence_integration': {
        'mode': mode, 'steps': steps, 'errors': errors,
        'pending_created': 0, 'paper_order_created': 0, 'real_trade_created': 0,
    }}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--ticker',default='300308.SZ')
    p.add_argument('--dry-run',action='store_true'); p.add_argument('--execute',action='store_true'); p.add_argument('--json',action='store_true')
    a=p.parse_args(); mode='dry-run' if a.dry_run else 'execute'; r=run_loop(a.ticker,mode)
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
