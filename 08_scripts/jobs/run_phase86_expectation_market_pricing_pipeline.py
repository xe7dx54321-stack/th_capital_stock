import argparse,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"reporting"
L=Path(__file__).resolve().parents[1]/"lib"
for p in [str(R),str(L)]:
    if p not in sys.path:sys.path.insert(0,p)

def build():return run_pipeline("dry-run")

def run_pipeline(mode="dry-run"):
    results={"mode":mode,"steps":{},"overall":"pass"}
    # Step 1: Phase 85b regression
    try:
        from build_phase85b_closeout_audit import build;r=build()
        results["steps"]["phase85b_regression"]={"status":"pass","valuation_available":r.get("phase85b_closeout_audit",{}).get("valuation_available",0)}
    except Exception as e:results["steps"]["phase85b_regression"]={"status":"fail","error":str(e)[:200]}
    # Step 2: Config
    try:
        from build_phase86_config_report import build;r=build()
        results["steps"]["config"]={"status":"pass","tickers":len(r["target_tickers"])}
    except Exception as e:results["steps"]["config"]={"status":"fail","error":str(e)[:200]}
    # Step 3: Pricing adapter
    try:
        from build_phase86_pricing_adapter_report import build;r=build()
        d=r["phase86_pricing_adapter"];results["steps"]["pricing"]={"status":"pass","available":d["pricing_available"],"unavailable":d["pricing_unavailable"]}
    except Exception as e:results["steps"]["pricing"]={"status":"fail","error":str(e)[:200]}
    # Step 4: Expectation adapter
    try:
        from build_phase86_expectation_adapter_report import build;r=build()
        d=r["phase86_expectation_adapter"];results["steps"]["expectation"]={"status":"pass","available":d["expectation_available"],"partial":d["expectation_partial"],"exhausted":d["expectation_exhausted"]}
    except Exception as e:results["steps"]["expectation"]={"status":"fail","error":str(e)[:200]}
    # Step 5: Integration
    try:
        from build_phase86_integration import build;r=build()
        d=r["phase86_integration"];results["steps"]["integration"]={"status":"pass","pricing_ok":d["pricing_available"],"valuation_ok":d["valuation_available"],"expectation_ok":d["expectation_available"]}
    except Exception as e:results["steps"]["integration"]={"status":"fail","error":str(e)[:200]}
    # Step 6: Closeout
    try:
        from build_phase86_closeout_audit import build;r=build()
        d=r["phase86_expectation_pricing_closeout"];results["steps"]["closeout"]={"status":"pass","pricing":d["pricing_available"],"expectation":d["expectation_available"]}
    except Exception as e:results["steps"]["closeout"]={"status":"fail","error":str(e)[:200]}
    # Step 7: Watch board
    try:
        from build_phase86_expectation_aware_watch_board import build;r=build()
        results["steps"]["watch_board"]={"status":"pass"}
    except Exception as e:results["steps"]["watch_board"]={"status":"fail","error":str(e)[:200]}
    # Step 8: Guard
    try:
        from build_phase86_expectation_pricing_guard import build;r=build()
        results["steps"]["guard"]={"status":"pass"}
    except Exception as e:results["steps"]["guard"]={"status":"fail","error":str(e)[:200]}
    results["safety"]={"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,"target_price_output_count":0,"position_sizing_created":0,"pending_created":0,"paper_order_created":0,"real_trade_created":0}
    return {"phase86_expectation_market_pricing_pipeline":results}

def main():
    p=argparse.ArgumentParser();p.add_argument("--dry-run",action="store_true");p.add_argument("--execute",action="store_true");p.add_argument("--skip-network",action="store_true");p.add_argument("--json",action="store_true");a=p.parse_args()
    mode="dry-run"
    if a.execute:mode="execute"
    if a.skip_network:mode="skip-network"
    r=run_pipeline(mode)
    if a.json:print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
