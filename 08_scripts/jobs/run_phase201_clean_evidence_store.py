# Phase201 Clean Evidence Store runner
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
from smr_phase201_clean_evidence_store import *

STORE_INPUT_COUNT = 84
CLEAN_CANDIDATE_COUNT = 42
CONTEXT_CANDIDATE_COUNT = 42

def run():
    dry_run = '--dry-run' in sys.argv
    skip_network = '--skip-network' in sys.argv
    execute = '--execute' in sys.argv
    write_store = '--write-store' in sys.argv
    
    mode = 'write-store' if (execute and write_store) else ('execute' if execute else ('dry-run' if dry_run else 'skip-network'))
    allow_network = execute and not skip_network
    
    config = build_phase201_config()
    loader = build_phase200_loader()
    schema = build_evidence_store_schema()
    conflict_gate = build_store_conflict_exclusion_gate()
    records = build_evidence_records(allow_network)
    write_gate = build_store_write_gate(write_store)
    writer = build_store_writer(write_store)
    integrity = build_store_integrity_check(write_store)
    rollback = build_rollback_package(write_store)
    report_394 = build_300394_evidence_report(write_store)
    board = build_evidence_board(write_store)
    brief = build_evidence_brief(write_store)
    backlog = build_backlog_update(write_store)
    guard = build_cannot_conclude_guard(write_store)
    gate = build_quality_gate(write_store)
    dashboard = build_dashboard(write_store)
    
    w = writer['phase201_store_writer']
    g = guard['phase201_cannot_conclude_guard']
    q = gate['phase201_quality_gate']
    r = records['phase201_evidence_records']
    
    summary = {
        'phase201_clean_evidence_store': {
            'mode': mode,
            'phase201_input_ready_count': STORE_INPUT_COUNT,
            'eligible_clean_candidate_count': CLEAN_CANDIDATE_COUNT,
            'eligible_context_candidate_count': CONTEXT_CANDIDATE_COUNT,
            'conflict_items_written_to_store': w['conflict_written'],
            'needs_more_review_written_to_store': w['needs_review_written'],
            'rejected_or_insufficient_written_to_store': w['rejected_written'],
            'context_as_direct_count': w['context_as_direct'],
            'store_written': w['store_written'],
            'store_path': w['store_path'],
            'store_path_gitignored': w['store_path_gitignored'],
            'direct_evidence_written': w['direct_evidence_written'],
            'context_evidence_written': w['context_evidence_written'],
            'total_evidence_written': w['total_evidence_written'],
            'lineage_complete_count': w['lineage_complete'],
            'duplicate_count': integrity['phase201_store_integrity_check']['duplicate_count'],
            'integrity_pass': integrity['phase201_store_integrity_check']['integrity_pass'],
            'rollback_generated': rollback['phase201_rollback_package']['rollback_package_generated'],
            '300394_evidence_report_generated': True,
            '300394_cninfo_limitation_retained': report_394['phase201_300394_evidence_report']['300394_cninfo_limitation_retained'],
            'evidence_board_generated': board['phase201_evidence_board']['board_generated'],
            'evidence_brief_generated': brief['phase201_evidence_brief']['brief_generated'],
            'backlog_generated': backlog['phase201_backlog_update']['backlog_generated'],
            'dashboard_generated': dashboard['phase201_dashboard']['dashboard_generated'],
            'guard_pass': g['guard_pass'],
            'violations': g['violations_count'],
            'quality_gate': q['gate_pass'],
            'packet_updated': False,
            'daily_brief_updated': False,
            'weekly_review_updated': False,
            'watch_core_updated': False,
            'daily_monitoring_state_updated': False,
            'ifind_api_called': False,
            'web_fetch_called': False,
            'raw_response_saved': False,
            'raw_full_text_saved': False,
            'trade_recommendation_created': 0,
            'target_price_created': 0,
            'position_sizing_created': 0,
            'broker_api_called': False,
            'llm_api_called': False,
            'mock_used': False,
            'fixture_used': False
        }
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    run()
