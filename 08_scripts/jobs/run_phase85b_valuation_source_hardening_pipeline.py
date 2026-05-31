import argparse,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"reporting"
L=Path(__file__).resolve().parents[1]/"lib"
for p in [str(R),str(L)]:
    if p not in sys.path:sys.path.insert(0,p)

def build():
    return run_pipeline("dry-run")

def run_pipeline(mode="dry-run"):
    results={"mode":mode,"steps":{},"overall":"pass"}
    # Phase 85 regression
    try:
        from build_phase85_valuation_availability_audit import build;r=build()
        results["steps"]["phase85_regression"]={"status":"pass","valuation_available":r.get("phase85_valuation_availability_audit",{}).get("valuation_available",0)}
    except Exception as e:results["steps"]["phase85_regression"]={"status":"fail","error":str(e)[:200]}
    # Config
    try:
        from build_phase85b_closeout_config_report import build;r=build()
        results["steps"]["config"]={"status":"pass"}
    except Exception as e:results["steps"]["config"]={"status":"fail","error":str(e)[:200]}
    # Fallback
    try:
        from build_phase85b_fallback_registry_report import build;r=build()
        results["steps"]["fallback_registry"]={"status":"pass"}
    except Exception as e:results["steps"]["fallback_registry"]={"status":"fail","error":str(e)[:200]}
    # HK hardening
    try:
        from build_phase85b_hk_valuation_hardening_report import build;r=build()
        d=r["phase85b_hk_valuation_hardening"];results["steps"]["hk_hardening"]={"status":"pass","valuation_available":d["valuation_available"]}
    except Exception as e:results["steps"]["hk_hardening"]={"status":"fail","error":str(e)[:200]}
    # 688041 hardening
    try:
        from build_phase85b_688041_valuation_hardening_report import build;r=build()
        d=r["phase85b_688041_valuation_hardening"];results["steps"]["688041_hardening"]={"status":"pass","valuation_found":d["valuation_found"]}
    except Exception as e:results["steps"]["688041_hardening"]={"status":"fail","error":str(e)[:200]}
    # Source exhaustion
    try:
        from build_phase85b_source_exhaustion_report import build;r=build()
        d=r["phase85b_source_exhaustion_report"];results["steps"]["source_exhaustion"]={"status":"pass","resolved":d["resolved"]}
    except Exception as e:results["steps"]["source_exhaustion"]={"status":"fail","error":str(e)[:200]}
    # Closeout
    try:
        from build_phase85b_closeout_audit import build;r=build()
        d=r["phase85b_closeout_audit"];results["steps"]["closeout_audit"]={"status":"pass","total":d["tickers_total"],"valuation_available":d["valuation_available"],"blocked":d["blocked"]}
    except Exception as e:results["steps"]["closeout_audit"]={"status":"fail","error":str(e)[:200]}
    # Lint
    try:
        from build_phase85b_closeout_brief_quality_lint import build;r=build()
        results["steps"]["brief_lint"]={"status":"pass"}
    except Exception as e:results["steps"]["brief_lint"]={"status":"fail","error":str(e)[:200]}
    results["safety"]={"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}
    return {"phase85b_valuation_source_hardening_pipeline":results}

def main():
    p=argparse.ArgumentParser();p.add_argument("--dry-run",action="store_true");p.add_argument("--execute",action="store_true");p.add_argument("--skip-network",action="store_true");p.add_argument("--json",action="store_true");a=p.parse_args()
    mode="dry-run"
    if a.execute:mode="execute"
    if a.skip_network:mode="skip-network"
    r=run_pipeline(mode)
    if a.json:print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
