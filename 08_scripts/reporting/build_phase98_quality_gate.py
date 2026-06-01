import argparse,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
def main():
    from smr_phase98_endpoint_heartbeat import run_heartbeat_probe
    from smr_phase98_schema_drift_detector import detect_schema_drift
    from smr_phase98_field_availability_monitor import monitor_field_availability
    from smr_phase98_source_staleness_monitor import monitor_source_staleness
    from smr_phase98_monitoring_quality_gate import run_monitoring_quality_gate
    hb=run_heartbeat_probe("dry-run");sd=detect_schema_drift();fa=monitor_field_availability()
    st=monitor_source_staleness();r=run_monitoring_quality_gate(hb,sd,fa,st)
    if "--json" in sys.argv:print(json.dumps(r,ensure_ascii=False,indent=2))
    else:print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
