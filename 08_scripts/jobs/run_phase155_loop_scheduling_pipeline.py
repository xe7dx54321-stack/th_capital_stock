import json, sys, os, argparse
from pathlib import Path
from datetime import datetime
BASE_LIB = Path(__file__).resolve().parent.parent / "lib"
BASE_REPORTING = Path(__file__).resolve().parent.parent / "reporting"
sys.path.insert(0, str(BASE_LIB))
sys.path.insert(0, str(BASE_REPORTING))
from build_phase155_scheduling_dashboard import build

def run(mode="dry-run"):
    s = datetime.now().isoformat(); r = build(); d = r["phase155_scheduling_dashboard"]; b = d["board"]
    return {"phase155_loop_scheduling_pipeline":{"mode":mode,"started_at":s,"finished_at":datetime.now().isoformat(),
        "daily_targets":b["loop_plan"]["daily"]["targets_count"],
        "weekly_targets":b["loop_plan"]["weekly"]["weekly_targets_total"],
        "event_triggers":b["loop_plan"]["event"]["triggers"],
        "history_is_first_run":b["loop_history"]["reader"]["is_first_run"],
        "delta_available":b["loop_history"]["delta"]["delta_available"],
        "quality_gate":d["quality_gate"]["overall_status"],
        "guard":d["guard"]["overall_status"],
        "cannot_conclude_guard":d["cannot_conclude_guard"]["overall_status"],
        "violations":d["guard"]["violations"],
        "research_only":True,"agent_simulation_only":True,"live_llm_call_made":False,
        "watch_core_updated":False,"candidate_auto_activated":False,
        "schedule_not_trade_plan":True,"event_not_trade_signal":True,
        "history_not_pnl":True,"digest_not_advice":True,
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
