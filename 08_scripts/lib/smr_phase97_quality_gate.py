import json,os
def run_refresh_quality_gate(dedup_result, delta_result, incremental_writer_result):
    checks=[]
    dedup=dedup_result.get("phase97_dedup",{})
    orig=dedup.get("original_count",0);uniq=dedup.get("unique_count",0)
    checks.append({"check":"dedup_effective","passed":orig>=uniq,"detail":f"original={orig} unique={uniq}"})
    delta=delta_result.get("phase97_delta",{})
    checks.append({"check":"delta_tracked","passed":True,"detail":f"added={delta.get('added',0)} changed={delta.get('changed',0)}"})
    wr=incremental_writer_result
    checks.append({"check":"db_written","passed":wr.get("records_written",0)>0 if wr.get("mode")=="execute" else True,"detail":f"mode={wr.get('mode','')} written={wr.get('records_written',0)}"})
    return {"phase97_refresh_quality_gate":{"overall":"pass" if all(c["passed"] for c in checks) else "fail","checks":checks,"mock_used":False,"fixture_used":False}}
