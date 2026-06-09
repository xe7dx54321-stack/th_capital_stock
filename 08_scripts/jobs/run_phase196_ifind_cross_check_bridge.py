# Phase196 iFinD Cross-check Bridge for Web Scout Leads runner
"""Run iFinD cross-check bridge in dry-run / execute / skip-network modes."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
from smr_phase196_ifind_cross_check_bridge import (
    build_phase196_config, build_phase195_loader, build_phase188_loader,
    build_phase185_loader, build_bridge_domain_registry, build_bridge_matcher,
    build_source_independence_checker, build_source_diversity_checker,
    build_time_window_consistency, build_conflict_detector,
    build_verification_readiness_refresh, build_next_verification_task_queue,
    build_bridge_manifest, build_bridge_board, build_bridge_brief,
    build_backlog_update, build_cannot_conclude_guard, build_quality_gate,
    build_dashboard, MATCH_STRENGTHS
)

def run():
    dry_run = '--dry-run' in sys.argv
    skip_network = '--skip-network' in sys.argv
    execute = '--execute' in sys.argv
    allow_network = execute and not skip_network

    mode = 'execute' if execute else ('dry-run' if dry_run else 'skip-network')

    # Build all components
    config = build_phase196_config()
    p195_loader = build_phase195_loader()
    p188_loader = build_phase188_loader()
    p185_loader = build_phase185_loader()
    domain = build_bridge_domain_registry()
    matcher = build_bridge_matcher(allow_network)
    indep = build_source_independence_checker(allow_network)
    diver = build_source_diversity_checker(allow_network)
    time_win = build_time_window_consistency(allow_network)
    conflict = build_conflict_detector(allow_network)
    readiness = build_verification_readiness_refresh(allow_network)
    next_tasks = build_next_verification_task_queue(allow_network)
    manifest = build_bridge_manifest(allow_network)
    board = build_bridge_board(allow_network)
    brief = build_bridge_brief(allow_network)
    backlog = build_backlog_update(allow_network)
    guard = build_cannot_conclude_guard(allow_network)
    gate = build_quality_gate(allow_network)
    dashboard = build_dashboard(allow_network)

    m = matcher['phase196_bridge_matcher']
    manifest_data = manifest['phase196_bridge_manifest']
    g = guard['phase196_cannot_conclude_guard']
    q = gate['phase196_quality_gate']

    summary = {
        'phase196_ifind_cross_check_bridge': {
            'mode': mode,
            'ifind_dirty_item_count': p195_loader['phase196_phase195_loader']['dirty_item_count'],
            'web_source_item_count': p188_loader.get('phase196_phase188_loader', {}).get('converted_count', 0) if p188_loader.get('phase196_phase188_loader', {}).get('loaded') else 0,
            'cross_check_task_count': p185_loader.get('phase196_phase185_loader', {}).get('task_count', 0) if p185_loader.get('phase196_phase185_loader', {}).get('loaded') else 0,
            'bridge_match_count': m['match_count'],
            'strong': m['strong'],
            'moderate': m['moderate'],
            'weak': m['weak'],
            'not_matched': m['not_matched'],
            'not_applicable_market_scope': m['not_applicable_market_scope'],
            'independent_source_preview_count': indep['phase196_source_independence_checker']['independent_count'],
            'source_diversity_sufficient_count': diver['phase196_source_diversity_checker']['diverse_count'],
            'time_window_consistent_count': time_win['phase196_time_window_consistency']['consistent_count'],
            'conflict_detected_count': conflict['phase196_conflict_detector']['conflict_count'],
            'ready_for_real_verification': manifest_data['ready_for_real_verification'],
            'ready_for_classifier_preview': manifest_data['ready_for_classifier_preview'],
            'next_verification_task_count': next_tasks['phase196_next_verification_task_queue']['task_count'],
            'bridge_manifest_generated': manifest_data['manifest_generated'],
            'bridge_board_generated': board['phase196_bridge_board']['board_generated'],
            'bridge_brief_generated': brief['phase196_bridge_brief']['brief_generated'],
            'guard_pass': g['guard_pass'],
            'violations': g['violations_count'],
            'quality_gate': q['gate_pass'],
            'market_scope_cross_market': True,
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

    if '--json' in sys.argv:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(summary, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    run()
