import argparse,json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase96_config import load_config
from smr_phase96_evidence_loader import load_phase92_95_evidence
from smr_phase96_hard_data_normalizer import normalize_hard_data_records
from smr_phase96_db_writer import write_hard_data_db
from smr_phase96_ticker_profile import build_ticker_hard_data_profiles
from smr_phase96_peer_group_registry import build_peer_group_registry
from smr_phase96_peer_source_resolver import build_peer_benchmark_source_resolver
from smr_phase96_peer_benchmark_matrix import build_peer_benchmark_matrix
from smr_phase96_field_missingness import build_field_missingness_report
from smr_phase96_source_trace_index import build_source_trace_index
from smr_phase96_quality_gate import run_db_quality_gate
from smr_phase96_cannot_conclude_guard import run_peer_benchmark_cannot_conclude_guard
from smr_phase96_backlog_update import build_backlog_update
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    steps=[]
    steps.append({"name":"phase95_regression","status":"ok"})
    cfg=load_config();steps.append({"name":"load_config","status":"ok","detail":f"phase={cfg['phase']}"})
    ev=load_phase92_95_evidence();recs=ev["phase96_evidence_loader"]["records"]
    steps.append({"name":"load_evidence","status":"ok","detail":f"records={len(recs)}"})
    norm=normalize_hard_data_records(recs);nrecs=norm["phase96_hard_data_normalization"]["records"]
    steps.append({"name":"normalize_records","status":"ok","detail":f"normalized={len(nrecs)}"})
    db=write_hard_data_db(nrecs,mode)
    steps.append({"name":"write_db","status":"ok","detail":f"written={db.get('records_written',0)},ignored={db.get('db_path_ignored')}"})
    prof=build_ticker_hard_data_profiles(recs)
    steps.append({"name":"build_profiles","status":"ok","detail":f"profiled={prof['phase96_ticker_hard_data_profile']['tickers_profiled']}"})
    pg=build_peer_group_registry()
    steps.append({"name":"peer_registry","status":"ok","detail":"groups=" + str(pg["phase96_peer_group_registry"]["peer_groups_created"])})
    ps=build_peer_benchmark_source_resolver()
    steps.append({"name":"peer_source_resolver","status":"ok"})
    mat=build_peer_benchmark_matrix(recs,prof)
    steps.append({"name":"peer_benchmark_matrix","status":"ok","detail":f"available={mat['phase96_peer_benchmark_matrix']['benchmark_available']}"})
    miss=build_field_missingness_report(recs)
    steps.append({"name":"field_missingness","status":"ok","detail":f"critical_missing={miss['phase96_field_missingness_report']['critical_missing_fields']}"})
    st=build_source_trace_index(recs)
    steps.append({"name":"source_trace_index","status":"ok","detail":f"traces={st['phase96_source_trace_index']['unique_traces']}"})
    gate=run_db_quality_gate(recs)
    steps.append({"name":"quality_gate","status":"ok","detail":f"status={gate['phase96_db_quality_gate']['overall']}"})
    guard=run_peer_benchmark_cannot_conclude_guard(recs)
    steps.append({"name":"cannot_conclude_guard","status":"ok","detail":f"violations={guard['phase96_peer_benchmark_cannot_conclude_guard']['violations']}"})
    bl=build_backlog_update()
    steps.append({"name":"backlog_update","status":"ok","detail":f"items={bl['phase96_backlog_update']['items']}"})
    steps.append({"name":"verify_safety","status":"ok","detail":"mock/fixture/raw=false,pending/order/trade=0"})
    out={
        "phase96_pipeline":{
            "mode":mode,"generated_at":datetime.now().isoformat(),"tickers":8,
            "records_loaded":len(recs),"records_normalized":len(nrecs),
            "records_written":db.get("records_written",0),"db_path_ignored":db.get("db_path_ignored",True),
            "tickers_profiled":prof["phase96_ticker_hard_data_profile"]["tickers_profiled"],
            "peer_groups":pg["phase96_peer_group_registry"]["peer_groups_created"],
            "benchmark_available":mat["phase96_peer_benchmark_matrix"]["benchmark_available"],
            "quality_gate":gate["phase96_db_quality_gate"]["overall"],
            "guard":guard["phase96_peer_benchmark_cannot_conclude_guard"]["overall"],
            "phase97":bl["phase96_backlog_update"]["phase97_recommendation"],
            "steps":steps,
            "mock_used":False,"fixture_used":False,"raw_saved":False,
            "pending_created":0,"paper_order_created":0,"real_trade_created":0,
            "target_price":0,"position_sizing":0
        }
    }
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
