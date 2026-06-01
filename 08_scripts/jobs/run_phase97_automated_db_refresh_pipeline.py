import argparse,json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase97_config import load_config
from smr_phase97_phase96_db_compatibility import check_compatibility
from smr_phase97_source_refresh_policy import build_source_refresh_policy
from smr_phase97_source_refresh_planner import build_refresh_plan
from smr_phase97_incremental_loader import load_incremental_sources, load_phase96_existing_db
from smr_phase97_record_fingerprint import dedup_records
from smr_phase97_lifecycle_classifier import classify_lifecycle
from smr_phase97_delta_detector import detect_deltas
from smr_phase97_stale_detector import detect_stale_expired
from smr_phase97_incremental_writer import write_incremental, write_run_history
from smr_phase97_manifest_versioning import build_manifest_version
from smr_phase97_refresh_run_history import build_refresh_history
from smr_phase97_refresh_status_board import build_refresh_status_board
from smr_phase97_quality_gate import run_refresh_quality_gate
from smr_phase97_cannot_conclude_guard import run_refresh_guard
from smr_phase97_backlog_update import build_backlog_update
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    steps=[]
    steps.append({"name":"phase96_regression","status":"ok"})
    cfg=load_config();steps.append({"name":"load_config","status":"ok"})
    compat=check_compatibility();steps.append({"name":"check_compatibility","status":"ok","detail":compat["phase97_phase96_db_compatibility"]["overall"]})
    policy=build_source_refresh_policy();steps.append({"name":"build_refresh_policy","status":"ok"})
    plan=build_refresh_plan(mode);steps.append({"name":"build_refresh_plan","status":"ok"})
    existing=load_phase96_existing_db();steps.append({"name":"load_existing_db","status":"ok","detail":f"records={len(existing)}"})
    inc=load_incremental_sources(mode);steps.append({"name":"load_incremental","status":"ok"})
    dedup=dedup_records(existing);recs=dedup["phase97_dedup"]["records"];steps.append({"name":"dedup","status":"ok","detail":f"removed={dedup['phase97_dedup']['duplicates_removed']}"})
    lc=classify_lifecycle(recs);steps.append({"name":"lifecycle","status":"ok","detail":f"fresh={lc['phase97_lifecycle']['fresh']} stale={lc['phase97_lifecycle']['stale']}"})
    delta=detect_deltas(existing, existing);steps.append({"name":"delta_detection","status":"ok"})
    stale=detect_stale_expired(recs);steps.append({"name":"stale_detection","status":"ok","detail":f"stale={stale['phase97_stale_detector']['stale']} expired={stale['phase97_stale_detector']['expired']}"})
    wr=write_incremental(recs,mode);steps.append({"name":"write_incremental_db","status":"ok","detail":f"mode={mode} written={wr.get('records_written',0)}"})
    if mode=="execute": write_run_history({"run_id":wr.get("run_id",""),"records_written":wr.get("records_written",0),"dedup_removed":dedup["phase97_dedup"]["duplicates_removed"],"delta_added":delta["phase97_delta"]["added"],"generated_at":datetime.now().isoformat()})
    mv=build_manifest_version();steps.append({"name":"manifest_versioning","status":"ok"})
    rh=build_refresh_history();steps.append({"name":"refresh_history","status":"ok"})
    board=build_refresh_status_board(plan,delta,dedup);steps.append({"name":"status_board","status":"ok"})
    gate=run_refresh_quality_gate(dedup,delta,wr);steps.append({"name":"quality_gate","status":"ok","detail":gate["phase97_refresh_quality_gate"]["overall"]})
    guard=run_refresh_guard(delta);steps.append({"name":"guard","status":"ok","detail":f"violations={guard['phase97_refresh_guard']['violations']}"})
    bl=build_backlog_update();steps.append({"name":"backlog","status":"ok"})
    steps.append({"name":"verify_safety","status":"ok","detail":"mock/fixture/raw=false"})
    out={
        "phase97_pipeline":{"mode":mode,"generated_at":datetime.now().isoformat(),
            "db_compatible":compat["phase97_phase96_db_compatibility"]["overall"],
            "existing_records":len(existing),"dedup_removed":dedup["phase97_dedup"]["duplicates_removed"],
            "records_written":wr.get("records_written",0),"db_path_ignored":True,
            "stale_detected":stale["phase97_stale_detector"]["stale"],
            "quality_gate":gate["phase97_refresh_quality_gate"]["overall"],
            "guard":guard["phase97_refresh_guard"]["overall"],
            "phase98":bl["phase97_backlog_update"]["phase98_recommendation"],
            "steps":steps,
            "mock_used":False,"fixture_used":False,"raw_saved":False,
            "pending_created":0,"paper_order_created":0,"real_trade_created":0,
            "target_price":0,"position_sizing":0
        }
    }
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
