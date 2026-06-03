import json, sys, os, argparse
from pathlib import Path
from datetime import datetime
BASE_LIB = Path(__file__).resolve().parent.parent / "lib"
BASE_REPORTING = Path(__file__).resolve().parent.parent / "reporting"
sys.path.insert(0, str(BASE_LIB))
sys.path.insert(0, str(BASE_REPORTING))
from build_phase159_submission_dashboard import build

def run(mode="dry-run"):
    s = datetime.now().isoformat(); r = build(); d = r["phase159_submission_dashboard"]; b = d["board"]; fl = b["file_locator"]; q = b["quarantine"]; sm = b["safe_manifest"]
    return {"phase159_submission_pipeline":{"mode":mode,"started_at":s,"finished_at":datetime.now().isoformat(),
        "owner_input_present":fl["owner_input_present"],"invalid_count":q["invalid_count"],"safe_count":sm["safe_count"],
        "quality_gate":d["quality_gate"]["overall_status"],"guard":d["guard"]["overall_status"],
        "cannot_conclude_guard":d["cannot_conclude_guard"]["overall_status"],"violations":d["guard"]["violations"],
        "research_only":True,"submission_not_execution":True,"validation_not_activation":True,
        "preview_not_real":True,"manifest_not_watch_update":True,
        "approve_not_buy":True,"reject_not_sell":True,
        "watch_core_updated":False,"candidate_auto_activated":False,
        "mock_used":False,"fixture_used":False,
        "trade_recommendation_created":0,"target_price_created":0,"position_sizing_created":0,
        "paper_order_created":0,"paper_trade_created":0,"broker_api_called":False,"llm_api_called":False,
    }}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--dry-run",action="store_true"); p.add_argument("--execute",action="store_true")
    p.add_argument("--skip-network",action="store_true"); p.add_argument("--json",action="store_true")
    a = p.parse_args(); m = "execute" if a.execute else ("skip-network" if a.skip_network else "dry-run")
    print(json.dumps(run(m), indent=2, ensure_ascii=False, default=str))

if __name__ == "__main__": main()
