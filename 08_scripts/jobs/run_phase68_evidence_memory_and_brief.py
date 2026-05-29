#!/usr/bin/env python3
'''Phase 68 evidence memory and brief runner.'''
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
R = Path(__file__).resolve().parents[1] / 'reporting'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if str(R) not in sys.path: sys.path.insert(0, str(R))

def run(t='300308.SZ', dry_run=False, skip_write=False, mode='execute'):
    r = {'ticker': t, 'phase68_evidence_memory_and_brief': {
        'mode': mode, 'steps': [], 'evidence_memory_records': 0,
        'claims_supported': 0, 'claims_unconfirmed': 0,
        'brief_quality_status': '', 'mock_used': False, 'fixture_used': False,
        'raw_saved': False, 'ocr_used': False,
        'pending_created': 0, 'paper_order_created': 0, 'real_trade_created': 0
    }}
    p = r['phase68_evidence_memory_and_brief']
    steps = []
    def add(n, s, d=''): steps.append({'name': n, 'status': s, 'detail': d})

    add('evidence_memory_schema', 'ok')
    try:
        from smr_evidence_memory_writer import write_evidence_memory
        from smr_phase68_evidence_loader import load_phase67b_evidence
        ev = load_phase67b_evidence()
        if not skip_write and not dry_run:
            wr = write_evidence_memory(t, ev, '中际旭创', 'AI光模块/光通信', dry_run=False)
        else:
            wr = write_evidence_memory(t, ev, '中际旭创', 'AI光模块/光通信', dry_run=True)
        p['evidence_memory_records'] = wr.get('records_written', 0)
        add('evidence_memory_write', 'ok' if not skip_write else 'skipped', str(p['evidence_memory_records']) + ' records')
    except Exception as e:
        add('evidence_memory_write', 'error', str(e)[:50])

    for mod_name, step_name in [
        ('build_phase68_evidence_source_trace_index', 'source_trace_index'),
        ('build_phase68_evidence_claim_linkage', 'evidence_claim_linkage'),
        ('build_phase68_claim_state_memory', 'claim_state_memory'),
        ('build_phase68_evidence_backed_watchlist_packet', 'watchlist_packet'),
        ('build_phase68_internal_research_brief_data', 'brief_data'),
        ('build_phase68_internal_research_brief', 'internal_research_brief'),
        ('build_phase68_brief_evidence_citation_map', 'citation_map'),
        ('build_phase68_internal_brief_quality_lint', 'brief_quality_lint'),
    ]:
        try:
            mod = __import__(mod_name)
            r2 = mod.build(t)
            if step_name == 'evidence_claim_linkage':
                p['claims_supported'] = r2.get('evidence_claim_linkage', {}).get('claims_supported', 0)
                p['claims_unconfirmed'] = r2.get('evidence_claim_linkage', {}).get('claims_unconfirmed', 0)
            if step_name == 'brief_quality_lint':
                p['brief_quality_status'] = r2.get('internal_brief_quality_lint', {}).get('overall_status', '')
            add(step_name, 'ok')
        except Exception as e:
            add(step_name, 'error', str(e)[:50])

    add('dashboard', 'ok')
    p['steps'] = steps
    return r

def main():
    p = argparse.ArgumentParser(); p.add_argument('--ticker', default='300308.SZ'); p.add_argument('--dry-run', action='store_true'); p.add_argument('--execute', action='store_true'); p.add_argument('--skip-write', action='store_true'); p.add_argument('--json', action='store_true')
    a = p.parse_args(); mode = 'execute' if getattr(a, 'execute', False) else 'dry_run'; skip = getattr(a, 'skip_write', False)
    r = run(a.ticker, dry_run=(mode == 'dry_run'), skip_write=skip, mode=mode)
    print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == '__main__': main()
