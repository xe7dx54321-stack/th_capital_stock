# Phase203 HK/US Evidence Chain Expansion runner
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
from smr_phase203_hk_us_evidence_chain_expansion import *

def run():
    dry_run = '--dry-run' in sys.argv
    skip_network = '--skip-network' in sys.argv
    execute = '--execute' in sys.argv
    mode = 'execute' if execute else ('dry-run' if dry_run else 'skip-network')

    config = build_phase203_config()
    gap = build_phase202_coverage_gap()
    audit = build_additive_source_audit()
    registry = build_hk_us_source_registry()
    routes = build_hk_us_route_plan()
    leads = build_hk_us_source_leads()
    dirty = build_hk_us_dirty_items()
    pairs = build_hk_us_source_pair_candidates()
    verif = build_hk_us_verification_preview()
    candidates = build_hk_us_dirty_to_clean_candidate_preview()
    backfill = build_hk_us_store_backfill_preview()
    coverage = build_packet_coverage_refresh_preview()
    ticker_reports = build_hk_us_ticker_reports()
    board = build_hk_us_expansion_board()
    brief = build_hk_us_expansion_brief()
    backlog = build_backlog_update()
    guard = build_cannot_conclude_guard()
    gate = build_quality_gate()
    dashboard = build_dashboard()

    a = audit['phase203_additive_source_audit']
    l = leads['phase203_hk_us_source_leads']
    bf = backfill['phase203_hk_us_store_backfill_preview']
    cv = coverage['phase203_packet_coverage_refresh_preview']
    g = guard['phase203_cannot_conclude_guard']
    q = gate['phase203_quality_gate']

    summary = {
        'phase203_hk_us_evidence_chain_expansion': {
            'mode': mode,
            'target_ticker_count': 4,
            'hk_ticker_count': 2, 'us_ticker_count': 2,
            'additive_source_audit_generated': a['audit_generated'],
            'ifind_replacement_detected': a['ifind_replacement_detected'],
            'existing_sources_preserved': a['existing_sources_preserved'],
            'existing_adapters_preserved': a['existing_adapters_preserved'],
            'route_count': routes['phase203_hk_us_route_plan']['route_count'],
            'fetch_attempt_count': l['fetch_attempt_count'],
            'fetched_count': l['fetched_count'],
            'skipped_by_policy_count': l['skipped_by_policy_count'],
            'failed_non_blocking_count': l['failed_non_blocking_count'],
            'source_lead_count': l['source_lead_count'],
            'dirty_item_count': dirty['phase203_hk_us_dirty_items']['dirty_item_count'],
            'source_pair_candidate_count': pairs['phase203_hk_us_source_pair_candidates']['source_pair_candidate_count'],
            'verification_preview_count': verif['phase203_hk_us_verification_preview']['verification_preview_count'],
            'ready_for_phase204_real_verification_count': verif['phase203_hk_us_verification_preview']['ready_for_phase204_real_verification_count'],
            'dirty_to_clean_candidate_preview_count': candidates['phase203_hk_us_dirty_to_clean_candidate_preview']['dirty_to_clean_candidate_preview_count'],
            'store_backfill_preview_count': bf['store_backfill_preview_count'],
            'estimated_total_evidence_backfill': bf['estimated_total_evidence'],
            'packet_coverage_refresh_generated': cv['packet_coverage_refresh_generated'],
            'missing_ticker_count_after_backfill': cv['missing_ticker_count_after_backfill'],
            'ticker_reports_generated': ticker_reports['phase203_hk_us_ticker_reports']['ticker_reports_generated'],
            'board_generated': board['phase203_hk_us_expansion_board']['board_generated'],
            'brief_generated': brief['phase203_hk_us_expansion_brief']['brief_generated'],
            'backlog_generated': backlog['phase203_backlog_update']['backlog_generated'],
            'dashboard_generated': dashboard['phase203_dashboard']['dashboard_generated'],
            'guard_pass': g['guard_pass'],
            'violations': g['violations_count'],
            'quality_gate': q['gate_pass'],
            'formal_packet_updated': False,
            'research_packet_updated': False,
            'evidence_packet_updated': False,
            'clean_evidence_store_updated': False,
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
