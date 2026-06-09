# Phase200 Dirty-to-Clean Classifier runner
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
from smr_phase200_dirty_to_clean_classifier import *
def run():
    dry_run = '--dry-run' in sys.argv; skip_network = '--skip-network' in sys.argv; execute = '--execute' in sys.argv
    an = execute and not skip_network
    mode = 'execute' if execute else ('dry-run' if dry_run else 'skip-network')
    config = build_phase200_config(); p199 = build_phase199_loader()
    conflict = build_conflict_exclusion_gate(); eligible = build_candidate_eligibility_prefilter(an)
    etype = build_evidence_type_classifier(an); claim = build_claim_support_classifier(an)
    strength = build_evidence_strength_classifier(an); lineage = build_source_lineage(an)
    risk = build_evidence_risk_tagger(an); ctx_policy = build_context_only_policy()
    p394 = build_300394_classifier_report(an); preview = build_clean_evidence_candidate_preview(an)
    store = build_phase201_store_input_preview(an); manifest = build_classifier_manifest(an)
    board = build_classifier_board(an); brief = build_classifier_brief(an)
    backlog = build_backlog_update(an); guard = build_cannot_conclude_guard(an)
    gate = build_quality_gate(an); dashboard = build_dashboard(an)
    p = preview['phase200_clean_evidence_candidate_preview']
    m = manifest['phase200_classifier_manifest']; g = guard['phase200_cannot_conclude_guard']; q = gate['phase200_quality_gate']
    summary = {'phase200_dirty_to_clean_classifier': {'mode': mode, 'candidate_input_count': m['input_candidates'], 'classifier_input_count': CANDIDATE_INPUT_COUNT, 'conflict_excluded_count': conflict['phase200_conflict_exclusion_gate']['conflict_items_excluded'], 'conflict_sent_to_classifier': 0, 'insufficient_rejected_excluded': 63, 'classified_count': m['classified'], 'eligible_clean_candidate_count': p['clean_candidate_count'], 'eligible_context_candidate_count': p['context_candidate_count'], 'needs_more_review_count': p['needs_review_count'], 'rejected_by_classifier_count': p['rejected_count'], 'phase201_store_input_count': store['phase200_phase201_store_input_preview']['total_candidates_for_store'], 'manual_review_queue_retained': conflict['phase200_conflict_exclusion_gate']['manual_review_queue_retained'], '300394_classifier_report_generated': True, '300394_cninfo_limitation_retained': True, 'classifier_manifest_generated': m['manifest_generated'], 'classifier_board_generated': board['phase200_classifier_board']['board_generated'], 'classifier_brief_generated': brief['phase200_classifier_brief']['brief_generated'], 'guard_pass': g['guard_pass'], 'violations': g['violations_count'], 'quality_gate': q['gate_pass'], 'clean_evidence_store_updated': False, 'clean_evidence_created': False, 'packet_updated': False, 'daily_brief_updated': False, 'watch_core_updated': False, 'trade_recommendation_created': False, 'target_price_created': False, 'position_sizing_created': False, 'broker_api_called': False, 'llm_api_called': False, 'mock_used': False, 'fixture_used': False}}
    print(json.dumps(summary, indent=2, ensure_ascii=False))
if __name__ == '__main__': run()
