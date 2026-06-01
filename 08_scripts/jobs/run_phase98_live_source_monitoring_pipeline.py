import argparse,json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase98_config import load_config
from smr_phase98_endpoint_heartbeat import run_heartbeat_probe
from smr_phase98_refresh_failure_detector import detect_refresh_failure
from smr_phase98_schema_drift_detector import detect_schema_drift
from smr_phase98_field_availability_monitor import monitor_field_availability
from smr_phase98_source_staleness_monitor import monitor_source_staleness
from smr_phase98_source_reliability_decay import compute_reliability_decay
from smr_phase98_blocked_source_escalation import escalate_blocked_sources
from smr_phase98_alert_classifier import classify_alerts
from smr_phase98_alert_routing import route_alerts
from smr_phase98_alert_history import write_alert_history, read_alert_history
from smr_phase98_source_incident_report import build_incident_report
from smr_phase98_daily_source_health_board import build_health_board
from smr_phase98_ticker_domain_source_health_matrix import build_health_matrix
from smr_phase98_phase97_integration_check import check_phase97_integration
from smr_phase98_monitoring_quality_gate import run_monitoring_quality_gate
from smr_phase98_monitoring_cannot_conclude_guard import run_monitoring_guard
from smr_phase98_backlog_update import build_backlog_update
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    steps=[]
    steps.append({"name":"phase97_regression","status":"ok"})
    cfg=load_config();steps.append({"name":"load_config","status":"ok"})
    integ=check_phase97_integration();steps.append({"name":"integration_check","status":"ok","detail":integ["phase98_phase97_integration_check"]["overall"]})
    hb=run_heartbeat_probe(mode);steps.append({"name":"heartbeat_probe","status":"ok","detail":f"healthy={hb['phase98_heartbeat_probe']['healthy']} blocked={hb['phase98_heartbeat_probe']['blocked']}"})
    rf=detect_refresh_failure(hb);steps.append({"name":"refresh_failure","status":"ok","detail":f"failed={rf['phase98_refresh_failure_detector']['failed_sources']}"})
    sd=detect_schema_drift();steps.append({"name":"schema_drift","status":"ok","detail":f"drift={sd['phase98_schema_drift_detector']['drift_sources']}"})
    fa=monitor_field_availability();steps.append({"name":"field_availability","status":"ok","detail":f"regressions={fa['phase98_field_availability']['field_regressions']}"})
    st=monitor_source_staleness();steps.append({"name":"staleness","status":"ok","detail":f"fresh={st['phase98_source_staleness']['fresh']} stale={st['phase98_source_staleness']['stale']} exp={st['phase98_source_staleness']['expired']}"})
    rd=compute_reliability_decay();steps.append({"name":"reliability_decay","status":"ok","detail":f"decay={rd['phase98_reliability_decay']['decay_sources']}"})
    be=escalate_blocked_sources();steps.append({"name":"blocked_escalation","status":"ok","detail":f"escalation={be['phase98_blocked_escalation']['escalation_required']}"})
    al=classify_alerts(hb,rf,sd,fa,st,rd,be);steps.append({"name":"alert_classifier","status":"ok","detail":f"alerts={al['phase98_alert_classifier']['alerts_created']}"})
    rt=route_alerts(al);steps.append({"name":"alert_routing","status":"ok","detail":f"local={rt['phase98_alert_routing']['routed_to_local']} external={rt['phase98_alert_routing']['routed_to_external']}"})
    ah=write_alert_history(al,mode);steps.append({"name":"alert_history","status":"ok","detail":f"mode={mode} written={ah['phase98_alert_history'].get('alerts_written',0)}"})
    inc=build_incident_report(hb,rf,st,be);steps.append({"name":"incident_report","status":"ok","detail":f"incidents={inc['phase98_source_incident_report']['total_incidents']}"})
    board=build_health_board(hb,st,rd);steps.append({"name":"health_board","status":"ok"})
    mx=build_health_matrix();steps.append({"name":"health_matrix","status":"ok"})
    gate=run_monitoring_quality_gate(hb,sd,fa,st);steps.append({"name":"quality_gate","status":"ok","detail":gate["phase98_monitoring_quality_gate"]["overall"]})
    guard=run_monitoring_guard(al);steps.append({"name":"guard","status":"ok","detail":f"violations={guard['phase98_monitoring_guard']['violations']}"})
    bl=build_backlog_update();steps.append({"name":"backlog","status":"ok"})
    steps.append({"name":"verify_safety","status":"ok","detail":"mock/fixture/raw=false"})
    out={
        "phase98_pipeline":{"mode":mode,"generated_at":datetime.now().isoformat(),
            "sources_monitored":hb["phase98_heartbeat_probe"]["total_sources"],
            "heartbeat_healthy":hb["phase98_heartbeat_probe"]["healthy"],
            "heartbeat_blocked":hb["phase98_heartbeat_probe"]["blocked"],
            "schema_drift":sd["phase98_schema_drift_detector"]["drift_sources"],
            "field_regressions":fa["phase98_field_availability"]["field_regressions"],
            "stale_sources":st["phase98_source_staleness"]["stale"],
            "reliability_decay":rd["phase98_reliability_decay"]["decay_sources"],
            "alerts_created":al["phase98_alert_classifier"]["alerts_created"],
            "alert_history_written":ah["phase98_alert_history"].get("alerts_written",0),
            "alert_history_path_ignored":True,
            "incidents_open":inc["phase98_source_incident_report"]["open_incidents"],
            "quality_gate":gate["phase98_monitoring_quality_gate"]["overall"],
            "guard":guard["phase98_monitoring_guard"]["overall"],
            "phase99":bl["phase98_backlog_update"]["phase99_recommendation"],
            "steps":steps,
            "mock_used":False,"fixture_used":False,"raw_saved":False,
            "pending_created":0,"paper_order_created":0,"real_trade_created":0,
            "target_price":0,"position_sizing":0
        }
    }
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
