# Phase197 CN_A Web Scout Expansion runner
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
from smr_phase197_cn_a_web_scout_expansion import (
    build_phase197_config, build_domain_registry, build_source_universe,
    build_official_source_routes, build_company_ir_routes,
    build_investor_interaction_routes, build_financial_news_routes,
    build_query_plan, build_safe_network_policy, build_fetch_status,
    build_source_lead_observations, build_source_category_classifier,
    build_source_reliability_pre_score, build_dedup, build_dirty_inbox_converter,
    build_ingestion_manifest, build_same_market_alignment_preview,
    build_phase196_rerun_readiness, build_next_verification_task_seed,
    build_blocked_source_handler, build_scout_board, build_scout_brief,
    build_backlog_update, build_cannot_conclude_guard, build_quality_gate,
    build_dashboard, CN_A_SCOUT_TICKERS, CN_A_SOURCE_CATEGORIES
)

def run():
    dry_run = '--dry-run' in sys.argv
    skip_network = '--skip-network' in sys.argv
    execute = '--execute' in sys.argv
    allow_network = execute and not skip_network
    mode = 'execute' if execute else ('dry-run' if dry_run else 'skip-network')

    # Build all
    config = build_phase197_config()
    domain = build_domain_registry()
    universe = build_source_universe()
    official = build_official_source_routes()
    ir_routes = build_company_ir_routes()
    inv_routes = build_investor_interaction_routes()
    news_routes = build_financial_news_routes()
    query = build_query_plan(allow_network)
    policy = build_safe_network_policy()
    fetch = build_fetch_status(allow_network)
    leads = build_source_lead_observations(allow_network)
    classifier = build_source_category_classifier()
    reliability = build_source_reliability_pre_score()
    dedup = build_dedup(allow_network)
    converted = build_dirty_inbox_converter(allow_network)
    manifest = build_ingestion_manifest(allow_network)
    alignment = build_same_market_alignment_preview(allow_network)
    rerun = build_phase196_rerun_readiness(allow_network)
    next_tasks = build_next_verification_task_seed(allow_network)
    blocked = build_blocked_source_handler(allow_network)
    board = build_scout_board(allow_network)
    brief = build_scout_brief(allow_network)
    backlog = build_backlog_update(allow_network)
    guard = build_cannot_conclude_guard(allow_network)
    gate = build_quality_gate(allow_network)
    dashboard = build_dashboard(allow_network)

    m = manifest['phase197_ingestion_manifest']
    a = alignment['phase197_same_market_alignment_preview']
    f = fetch['phase197_fetch_status']
    g = guard['phase197_cannot_conclude_guard']
    q = gate['phase197_quality_gate']

    summary = {
        'phase197_cn_a_web_scout_expansion': {
            'mode': mode,
            'tickers_total': len(CN_A_SCOUT_TICKERS),
            'query_count': query['phase197_query_plan']['query_count'],
            'fetch_attempt_count': f['fetch_attempts'],
            'fetched_count': f['status_summary'].get('fetched', 0),
            'skipped_by_policy_count': f['status_summary'].get('skipped_by_policy', 0),
            'failed_non_blocking_count': f['status_summary'].get('rate_limited', 0),
            'source_lead_observation_count': leads['phase197_source_leads']['lead_count'],
            'converted_dirty_item_count': converted['phase197_converted_items']['converted_count'],
            'duplicate_count': dedup['phase197_dedup']['duplicates_found'],
            'quarantine_count': dedup['phase197_dedup']['duplicates_found'],
            'ingested_dirty_item_count': m['ingested'],
            'official_disclosure_source_count': len(board['phase197_scout_board']['sections'].get('official_disclosure', [])),
            'company_ir_source_count': len(board['phase197_scout_board']['sections'].get('company_ir', [])),
            'investor_interaction_source_count': len(board['phase197_scout_board']['sections'].get('investor_interaction', [])),
            'financial_news_source_count': len(board['phase197_scout_board']['sections'].get('financial_news', [])),
            'industry_media_source_count': len(board['phase197_scout_board']['sections'].get('industry_media', [])),
            'same_market_alignment_count': a['alignment_count'],
            'strong_alignment': a['strong'],
            'moderate_alignment': a['moderate'],
            'weak_alignment': a['weak'],
            'would_help_cross_check_count': a['would_help_cross_check_count'],
            'phase196_rerun_recommended': rerun['phase197_phase196_rerun_readiness']['rerun_recommended'],
            'ready_for_bridge_rerun_count': rerun['phase197_phase196_rerun_readiness']['ready_for_bridge_rerun_count'],
            'next_verification_task_seed_count': next_tasks['phase197_next_verification_task_seed']['task_count'],
            'scout_manifest_generated': m['manifest_generated'],
            'scout_board_generated': board['phase197_scout_board']['board_generated'],
            'scout_brief_generated': brief['phase197_scout_brief']['brief_generated'],
            'guard_pass': g['guard_pass'],
            'violations': g['violations_count'],
            'quality_gate': q['gate_pass'],
            '300394_cninfo_blocker_retained': True,
            'real_verification_executed': False,
            'classifier_executed': False,
            'clean_evidence_created': False,
            'packet_updated': False,
            'daily_brief_updated': False,
            'watch_core_updated': False,
            'trade_recommendation_created': False,
            'target_price_created': False,
            'position_sizing_created': False,
            'broker_api_called': False,
            'llm_api_called': False,
            'mock_used': False,
            'fixture_used': False
        }
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    run()
