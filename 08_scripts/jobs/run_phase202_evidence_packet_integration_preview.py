# Phase202 Evidence-to-Packet Integration Preview runner
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
from smr_phase202_evidence_packet_integration_preview import *

def run():
    dry_run = '--dry-run' in sys.argv
    skip_network = '--skip-network' in sys.argv
    execute = '--execute' in sys.argv
    mode = 'execute' if execute else ('dry-run' if dry_run else 'skip-network')
    
    config = build_phase202_config()
    loader = build_phase201_loader()
    ticker_summaries = build_ticker_evidence_summaries()
    claim_map = build_evidence_to_claim_map()
    policy = build_direct_context_policy()
    section_preview = build_packet_section_preview()
    packet_preview = build_evidence_packet_preview()
    readiness = build_packet_readiness_score()
    missing = build_missing_evidence_report()
    reminder = build_conflict_manual_review_reminder()
    p394 = build_300394_packet_preview()
    apply_gate = build_packet_apply_readiness_gate()
    manifest = build_packet_integration_manifest()
    board = build_packet_integration_board()
    brief = build_packet_integration_brief()
    backlog = build_backlog_update()
    guard = build_cannot_conclude_guard()
    gate = build_quality_gate()
    dashboard = build_dashboard()
    
    l = loader['phase202_phase201_loader']
    ts = ticker_summaries['phase202_ticker_evidence_summaries']
    cm = claim_map['phase202_evidence_to_claim_map']
    rd = readiness['phase202_packet_readiness_score']
    ms = missing['phase202_missing_evidence_report']
    rm = reminder['phase202_conflict_manual_review_reminder']
    ag = apply_gate['phase202_packet_apply_readiness_gate']
    g = guard['phase202_cannot_conclude_guard']
    q = gate['phase202_quality_gate']
    pp = packet_preview['phase202_evidence_packet_preview']
    mf = manifest['phase202_packet_integration_manifest']
    
    summary = {
        'phase202_evidence_to_packet_integration_preview': {
            'mode': mode,
            'clean_evidence_record_count': l['clean_evidence_record_count'],
            'direct_evidence_count': l['direct_evidence_count'],
            'context_evidence_count': l['context_evidence_count'],
            'ticker_summary_count': ts['ticker_count'],
            'claim_map_count': cm['claim_types_count'],
            'packet_section_preview_count': section_preview['phase202_packet_section_preview']['total_sections'],
            'evidence_packet_preview_generated': pp['packet_preview_generated'],
            'packet_readiness_score': rd['score'],
            'packet_readiness_label': rd['readiness_label'],
            'missing_evidence_report_generated': ms['report_generated'],
            'missing_ticker_count': ms['missing_count'],
            'conflict_manual_review_reminder_generated': rm['reminder_generated'],
            'manual_review_queue_retained_count': rm['manual_review_queue_retained_count'],
            'conflict_needs_manual_review_count': rm['conflict_needs_manual_review_count'],
            'needs_more_review_count': rm['needs_more_review_count'],
            '300394_packet_preview_generated': p394['phase202_300394_packet_preview']['300394_packet_preview_generated'],
            '300394_cninfo_limitation_retained': p394['phase202_300394_packet_preview']['300394_cninfo_limitation_retained'],
            'packet_apply_readiness_gate_generated': ag['gate_generated'],
            'can_apply_formal_packet': ag['can_apply_formal_packet'],
            'packet_integration_manifest_generated': mf['manifest_generated'],
            'packet_integration_board_generated': board['phase202_packet_integration_board']['board_generated'],
            'packet_integration_brief_generated': brief['phase202_packet_integration_brief']['brief_generated'],
            'backlog_generated': backlog['phase202_backlog_update']['backlog_generated'],
            'dashboard_generated': dashboard['phase202_dashboard']['dashboard_generated'],
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
            'context_as_direct_count': 0,
            'conflict_as_evidence_count': rm['conflict_as_evidence_count'],
            'needs_review_as_evidence_count': rm['needs_review_as_evidence_count'],
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
