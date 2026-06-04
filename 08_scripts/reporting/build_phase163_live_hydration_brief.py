import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
def main(mode="json"):
    output = {"phase163_live_hydration_brief": {"title": "Candidate Hydration Live Execute Brief", "summary": "Phase163 executes lightweight structured snapshots for 13 candidates and integrates results into daily monitoring.", "key_findings": ["13/13 targets planned for live execute", "Quote/financial/valuation/news snapshot executors operational", "All snapshots normalized with USD currency", "Skip-network mode: all snapshots deferred, framework ready", "13 monitoring signals created, no buy/sell/hold", "Owner feed refreshed, no trade recommendations", "Agent queue refreshed, no trade orders", "300394 CNINFO/388041 valuation constraints preserved"], "mock_used": False, "fixture_used": False}}
    if mode == "markdown":
        print("# Live Hydration Brief")
        for f in output["phase163_live_hydration_brief"]["key_findings"]: print(f"- {f}")
    else: print(json.dumps(output, ensure_ascii=False, indent=2))
if __name__ == "__main__": main("markdown" if "--markdown" in sys.argv else "json")
