# Phase207 runner
import json,os,sys
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..','lib'))
from smr_phase207_formal_packet_apply_execution import *
def run():
    dry='--dry-run' in sys.argv;sk='--skip-network' in sys.argv;ex='--execute' in sys.argv
    ac='--apply-confirmed' in sys.argv;wp='--write-formal-packet' in sys.argv;oi='--owner-input' in sys.argv
    if ex and ac and wp:mode='apply-confirmed'
    elif ex and oi:mode='owner-input'
    elif ex:mode='execute'
    elif sk:mode='skip-network'
    else:mode='dry-run'
    config=build_phase207_config();p206=build_phase206_loader();p205=build_phase205_loader()
    dr=build_owner_decision_revalidation();snap=build_pre_apply_snapshot(ac and wp)
    gate=build_formal_apply_gate(ac);writer=build_formal_packet_writer(ac,wp)
    rollback=build_rollback_package(ac,wp);pav=build_post_apply_verification(ac,wp)
    integ=build_packet_integrity_check(ac,wp);evr=build_evidence_reference_validation()
    dc=build_direct_context_separation_check();ntv=build_no_trade_validator()
    audit=build_apply_audit_trail(ac,wp);auditv5=build_additive_source_audit_v5()
    board=build_formal_apply_board(ac,wp);brief=build_formal_apply_brief(ac,wp)
    backlog=build_backlog_update(ac,wp);guard=build_cannot_conclude_guard()
    gate_q=build_quality_gate(ac,wp);dashboard=build_dashboard(ac,wp)
    d=dr['phase207_owner_decision_revalidation'];g=gate['phase207_formal_apply_gate']
    w=writer['phase207_formal_packet_writer'];grd=guard['phase207_cannot_conclude_guard'];q=gate_q['phase207_quality_gate']
    n=ntv['phase207_no_trade_validator'];s=dc['phase207_direct_context_separation_check']
    s={'phase207_formal_packet_apply_execution':{'mode':mode,
        'owner_decision_loaded':d['owner_decision_loaded'],
        'owner_decision_revalidated':d['owner_decision_revalidated'],
        'owner_decision_valid':d['owner_decision_valid'],
        'decision_type':d['decision_type'],
        'owner_confirmation_filled':d['owner_confirmation_filled'],
        'can_execute_formal_apply':g['can_execute_formal_apply'],
        'formal_apply_executed':w['packet_written'],
        'research_packet_written':w['research_packet_written'],
        'evidence_packet_written':w['evidence_packet_written'],
        'limitation_appendix_written':w['limitation_appendix_written'],
        'included_ticker_count':w['included_ticker_count'],
        'excluded_ticker_count':w['excluded_ticker_count'],
        'excluded_tickers':w['excluded_tickers'],
        '300394_excluded':w.get('300394_excluded',True),
        '300394_cninfo_limitation_retained':w.get('300394_cninfo_limitation_retained',True),
        '300394_cninfo_resolved':w.get('300394_cninfo_resolved',False),
        'pre_apply_snapshot_generated':snap['phase207_pre_apply_snapshot']['snapshot_generated'],
        'rollback_package_generated':rollback['phase207_rollback_package']['rollback_package_written'],
        'rollback_available':rollback['phase207_rollback_package']['rollback_available'],
        'post_apply_verification_pass':pav['phase207_post_apply_verification']['all_checks_pass'],
        'packet_integrity_pass':integ['phase207_packet_integrity_check']['integrity_pass'],
        'evidence_reference_validation_pass':evr['phase207_evidence_reference_validation']['validation_pass'],
        'direct_context_separation_pass':dc['phase207_direct_context_separation_check']['separation_pass'],
        'context_as_direct_count':s['context_as_direct_count'],
        'conflict_as_evidence_count':s['conflict_as_evidence_count'],
        'needs_review_as_evidence_count':s['needs_review_as_evidence_count'],
        'no_trade_validation_pass':ntv['phase207_no_trade_validator']['validation_pass'],
        'buy_count':n['buy_count'],'sell_count':n['sell_count'],'hold_count':n['hold_count'],
        'target_price_count':n['target_price_count'],'position_sizing_count':n['position_sizing_count'],
        'additive_source_audit_generated':auditv5['phase207_additive_source_audit_v5']['audit_generated'],
        'ifind_replacement_detected':auditv5['phase207_additive_source_audit_v5']['ifind_replacement_detected'],
        'existing_sources_preserved':auditv5['phase207_additive_source_audit_v5']['existing_sources_preserved'],
        'existing_adapters_preserved':auditv5['phase207_additive_source_audit_v5']['existing_adapters_preserved'],
        'watch_core_updated':False,'daily_brief_updated':False,'weekly_review_updated':False,
        'daily_monitoring_state_updated':False,'thesis_state_updated':False,
        'board_generated':board['phase207_formal_apply_board']['board_generated'],
        'brief_generated':brief['phase207_formal_apply_brief']['brief_generated'],
        'backlog_generated':backlog['phase207_backlog_update']['backlog_generated'],
        'dashboard_generated':dashboard['phase207_dashboard']['dashboard_generated'],
        'guard_pass':grd['guard_pass'],'violations':grd['violations_count'],'quality_gate':q['gate_pass'],
        'ifind_api_called':False,'web_fetch_called':False,'raw_response_saved':False,'raw_full_text_saved':False,
        'broker_api_called':False,'llm_api_called':False,'mock_used':False,'fixture_used':False}}
    print(json.dumps(s,indent=2,ensure_ascii=False))
if __name__=='__main__':run()
