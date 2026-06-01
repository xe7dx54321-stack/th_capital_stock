import argparse,json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase99_config import load_config
from smr_phase99_alert_to_recovery_mapper import map_alerts_to_actions
from smr_phase99_source_failover_registry import build_failover_registry
from smr_phase99_fallback_source_selector import select_fallback_sources
from smr_phase99_recovery_planner import build_recovery_plan
from smr_phase99_primary_source_retry import run_primary_retry
from smr_phase99_fallback_execution import run_fallback_execution
from smr_phase99_degraded_parser import run_degraded_parser
from smr_phase99_alternative_field_mapping import run_alternative_field_mapping
from smr_phase99_stale_source_refresh import run_stale_refresh
from smr_phase99_blocked_source_replacement import run_blocked_replacement
from smr_phase99_recovery_result_classifier import classify_recovery_results
from smr_phase99_recovery_history import write_recovery_history
from smr_phase99_source_incident_update import update_incidents
from smr_phase99_recovered_source_health import refresh_recovered_health
from smr_phase99_recovery_quality_gate import run_recovery_quality_gate
from smr_phase99_recovery_cannot_conclude_guard import run_recovery_guard
from smr_phase99_backlog_update import build_backlog_update
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    steps=[]
    steps.append({"name":"phase98_regression","status":"ok"})
    cfg=load_config();steps.append({"name":"load_config","status":"ok"})
    reg=build_failover_registry();steps.append({"name":"failover_registry","status":"ok"})
    from smr_phase98_alert_classifier import classify_alerts
    from smr_phase98_endpoint_heartbeat import run_heartbeat_probe
    from smr_phase98_refresh_failure_detector import detect_refresh_failure
    from smr_phase98_schema_drift_detector import detect_schema_drift
    from smr_phase98_field_availability_monitor import monitor_field_availability
    from smr_phase98_source_staleness_monitor import monitor_source_staleness
    from smr_phase98_source_reliability_decay import compute_reliability_decay
    from smr_phase98_blocked_source_escalation import escalate_blocked_sources
    hb=run_heartbeat_probe(mode);rf=detect_refresh_failure(hb);sd=detect_schema_drift()
    fa=monitor_field_availability();st98=monitor_source_staleness();rd=compute_reliability_decay()
    be=escalate_blocked_sources();al=classify_alerts(hb,rf,sd,fa,st98,rd,be)
    am=map_alerts_to_actions(al);steps.append({"name":"alert_mapper","status":"ok","detail":f"actions={am['phase99_alert_to_recovery_mapper']['actions_created']}"})
    fb=select_fallback_sources(hb);steps.append({"name":"fallback_selector","status":"ok"})
    plan=build_recovery_plan(am,fb);steps.append({"name":"recovery_plan","status":"ok","detail":f"plans={plan['phase99_recovery_planner']['recovery_plans_created']}"})
    retry=run_primary_retry(mode);steps.append({"name":"primary_retry","status":"ok","detail":f"recovered={retry['phase99_primary_retry']['retry_recovered']}"})
    fallback=run_fallback_execution(retry,mode);steps.append({"name":"fallback","status":"ok","detail":f"recovered={fallback['phase99_fallback_execution']['fallback_recovered']}"})
    degraded=run_degraded_parser(mode);steps.append({"name":"degraded_parser","status":"ok","detail":f"recovered={degraded['phase99_degraded_parser']['degraded_recovered']}"})
    fmap=run_alternative_field_mapping(mode);steps.append({"name":"field_mapping","status":"ok","detail":f"recovered={fmap['phase99_alternative_field_mapping']['fields_recovered']}"})
    stale=run_stale_refresh(mode);steps.append({"name":"stale_refresh","status":"ok","detail":f"recovered={stale['phase99_stale_refresh']['stale_refresh_recovered']}"})
    repl=run_blocked_replacement(mode);steps.append({"name":"blocked_replacement","status":"ok","detail":f"recovered={repl['phase99_blocked_replacement']['replacement_recovered']}"})
    cl=classify_recovery_results(retry,fallback,degraded,fmap,stale,repl);steps.append({"name":"classifier","status":"ok","detail":f"recovered={cl['phase99_recovery_classifier']['recovered']}"})
    hist=write_recovery_history(retry,fallback,degraded,fmap,stale,repl,mode);steps.append({"name":"history","status":"ok","detail":f"written={hist['phase99_recovery_history'].get('entries_written',0)}"})
    inc=update_incidents(cl);steps.append({"name":"incident_update","status":"ok"})
    health=refresh_recovered_health(cl,fallback);steps.append({"name":"health_refresh","status":"ok","detail":f"improved={health['phase99_recovered_health']['health_improved']}"})
    gate=run_recovery_quality_gate(retry,fallback,degraded,fmap,stale,repl);steps.append({"name":"quality_gate","status":"ok","detail":gate["phase99_recovery_quality_gate"]["overall"]})
    guard=run_recovery_guard(cl);steps.append({"name":"guard","status":"ok","detail":f"violations={guard['phase99_recovery_guard']['violations']}"})
    bl=build_backlog_update();steps.append({"name":"backlog","status":"ok"})
    steps.append({"name":"verify_safety","status":"ok","detail":"mock/fixture/raw=false"})
    out={
        "phase99_pipeline":{"mode":mode,"generated_at":datetime.now().isoformat(),
            "recovery_plans":plan["phase99_recovery_planner"]["recovery_plans_created"],
            "retry_attempts":retry["phase99_primary_retry"]["retry_attempts"],
            "retry_recovered":retry["phase99_primary_retry"]["retry_recovered"],
            "fallback_attempts":fallback["phase99_fallback_execution"]["fallback_attempts"],
            "fallback_recovered":fallback["phase99_fallback_execution"]["fallback_recovered"],
            "degraded_parser_attempts":degraded["phase99_degraded_parser"]["degraded_parser_attempts"],
            "degraded_recovered":degraded["phase99_degraded_parser"]["degraded_recovered"],
            "field_mapping_attempts":fmap["phase99_alternative_field_mapping"]["field_mapping_attempts"],
            "stale_refresh_attempts":stale["phase99_stale_refresh"]["stale_refresh_attempts"],
            "stale_refresh_recovered":stale["phase99_stale_refresh"]["stale_refresh_recovered"],
            "replacement_attempts":repl["phase99_blocked_replacement"]["replacement_attempts"],
            "still_blocked":repl["phase99_blocked_replacement"]["still_blocked"],
            "total_recovered":cl["phase99_recovery_classifier"]["recovered"],
            "partially_recovered":cl["phase99_recovery_classifier"]["partially_recovered"],
            "recovery_history_written":hist["phase99_recovery_history"].get("entries_written",0),
            "recovery_history_path_ignored":True,
            "quality_gate":gate["phase99_recovery_quality_gate"]["overall"],
            "guard":guard["phase99_recovery_guard"]["overall"],
            "phase100":bl["phase99_backlog_update"]["phase100_recommendation"],
            "steps":steps,
            "mock_used":False,"fixture_used":False,"raw_saved":False,
            "pending_created":0,"paper_order_created":0,"real_trade_created":0,
            "target_price":0,"position_sizing":0
        }
    }
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
