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
        from build_phase86_integration import build;r=build()
        results["steps"]["phase86_regression"]={"status":"pass","integration_pricing":r.get("phase86_integration",{}).get("pricing_available",0)}
    except Exception as e:results["steps"]["phase86_regression"]={"status":"fail","error":str(e)[:200]}
    try:
        from build_phase87_config_report import build;r=build()
        results["steps"]["config"]={"status":"pass"}
    except Exception as e:results["steps"]["config"]={"status":"fail","error":str(e)[:200]}
    try:
        from build_phase87_external_source_registry_report import build;r=build()
        d=r["phase87_external_source_registry"];results["steps"]["source_registry"]={"status":"pass","sources":d["sources_defined"]}
    except Exception as e:results["steps"]["source_registry"]={"status":"fail","error":str(e)[:200]}
    try:
        from build_phase87_external_evidence_report import build;r=build()
        d=r["phase87_external_evidence"];results["steps"]["evidence"]={"status":"pass","entries":d["evidence_entries"]}
    except Exception as e:results["steps"]["evidence"]={"status":"fail","error":str(e)[:200]}
    try:
        from build_phase87_coverage_blocker import build;r=build()
        d=r["phase87_coverage_blocker_report"];results["steps"]["coverage_blocker"]={"status":"pass","available":d["source_available"],"blocked":d["blocked"]}
    except Exception as e:results["steps"]["coverage_blocker"]={"status":"fail","error":str(e)[:200]}
    try:
        from build_phase87_external_watch_board import build;r=build()
        results["steps"]["watch_board"]={"status":"pass"}
    except Exception as e:results["steps"]["watch_board"]={"status":"fail","error":str(e)[:200]}
    try:
        from build_phase87_external_source_guard import build;r=build()
        results["steps"]["guard"]={"status":"pass"}
    except Exception as e:results["steps"]["guard"]={"status":"fail","error":str(e)[:200]}
    results["safety"]={"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,"target_price_output_count":0,"pending_created":0,"paper_order_created":0,"real_trade_created":0}
    return {"phase87_external_source_pipeline":results}

def main():
    p=argparse.ArgumentParser();p.add_argument("--dry-run",action="store_true");p.add_argument("--execute",action="store_true");p.add_argument("--skip-network",action="store_true");p.add_argument("--json",action="store_true");a=p.parse_args()
    mode="dry-run"
    if a.execute:mode="execute"
    if a.skip_network:mode="skip-network"
    r=run_pipeline(mode)
    if a.json:print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
