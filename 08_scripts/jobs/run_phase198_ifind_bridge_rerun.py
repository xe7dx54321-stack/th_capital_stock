# Phase198 iFinD Bridge Rerun runner
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
from smr_phase198_ifind_bridge_rerun import (
    build_phase198_config, build_phase195_loader, build_phase197_loader,
    build_phase196_rules_loader, build_alignment_denoise, build_bridge_matcher,
    build_source_independence_checker, build_source_diversity_checker,
    build_time_window_consistency, build_topic_similarity,
    build_reliability_compatibility, build_conflict_preview,
    build_verification_readiness, build_verification_task_queue,
    build_300394_bridge_readiness, build_bridge_manifest, build_bridge_board,
    build_bridge_brief, build_backlog_update, build_cannot_conclude_guard,
    build_quality_gate, build_dashboard
)

def run():
    dry_run = '--dry-run' in sys.argv
    skip_network = '--skip-network' in sys.argv
    execute = '--execute' in sys.argv
    an = execute and not skip_network
    mode = 'execute' if execute else ('dry-run' if dry_run else 'skip-network')

    config = build_phase198_config()
    p195 = build_phase195_loader()
    p197 = build_phase197_loader()
    p196 = build_phase196_rules_loader()
    denoise = build_alignment_denoise()
    matcher = build_bridge_matcher(an)
    indep = build_source_independence_checker(an)
    diver = build_source_diversity_checker(an)
    time_w = build_time_window_consistency(an)
    topic = build_topic_similarity(an)
    reliab = build_reliability_compatibility(an)
    conflict = build_conflict_preview(an)
    readiness = build_verification_readiness(an)
    tasks = build_verification_task_queue(an)
    p394 = build_300394_bridge_readiness(an)
    manifest = build_bridge_manifest(an)
    board = build_bridge_board(an)
    brief = build_bridge_brief(an)
    backlog = build_backlog_update(an)
    guard = build_cannot_conclude_guard(an)
    gate = build_quality_gate(an)
    dashboard = build_dashboard(an)

    m = matcher['phase198_bridge_matcher']
    d = denoise['phase198_alignment_denoise']
    r = readiness['phase198_verification_readiness']
    g = guard['phase198_cannot_conclude_guard']
    q = gate['phase198_quality_gate']

    summary = {
        'phase198_ifind_bridge_rerun': {
            'mode': mode,
            'ifind_dirty_item_count': p195['phase198_phase195_loader']['dirty_item_count'],
            'cn_a_web_scout_item_count': p197.get('phase198_phase197_loader', {}).get('lead_count', 0),
            'input_alignment_count': d['input_alignments'],
            'alignment_candidate_count': d['candidate_count'],
            'alignment_rejected_count': d['rejected_count'],
            'bridge_match_count': m['match_count'],
            'strong': m['strong'],
            'moderate': m['moderate'],
            'weak': m['weak'],
            'rejected': m['rejected'],
            'independent_source_preview_count': indep['phase198_source_independence']['independent_count'],
            'source_diversity_sufficient_count': diver['phase198_source_diversity']['diverse_count'],
            'time_window_consistent_count': time_w['phase198_time_window_consistency']['consistent_count'],
            'conflict_detected_count': conflict['phase198_conflict_preview']['conflict_count'],
            'ready_for_real_verification': r['ready_for_real_verification'],
            'ready_for_classifier_preview': r['ready_for_classifier_preview'],
            'next_verification_task_count': tasks['phase198_verification_task_queue']['task_count'],
            '300394_bridge_readiness_generated': True,
            '300394_cninfo_limitation_retained': True,
            'bridge_manifest_generated': manifest['phase198_bridge_manifest']['manifest_generated'],
            'bridge_board_generated': board['phase198_bridge_board']['board_generated'],
            'bridge_brief_generated': brief['phase198_bridge_brief']['brief_generated'],
            'guard_pass': g['guard_pass'],
            'violations': g['violations_count'],
            'quality_gate': q['gate_pass'],
            'ifind_api_called': False,
            'web_fetch_called': False,
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
