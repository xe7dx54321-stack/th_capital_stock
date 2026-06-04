import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
def main(mode="json"):
    from smr_phase163_target_planner import plan_live_execute_targets
    targets = plan_live_execute_targets()["phase163_target_planner"]["targets"]
    rows = [{"ticker": t["ticker"], "market": t["market"], "sector": t["sector"], "priority": t["priority"], "snapshot": "deferred"} for t in targets]
    output = {"phase163_live_hydration_board": {"targets_total": len(targets), "deferred": len(targets), "live": 0, "markets": {"US": 13}, "snapshot_not_approval": True, "rows": rows, "mock_used": False, "fixture_used": False}}
    if mode == "markdown":
        print("# Phase163 Live Hydration Board")
        print(f"| Ticker | Market | Sector | Priority | Snapshot |")
        print(f"|--------|--------|--------|----------|----------|")
        for r in rows: print(f"| {r['ticker']} | {r['market']} | {r['sector']} | {r['priority']} | {r['snapshot']} |")
    else: print(json.dumps(output, ensure_ascii=False, indent=2))
if __name__ == "__main__": main("markdown" if "--markdown" in sys.argv else "json")
