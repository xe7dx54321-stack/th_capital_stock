import argparse,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
def main():
    from smr_phase98_endpoint_heartbeat import run_heartbeat_probe
    from smr_phase98_refresh_failure_detector import detect_refresh_failure
    from smr_phase98_source_staleness_monitor import monitor_source_staleness
    from smr_phase98_blocked_source_escalation import escalate_blocked_sources
    from smr_phase98_source_incident_report import build_incident_report
    hb=run_heartbeat_probe("dry-run");rf=detect_refresh_failure(hb);st=monitor_source_staleness()
    be=escalate_blocked_sources();r=build_incident_report(hb,rf,st,be)
    if "--json" in sys.argv:print(json.dumps(r,ensure_ascii=False,indent=2))
    else:print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
