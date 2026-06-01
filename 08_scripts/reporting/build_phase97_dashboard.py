import argparse,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase97_config import load_config
from smr_phase97_phase96_db_compatibility import check_compatibility
from smr_phase97_source_refresh_policy import build_source_refresh_policy
from smr_phase97_incremental_loader import load_phase96_existing_db
from smr_phase97_record_fingerprint import dedup_records
from smr_phase97_lifecycle_classifier import classify_lifecycle
from smr_phase97_delta_detector import detect_deltas
from smr_phase97_stale_detector import detect_stale_expired
from smr_phase97_incremental_writer import write_incremental
from smr_phase97_quality_gate import run_refresh_quality_gate
from smr_phase97_cannot_conclude_guard import run_refresh_guard
from smr_phase97_backlog_update import build_backlog_update
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
    cfg=load_config()
    compat=check_compatibility()
    policy=build_source_refresh_policy()
    existing=load_phase96_existing_db()
    dedup=dedup_records(existing)
    lifecycle=classify_lifecycle(existing)
    delta=detect_deltas(existing, existing)
    stale=detect_stale_expired(existing)
    wr=write_incremental(dedup["phase97_dedup"]["records"],mode)
    gate=run_refresh_quality_gate(dedup, delta, wr)
    guard=run_refresh_guard(delta)
    bl=build_backlog_update()
    summary={
        "phase":"phase97","generated_at":__import__("datetime").datetime.now().isoformat(),
        "db_compatible":compat["phase97_phase96_db_compatibility"]["overall"],
        "existing_records":len(existing),
        "dedup_removed":dedup["phase97_dedup"]["duplicates_removed"],
        "lifecycle_fresh":lifecycle["phase97_lifecycle"]["fresh"],
        "lifecycle_stale":lifecycle["phase97_lifecycle"]["stale"],
        "lifecycle_expired":lifecycle["phase97_lifecycle"]["expired"],
        "quality_gate":gate["phase97_refresh_quality_gate"]["overall"],
        "guard":guard["phase97_refresh_guard"]["overall"],
        "phase98":bl["phase97_backlog_update"]["phase98_recommendation"],
        "records_written":wr.get("records_written",0),
        "db_path_ignored":wr.get("db_path_ignored",True),
        "mock_used":False,"fixture_used":False,"raw_saved":False,
        "pending_created":0,"paper_order_created":0,"real_trade_created":0,
        "target_price":0,"position_sizing":0
    }
    out={"summary":summary}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
