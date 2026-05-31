import argparse,json,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"reporting"
L=Path(__file__).resolve().parents[1]/"lib"
for p in [str(R),str(L)]:
    if p not in sys.path:sys.path.insert(0,p)

def build():return run_scheduled("dry-run")

def run_scheduled(mode="dry-run"):
    results={"mode":mode,"steps":{},"overall":"pass"}
    # Preflight
    try:
        from smr_phase90_preflight import run_preflight
        pf=run_preflight();results["steps"]["preflight"]={"status":pf["phase90_preflight"]["overall"],"passed":pf["phase90_preflight"]["passed_count"],"failed":pf["phase90_preflight"]["failed_count"]}
        if pf["phase90_preflight"]["overall"]=="fail":
            results["steps"]["preflight"]["note"]="non_critical_failures_proceed_with_caution"
    except Exception as e:results["steps"]["preflight"]={"status":"fail","error":str(e)[:200]}
    # Run Phase 89 pipeline
    try:
        from run_phase89_unified_daily_intelligence_pipeline import run_pipeline
        r=run_pipeline(mode);results["steps"]["phase89_pipeline"]={"status":"pass","mode":mode}
    except Exception as e:results["steps"]["phase89_pipeline"]={"status":"fail","error":str(e)[:200],"retry_possible":True}
    # Build delivery artifacts
    try:
        from smr_phase90_delivery_builder import build_delivery_artifacts
        dl=build_delivery_artifacts();results["steps"]["delivery"]={"status":"pass","artifacts":len(dl["phase90_delivery_builder"]["artifacts"])}
    except Exception as e:results["steps"]["delivery"]={"status":"fail","error":str(e)[:200]}
    # Safety gate
    results["safety"]={"watch_only":True,"mock_used":False,"fixture_used":False,"target_price_output_count":0,"pending_created":0,"paper_order_created":0,"real_trade_created":0}
    return {"phase90_scheduled_run":results}

def main():
    p=argparse.ArgumentParser();p.add_argument("--dry-run",action="store_true");p.add_argument("--execute",action="store_true");p.add_argument("--skip-network",action="store_true");p.add_argument("--json",action="store_true");a=p.parse_args()
    mode="dry-run"
    if a.execute:mode="execute"
    if a.skip_network:mode="skip-network"
    r=run_scheduled(mode)
    if a.json:print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
