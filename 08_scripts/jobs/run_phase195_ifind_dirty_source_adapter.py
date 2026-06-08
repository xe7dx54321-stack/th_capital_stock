# Phase195 iFinD Dirty Source Adapter runner
"""Run iFinD dirty source adapter in dry-run / execute / skip-network modes."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
from smr_phase195_ifind_dirty_source_adapter import (
    build_phase195_config, build_domain_registry, build_cn_a_dirty_source_universe,
    build_news_query_plan, build_announcement_query_plan, build_event_query_plan,
    build_wencai_query_plan, build_source_metadata_schema, build_source_lead_observation_schema,
    build_copyright_policy, build_source_category_classifier, build_source_reliability_pre_score,
    build_ingestion_preview, build_metadata_validation, build_copyright_validator,
    build_dedup_manifest, build_cross_check_route_preview, build_web_scout_bridge_preview,
    build_ingestion_manifest, build_dirty_source_board, build_dirty_source_brief,
    build_backlog_update, build_cannot_conclude_guard, build_quality_gate, build_dashboard,
    CN_A_TICKERS, DIRTY_LANES
)

def run():
    dry_run = '--dry-run' in sys.argv
    skip_network = '--skip-network' in sys.argv
    execute = '--execute' in sys.argv
    allow_network = execute and not skip_network

    mode = 'execute' if execute else ('dry-run' if dry_run else 'skip-network')

    # Build all components
    cfg = build_phase195_config()
    domain = build_domain_registry()
    universe = build_cn_a_dirty_source_universe()
    news_plan = build_news_query_plan(allow_network)
    ann_plan = build_announcement_query_plan(allow_network)
    evt_plan = build_event_query_plan(allow_network)
    wc_plan = build_wencai_query_plan(allow_network)
    meta_schema = build_source_metadata_schema()
    obs_schema = build_source_lead_observation_schema()
    copy_policy = build_copyright_policy()
    classifier = build_source_category_classifier()
    reliability = build_source_reliability_pre_score()
    preview = build_ingestion_preview(allow_network)
    meta_valid = build_metadata_validation(allow_network)
    copy_valid = build_copyright_validator(allow_network)
    dedup = build_dedup_manifest(allow_network)
    cross_check = build_cross_check_route_preview(allow_network)
    web_scout = build_web_scout_bridge_preview(allow_network)
    manifest = build_ingestion_manifest(allow_network)
    board = build_dirty_source_board(allow_network)
    brief = build_dirty_source_brief(allow_network)
    backlog = build_backlog_update(allow_network)
    guard = build_cannot_conclude_guard(allow_network)
    gate = build_quality_gate(allow_network)
    dashboard = build_dashboard(allow_network)

    p = preview['phase195_ingestion_preview']
    m = manifest['phase195_ingestion_manifest']
    g = guard['phase195_cannot_conclude_guard']
    q = gate['phase195_quality_gate']
    b = board['phase195_dirty_source_board']

    summary = {
        'phase195_ifind_dirty_source_adapter': {
            'mode': mode,
            'tickers_total': len(CN_A_TICKERS),
            'dirty_source_enabled': 4,
            'blocked': 1,
            'lanes': DIRTY_LANES,
            'dirty_items_total': p['dirty_item_count'],
            'ingested': m['ingested'],
            'quarantined': m['quarantined'],
            'ready_for_triage': m['ready_for_triage'],
            'needs_cross_check': m['needs_cross_check'],
            'board_sections': b['section_summary'],
            'guard_pass': g['guard_pass'],
            'violations': g['violations_count'],
            'quality_gate': q['gate_pass'],
            '300394_blocker_retained': b['300394_blocker_retained'],
            'network_called': allow_network,
            'mock_used': False,
            'fixture_used': False,
            'raw_response_saved': False,
            'raw_full_text_saved': False,
            'clean_evidence_created': False,
            'packet_updated': False,
            'daily_brief_updated': False,
            'watch_core_updated': False,
            'trade_recommendation_created': False,
            'target_price_created': False,
            'position_sizing_created': False,
            'broker_api_called': False,
            'llm_api_called': False
        }
    }

    if '--json' in sys.argv:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(summary, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    run()
