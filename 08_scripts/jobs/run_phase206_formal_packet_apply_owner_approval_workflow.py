# Phase206 runner
import json,os,sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__),'..','lib'))
from smr_phase206_formal_packet_apply_owner_approval_workflow import *
def run():
    dry='--dry-run' in sys.argv; sk='--skip-network' in sys.argv; ex='--execute' in sys.argv
    oi='--owner-decision-input' in sys.argv
    mode='owner-decision-input' if (ex and oi) else ('execute' if ex else ('dry-run' if dry else 'skip-network'))
    config=build_phase206_config();p205=build_phase205_loader()
    template=build_owner_approval_template();schema=build_owner_decision_schema()
    decision=build_owner_decision_input(ex and oi)
    w394=build_300394_limitation_decision_workflow();mr=build_manual_review_decision_workflow()
    scope=build_apply_scope_preview();partial=build_partial_apply_preview()
    blocker=build_blocker_closeout();pkg=build_formal_apply_execution_package_preview()
    rollback=build_rollback_readiness();verify=build_post_apply_verification_readiness()
    checklist=build_final_pre_apply_checklist();manifest=build_owner_confirmation_manifest()
    audit=build_audit_trail();auditv4=build_additive_source_audit_v4()
    board=build_approval_board();brief=build_approval_brief();backlog=build_backlog_update()
    guard=build_cannot_conclude_guard();gate=build_quality_gate();dashboard=build_dashboard()
    d=decision['phase206_owner_decision_input'];a=auditv4['phase206_additive_source_audit_v4']
    g=guard['phase206_cannot_conclude_guard'];q=gate['phase206_quality_gate']
    s={'phase206_formal_packet_apply_owner_approval_workflow':{'mode':mode,
        'owner_template_generated':template['phase206_owner_approval_template']['template_generated'],
        'owner_decision_schema_generated':True,
        'owner_decision_input_loaded':d['input_loaded'],
        'owner_decision_valid':d['decision_valid'],
        'owner_decision_quarantine':d['decision_quarantine'],
        'decision_type':d['decision_type'],'decision_scope':d['decision_scope'],
        'owner_confirmation':d['owner_confirmation'],
        '300394_workflow_generated':w394['phase206_300394_limitation_decision_workflow']['workflow_generated'],
        '300394_cninfo_retained':w394['phase206_300394_limitation_decision_workflow']['300394_cninfo_limitation_retained'],
        '300394_cninfo_resolved':w394['phase206_300394_limitation_decision_workflow']['300394_cninfo_resolved'],
        'manual_review_workflow_generated':mr['phase206_manual_review_decision_workflow']['workflow_generated'],
        'apply_scope_preview_generated':scope['phase206_apply_scope_preview']['scope_preview_generated'],
        'partial_apply_preview_generated':partial['phase206_partial_apply_preview']['partial_apply_preview_generated'],
        'blocker_closeout_generated':blocker['phase206_blocker_closeout']['closeout_generated'],
        'execution_package_preview_generated':pkg['phase206_formal_apply_execution_package_preview']['execution_package_preview_generated'],
        'rollback_readiness_generated':rollback['phase206_rollback_readiness']['rollback_ready'],
        'post_apply_verification_generated':verify['phase206_post_apply_verification_readiness']['verification_readiness_generated'],
        'pre_apply_checklist_generated':checklist['phase206_final_pre_apply_checklist']['checklist_generated'],
        'owner_confirmation_manifest_generated':manifest['phase206_owner_confirmation_manifest']['manifest_generated'],
        'audit_trail_generated':audit['phase206_audit_trail']['audit_trail_generated'],
        'additive_source_audit_generated':a['audit_generated'],
        'ifind_replacement_detected':a['ifind_replacement_detected'],
        'existing_sources_preserved':a['existing_sources_preserved'],
        'existing_adapters_preserved':a['existing_adapters_preserved'],
        'formal_apply_next_phase_allowed':False,
        'ready_for_phase207_formal_apply_execution':False,
        'formal_apply_executed':False,
        'research_packet_updated':False,'evidence_packet_updated':False,
        'board_generated':board['phase206_approval_board']['board_generated'],
        'brief_generated':brief['phase206_approval_brief']['brief_generated'],
        'backlog_generated':backlog['phase206_backlog_update']['backlog_generated'],
        'dashboard_generated':dashboard['phase206_dashboard']['dashboard_generated'],
        'guard_pass':g['guard_pass'],'violations':g['violations_count'],
        'quality_gate':q['gate_pass'],
        'daily_brief_updated':False,'weekly_review_updated':False,
        'watch_core_updated':False,'daily_monitoring_state_updated':False,'thesis_state_updated':False,
        'ifind_api_called':False,'web_fetch_called':False,
        'raw_response_saved':False,'raw_full_text_saved':False,
        'trade_recommendation_created':0,'target_price_created':0,'position_sizing_created':0,
        'broker_api_called':False,'llm_api_called':False,'mock_used':False,'fixture_used':False}}
    print(json.dumps(s,indent=2,ensure_ascii=False))
if __name__=='__main__':run()
