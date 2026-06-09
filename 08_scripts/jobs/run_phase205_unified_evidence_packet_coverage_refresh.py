# Phase205 Unified Evidence runner
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
from smr_phase205_unified_evidence_packet_coverage_refresh import *

def run():
    dry_run = '--dry-run' in sys.argv
    skip_network = '--skip-network' in sys.argv
    execute = '--execute' in sys.argv
    mode = 'execute' if execute else ('dry-run' if dry_run else 'skip-network')

    config = build_phase205_config()
    p201 = build_phase201_loader()
    p204 = build_phase204_loader()
    unified = build_unified_evidence_loader()
    coverage = build_ticker_coverage_board()
    market = build_market_matrix()
    claim_map = build_evidence_to_claim_map_refresh()
    section = build_packet_section_preview_refresh()
    packet = build_evidence_packet_preview_refresh()
    readiness = build_packet_readiness_recalculation()
    gap = build_remaining_gap_closeout()
    reminder = build_manual_review_reminder()
    p394 = build_300394_source_limitation_report()
    audit = build_additive_source_audit_v3()
    apply_gate = build_formal_apply_gate_preview()
    apply_pkg = build_apply_package_preview()
    rollback = build_rollback_requirement_preview()
    checklist = build_post_apply_checklist_preview()
    board = build_unified_board()
    brief = build_unified_brief()
    backlog = build_backlog_update()
    guard = build_cannot_conclude_guard()
    gate = build_quality_gate()
    dashboard = build_dashboard()

    u = unified['phase205_unified_evidence_loader']
    r = readiness['phase205_packet_readiness_recalculation']
    g = gap['phase205_remaining_gap_closeout']
    a = audit['phase205_additive_source_audit_v3']
    ag = apply_gate['phase205_formal_apply_gate_preview']
    grd = guard['phase205_cannot_conclude_guard']
    q = gate['phase205_quality_gate']

    summary = {
        'phase205_unified_evidence_packet_coverage_refresh': {
            'mode': mode,
            'unified_evidence_record_count': u['total_evidence_records'],
            'direct_evidence_count': u['direct_evidence_count'],
            'context_evidence_count': u['context_evidence_count'],
            'duplicate_evidence_count': u['duplicate_evidence_count'],
            'ticker_count': coverage['phase205_ticker_coverage_board']['ticker_count'],
            'covered_count': coverage['phase205_ticker_coverage_board']['covered_count'],
            'blocked_count': coverage['phase205_ticker_coverage_board']['blocked_count'],
            'market_count': market['phase205_market_matrix']['market_count'],
            'claim_map_count': claim_map['phase205_evidence_to_claim_map_refresh']['claim_type_count'],
            'packet_section_preview_count': section['phase205_packet_section_preview_refresh']['total_sections'],
            'evidence_packet_preview_generated': packet['phase205_evidence_packet_preview_refresh']['packet_preview_generated'],
            'packet_readiness_generated': r['readiness_recalculated'],
            'packet_readiness_score': r['score'],
            'packet_readiness_label': r['label'],
            'remaining_gap_closeout_generated': g['gap_closeout_generated'],
            'remaining_gap': g['remaining_gap'],
            'manual_review_reminder_generated': reminder['phase205_manual_review_reminder']['reminder_generated'],
            '300394_source_limitation_report_generated': p394['phase205_300394_source_limitation_report']['report_generated'],
            '300394_cninfo_limitation_retained': p394['phase205_300394_source_limitation_report']['300394_cninfo_limitation_retained'],
            '300394_not_cninfo_resolved': g['300394_not_cninfo_resolved'],
            'additive_source_audit_generated': a['audit_generated'],
            'ifind_replacement_detected': a['ifind_replacement_detected'],
            'existing_sources_preserved': a['existing_sources_preserved'],
            'existing_adapters_preserved': a['existing_adapters_preserved'],
            'formal_apply_gate_generated': ag['gate_preview_generated'],
            'can_apply_preview': ag['can_apply_preview'],
            'formal_apply_allowed': ag['formal_apply_allowed'],
            'formal_apply_executed': ag['formal_apply_executed'],
            'apply_package_preview_generated': apply_pkg['phase205_apply_package_preview']['apply_package_generated'],
            'rollback_preview_generated': rollback['phase205_rollback_requirement_preview']['rollback_preview_generated'],
            'post_apply_checklist_generated': checklist['phase205_post_apply_checklist_preview']['checklist_generated'],
            'board_generated': board['phase205_unified_board']['board_generated'],
            'brief_generated': brief['phase205_unified_brief']['brief_generated'],
            'backlog_generated': backlog['phase205_backlog_update']['backlog_generated'],
            'dashboard_generated': dashboard['phase205_dashboard']['dashboard_generated'],
            'guard_pass': grd['guard_pass'],
            'violations': grd['violations_count'],
            'quality_gate': q['gate_pass'],
            'research_packet_updated': False,
            'evidence_packet_updated': False,
            'daily_brief_updated': False,
            'weekly_review_updated': False,
            'watch_core_updated': False,
            'daily_monitoring_state_updated': False,
            'thesis_state_updated': False,
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
