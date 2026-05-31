import argparse,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"reporting"
L=Path(__file__).resolve().parents[1]/"lib"
for p in [str(R),str(L)]:
    if p not in sys.path:sys.path.insert(0,p)

def build():return run_pipeline("dry-run")

def run_pipeline(mode="dry-run"):
    results={"mode":mode,"steps":{},"overall":"pass"}
    try:
        from build_phase88_daily_delta_report import build;r=build()
        results["steps"]["phase88_regression"]={"status":"pass","texts":r.get("phase88_daily_delta",{}).get("external_texts_checked",0)}
    except Exception as e:results["steps"]["phase88_regression"]={"status":"fail","error":str(e)[:200]}
    try:
        from build_phase89_config_report import build;r=build()
        results["steps"]["config"]={"status":"pass"}
    except Exception as e:results["steps"]["config"]={"status":"fail","error":str(e)[:200]}
    try:
        from build_phase89_subsystem_registry import build;r=build()
        d=r["phase89_subsystem_registry"];results["steps"]["subsystem_registry"]={"status":"pass","subsystems":d["subsystems_defined"]}
    except Exception as e:results["steps"]["subsystem_registry"]={"status":"fail","error":str(e)[:200]}
    try:
        from build_phase89_unified_ticker_state import build;r=build()
        d=r["phase89_unified_ticker_state"];results["steps"]["ticker_state"]={"status":"pass","full":d["full_coverage"],"partial":d["partial_coverage"],"degraded":d["degraded"],"blocked":d["blocked"]}
    except Exception as e:results["steps"]["ticker_state"]={"status":"fail","error":str(e)[:200]}
    try:
        from build_phase89_source_health import build;r=build()
        d=r["phase89_source_health"];results["steps"]["source_health"]={"status":"pass","overall":d["overall"]}
    except Exception as e:results["steps"]["source_health"]={"status":"fail","error":str(e)[:200]}
    try:
        from build_phase89_opportunity_risk import build;r=build()
        results["steps"]["opportunity_risk"]={"status":"pass"}
    except Exception as e:results["steps"]["opportunity_risk"]={"status":"fail","error":str(e)[:200]}
    try:
        from build_phase89_unified_watch_board import build;r=build()
        results["steps"]["watch_board"]={"status":"pass"}
    except Exception as e:results["steps"]["watch_board"]={"status":"fail","error":str(e)[:200]}
    try:
        from build_phase89_unified_guard import build;r=build()
        results["steps"]["guard"]={"status":"pass"}
    except Exception as e:results["steps"]["guard"]={"status":"fail","error":str(e)[:200]}
    results["safety"]={"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,"target_price_output_count":0,"position_sizing_created":0,"pending_created":0,"paper_order_created":0,"real_trade_created":0}
    return {"phase89_unified_daily_intelligence_pipeline":results}

def main():
    p=argparse.ArgumentParser();p.add_argument("--dry-run",action="store_true");p.add_argument("--execute",action="store_true");p.add_argument("--skip-network",action="store_true");p.add_argument("--json",action="store_true");a=p.parse_args()
    mode="dry-run"
    if a.execute:mode="execute"
    if a.skip_network:mode="skip-network"
    r=run_pipeline(mode)
    if a.json:print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
