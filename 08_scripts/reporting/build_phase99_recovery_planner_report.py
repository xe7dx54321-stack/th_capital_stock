import argparse,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase98_alert_classifier import classify_alerts
from smr_phase98_endpoint_heartbeat import run_heartbeat_probe
from smr_phase98_refresh_failure_detector import detect_refresh_failure
from smr_phase98_schema_drift_detector import detect_schema_drift
from smr_phase98_field_availability_monitor import monitor_field_availability
from smr_phase98_source_staleness_monitor import monitor_source_staleness
from smr_phase98_source_reliability_decay import compute_reliability_decay
from smr_phase98_blocked_source_escalation import escalate_blocked_sources
from smr_phase99_alert_to_recovery_mapper import map_alerts_to_actions
from smr_phase99_fallback_source_selector import select_fallback_sources
from smr_phase99_recovery_planner import build_recovery_plan
def main(): hb=run_heartbeat_probe("dry-run");rf=detect_refresh_failure(hb);sd=detect_schema_drift();fa=monitor_field_availability();st=monitor_source_staleness();rd=compute_reliability_decay();be=escalate_blocked_sources();al=classify_alerts(hb,rf,sd,fa,st,rd,be);am=map_alerts_to_actions(al);fb=select_fallback_sources(hb);r=build_recovery_plan(am,fb);print(json.dumps(r,ensure_ascii=False,indent=2) if "--json" in sys.argv else json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
