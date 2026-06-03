import json, sys, os, argparse
from pathlib import Path
from datetime import datetime
BASE_LIB = Path(__file__).resolve().parent.parent / "lib"
BASE_REPORTING = Path(__file__).resolve().parent.parent / "reporting"
sys.path.insert(0, str(BASE_LIB)); sys.path.insert(0, str(BASE_REPORTING))
from build_phase147_onboarding_dashboard import build

def run(mode="dry-run"):
    s = datetime.now().isoformat()
    r = build(); d = r["phase147_onboarding_dashboard"]
    return {"phase147_onboarding_pipeline": {
        "mode": mode, "started_at": s, "finished_at": datetime.now().isoformat(),
        "total_tickers": d["pipeline"]["summary"]["total_tickers"],
        "onboarded": d["pipeline"]["summary"]["onboarded"],
        "candidates": d["pipeline"]["summary"]["candidates"],
        "stages": d["stage_checklist"]["stages"],
        "quality_gate": d["quality_gate"]["overall_status"],
        "guard": d["guard"]["overall_status"], "violations": d["guard"]["violations"],
        "research_only": True, "mock_used": False, "fixture_used": False,
        "trade_recommendation_created": 0, "paper_order_created": 0,
    }}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--dry-run", action="store_true"); p.add_argument("--execute", action="store_true"); p.add_argument("--skip-network", action="store_true"); p.add_argument("--json", action="store_true")
    a = p.parse_args()
    m = "execute" if a.execute else ("skip-network" if a.skip_network else "dry-run")
    print(json.dumps(run(m), indent=2, ensure_ascii=False, default=str))

if __name__ == "__main__": main()
