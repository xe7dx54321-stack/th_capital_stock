import argparse,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase96_config import load_config
from smr_phase96_evidence_loader import load_phase92_95_evidence
from smr_phase96_db_writer import write_hard_data_db
from smr_phase96_ticker_profile import build_ticker_hard_data_profiles
from smr_phase96_peer_group_registry import build_peer_group_registry
from smr_phase96_peer_benchmark_matrix import build_peer_benchmark_matrix
from smr_phase96_field_missingness import build_field_missingness_report
from smr_phase96_quality_gate import run_db_quality_gate
from smr_phase96_cannot_conclude_guard import run_peer_benchmark_cannot_conclude_guard
from smr_phase96_backlog_update import build_backlog_update
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
    cfg=load_config()
    ev=load_phase92_95_evidence();records=ev["phase96_evidence_loader"]["records"]
    norm_records=records
    db=write_hard_data_db(norm_records,mode)
    prof=build_ticker_hard_data_profiles(records)
    pg=build_peer_group_registry()
    mat=build_peer_benchmark_matrix(records,prof)
    miss=build_field_missingness_report(records)
    gate=run_db_quality_gate(records)
    guard=run_peer_benchmark_cannot_conclude_guard(records)
    bl=build_backlog_update()
    summary={
        "phase":"phase96","generated_at":__import__("datetime").datetime.now().isoformat(),
        "records_loaded":ev["phase96_evidence_loader"]["records_loaded"],
        "records_written":db.get("records_written",0),
        "db_path_ignored":db.get("db_path_ignored",True),
        "tickers_profiled":prof["phase96_ticker_hard_data_profile"]["tickers_profiled"],
        "peer_groups":pg["phase96_peer_group_registry"]["peer_groups_created"],
        "quality_gate":gate["phase96_db_quality_gate"]["overall"],
        "guard_status":guard["phase96_peer_benchmark_cannot_conclude_guard"]["overall"],
        "critical_missing":miss["phase96_field_missingness_report"]["critical_missing_fields"],
        "phase97":bl["phase96_backlog_update"]["phase97_recommendation"],
        "mock_used":False,"fixture_used":False,"raw_saved":False,
        "pending_created":0,"paper_order_created":0,"real_trade_created":0,
        "target_price":0,"position_sizing":0
    }
    out={"summary":summary}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
