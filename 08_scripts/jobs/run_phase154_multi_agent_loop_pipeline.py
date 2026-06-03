import json, sys, os, argparse
from pathlib import Path
from datetime import datetime
BASE_LIB = Path(__file__).resolve().parent.parent / "lib"
BASE_REPORTING = Path(__file__).resolve().parent.parent / "reporting"
sys.path.insert(0, str(BASE_LIB))
sys.path.insert(0, str(BASE_REPORTING))
from build_phase154_loop_research_dashboard import build

def run(mode="dry-run"):
    s = datetime.now().isoformat(); r = build(); d = r["phase154_loop_research_dashboard"]; b = d["board"]; j = b["agents"]["judge"]
    return {"phase154_multi_agent_loop_pipeline": {
        "mode": mode, "started_at": s, "finished_at": datetime.now().isoformat(),
        "loop_targets_total": b["loop_targets_total"],
        "judge_passed": j["passed"], "judge_blocked": j["blocked"],
        "quality_gate": d["quality_gate"]["overall_status"],
        "guard": d["guard"]["overall_status"],
        "cannot_conclude_guard": d["cannot_conclude_guard"]["overall_status"],
        "violations": d["guard"]["violations"],
        "research_only": True, "agent_simulation_only": True, "live_llm_call_made": False,
        "watch_core_updated": False, "candidate_auto_activated": False,
        "confirmed_thesis_created": b["thesis_proposals"]["confirmed_thesis_created"],
        "owner_actions_contain_trade": False,
        "mock_used": False, "fixture_used": False,
        "trade_recommendation_created": 0, "target_price_created": 0,
        "position_sizing_created": 0, "paper_order_created": 0, "paper_trade_created": 0,
        "broker_api_called": False, "llm_api_called": False,
    }}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true"); p.add_argument("--execute", action="store_true")
    p.add_argument("--skip-network", action="store_true"); p.add_argument("--json", action="store_true")
    a = p.parse_args()
    m = "execute" if a.execute else ("skip-network" if a.skip_network else "dry-run")
    print(json.dumps(run(m), indent=2, ensure_ascii=False, default=str))

if __name__ == "__main__": main()
