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
    cfg=load_config()
    integ=check_phase97_integration()
    hb=run_heartbeat_probe(mode)
    rf=detect_refresh_failure(hb)
    sd=detect_schema_drift()
    fa=monitor_field_availability()
    st=monitor_source_staleness()
    rd=compute_reliability_decay()
    be=escalate_blocked_sources()
    al=classify_alerts(hb,rf,sd,fa,st,rd,be)
    rt=route_alerts(al)
    inc=build_incident_report(hb,rf,st,be)
    board=build_health_board(hb,st,rd)
    mx=build_health_matrix()
    gate=run_monitoring_quality_gate(hb,sd,fa,st)
    guard=run_monitoring_guard(al)
    bl=build_backlog_update()
    sev=al["phase98_alert_classifier"]["severity_breakdown"]
    summary={
        "phase":"phase98","generated_at":datetime.now().isoformat(),
        "sources_monitored":hb["phase98_heartbeat_probe"]["total_sources"],
        "heartbeat_healthy":hb["phase98_heartbeat_probe"]["healthy"],
        "heartbeat_blocked":hb["phase98_heartbeat_probe"]["blocked"],
        "schema_drift":sd["phase98_schema_drift_detector"]["drift_sources"],
        "field_regressions":fa["phase98_field_availability"]["field_regressions"],
        "stale_sources":st["phase98_source_staleness"]["stale"],
        "expired_sources":st["phase98_source_staleness"]["expired"],
        "reliability_decay":rd["phase98_reliability_decay"]["decay_sources"],
        "alerts_total":al["phase98_alert_classifier"]["alerts_created"],
        "alerts_info":sev.get("info",0),"alerts_warning":sev.get("warning",0),
        "alerts_critical":sev.get("critical",0),"alerts_escalation":sev.get("escalation",0),
        "external_notification_enabled":False,
        "alert_history_path_ignored":True,
        "incidents_open":inc["phase98_source_incident_report"]["open_incidents"],
        "integration_check":integ["phase98_phase97_integration_check"]["overall"],
        "quality_gate":gate["phase98_monitoring_quality_gate"]["overall"],
        "guard":guard["phase98_monitoring_guard"]["overall"],
        "phase99":bl["phase98_backlog_update"]["phase99_recommendation"],
        "mock_used":False,"fixture_used":False,"raw_saved":False,
        "pending_created":0,"paper_order_created":0,"real_trade_created":0,
        "target_price":0,"position_sizing":0
    }
    out={"summary":summary}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
