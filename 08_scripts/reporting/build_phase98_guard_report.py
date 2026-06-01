import argparse,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
def main():
    from smr_phase98_endpoint_heartbeat import run_heartbeat_probe
    from smr_phase98_refresh_failure_detector import detect_refresh_failure
    from smr_phase98_schema_drift_detector import detect_schema_drift
    from smr_phase98_field_availability_monitor import monitor_field_availability
    from smr_phase98_source_staleness_monitor import monitor_source_staleness
    from smr_phase98_source_reliability_decay import compute_reliability_decay
    from smr_phase98_blocked_source_escalation import escalate_blocked_sources
    from smr_phase98_alert_classifier import classify_alerts
    from smr_phase98_monitoring_cannot_conclude_guard import run_monitoring_guard
    hb=run_heartbeat_probe("dry-run");rf=detect_refresh_failure(hb);sd=detect_schema_drift()
    fa=monitor_field_availability();st=monitor_source_staleness();rd=compute_reliability_decay()
    be=escalate_blocked_sources();al=classify_alerts(hb,rf,sd,fa,st,rd,be);r=run_monitoring_guard(al)
    if "--json" in sys.argv:print(json.dumps(r,ensure_ascii=False,indent=2))
    else:print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
