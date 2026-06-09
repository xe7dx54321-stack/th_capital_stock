# Phase204 HK/US Real Verification & Store Backfill runner
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
from smr_phase204_hk_us_real_verification_store_backfill import *

def run():
    dry_run = '--dry-run' in sys.argv
    skip_network = '--skip-network' in sys.argv
    execute = '--execute' in sys.argv
    write_backfill = '--write-store-backfill' in sys.argv
    
    if execute and write_backfill:
        mode = 'write-store-backfill'
    elif execute:
        mode = 'execute'
    elif dry_run:
        mode = 'dry-run'
    else:
        mode = 'skip-network'
    
    an = execute and not skip_network
    wb = write_backfill
    
    config = build_phase204_config()
    p203 = build_phase203_loader()
    p201 = build_phase201_store_loader()
    audit = build_additive_source_audit()
    tasks = build_hk_us_verification_tasks()
    vfy = build_hk_us_verification_execution(an)
    classifier = build_verification_classifier(an)
    candidates = build_store_backfill_candidates(an)
    manifest = build_store_backfill_manifest(an)
    writer = build_store_backfill_writer(an, wb)
    integrity = build_store_backfill_integrity(wb)
    rollback = build_store_backfill_rollback(wb)
    coverage = build_packet_coverage_refresh(an)
    ticker_reports = build_hk_us_ticker_reports(an)
    p394 = build_300394_report()
    board = build_hk_us_verification_board(an)
    brief = build_hk_us_verification_brief(an)
    backlog = build_backlog_update(an)
    guard = build_cannot_conclude_guard()
    gate = build_quality_gate(an)
    dashboard = build_dashboard(an, wb)

    a = audit['phase204_additive_source_audit']
    v = vfy['phase204_hk_us_verification_execution']
    cl = classifier['phase204_verification_classifier']
    ca = candidates['phase204_store_backfill_candidates']
    w = writer['phase204_store_backfill_writer']
    cv = coverage['phase204_packet_coverage_refresh']
    g = guard['phase204_cannot_conclude_guard']
    q = gate['phase204_quality_gate']

    summary = {
        'phase204_hk_us_real_verification_store_backfill': {
            'mode': mode,
            'target_ticker_count': 4,
            'hk_ticker_count': 2, 'us_ticker_count': 2,
            'additive_source_audit_generated': a['audit_generated'],
            'ifind_replacement_detected': a['ifind_replacement_detected'],
            'existing_sources_preserved': a['existing_sources_preserved'],
            'existing_adapters_preserved': a['existing_adapters_preserved'],
            'verification_task_count': tasks['phase204_hk_us_verification_tasks']['task_count'],
            'verification_executed_count': v['verification_executed_count'],
            'verified_support_count': v['verified_support_count'],
            'verified_context_only_count': v['verified_context_only_count'],
            'manual_review_count': v['manual_review_count'],
            'insufficient_count': v['insufficient_count'],
            'rejected_count': v['rejected_count'],
            'eligible_clean_candidate_count': cl['eligible_clean_candidate_count'],
            'eligible_context_candidate_count': cl['eligible_context_candidate_count'],
            'store_backfill_candidate_count': ca['backfill_candidate_count'],
            'direct_backfill_count': ca['direct_backfill_count'],
            'context_backfill_count': ca['context_backfill_count'],
            'duplicate_skipped_count': ca['duplicate_skipped_count'],
            'store_backfill_written': w['store_backfill_written'],
            'backfill_path': w['backfill_path'],
            'backfill_path_gitignored': w['backfill_path_gitignored'],
            'pre_backfill_store_total': p201['phase204_phase201_store_loader']['pre_backfill_total'],
            'packet_coverage_refresh_generated': cv['coverage_refresh_generated'],
            'missing_ticker_count_after_phase204': cv['missing_ticker_count_after_phase204'],
            'ticker_reports_generated': ticker_reports['phase204_hk_us_ticker_reports']['ticker_reports_generated'],
            '300394_cninfo_limitation_retained': p394['phase204_300394_report']['300394_cninfo_limitation_retained'],
            'board_generated': board['phase204_hk_us_verification_board']['board_generated'],
            'brief_generated': brief['phase204_hk_us_verification_brief']['brief_generated'],
            'backlog_generated': backlog['phase204_backlog_update']['backlog_generated'],
            'dashboard_generated': dashboard['phase204_dashboard']['dashboard_generated'],
            'guard_pass': g['guard_pass'],
            'violations': g['violations_count'],
            'quality_gate': q['gate_pass'],
            'formal_packet_updated': False,
            'research_packet_updated': False,
            'evidence_packet_updated': False,
            'daily_brief_updated': False,
            'weekly_review_updated': False,
            'watch_core_updated': False,
            'daily_monitoring_state_updated': False,
            'thesis_state_updated': False,
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
