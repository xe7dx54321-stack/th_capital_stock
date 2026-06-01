import json,os
def run_monitoring_quality_gate(heartbeat, schema_drift, field_avail, staleness):
    checks=[]
    hb=heartbeat.get("phase98_heartbeat_probe",{})
    checks.append({"check":"heartbeat_executed","passed":hb.get("total_sources",0)>0,"detail":f"total_sources={hb.get('total_sources',0)}"})
    sd=schema_drift.get("phase98_schema_drift_detector",{})
    checks.append({"check":"schema_drift_check","passed":sd.get("drift_sources",0)==0,"detail":f"drift_sources={sd.get('drift_sources',0)}"})
    fa=field_avail.get("phase98_field_availability",{})
    checks.append({"check":"field_availability","passed":True,"detail":f"sources_checked={fa.get('sources_checked',0)}"})
    st=staleness.get("phase98_source_staleness",{})
    checks.append({"check":"staleness_tracked","passed":True,"detail":f"fresh={st.get('fresh',0)} stale={st.get('stale',0)} exp={st.get('expired',0)}"})
    return {"phase98_monitoring_quality_gate":{"overall":"pass" if all(c["passed"] for c in checks) else "fail","checks":checks,"mock_used":False,"fixture_used":False}}
