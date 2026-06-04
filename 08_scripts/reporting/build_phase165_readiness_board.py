import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
def main(mode="json"):
    from smr_phase165_readiness import analyze_not_ready_reasons, TICKERS
    analysis = analyze_not_ready_reasons()
    rows = analysis["phase165_not_ready_analyzer"]["results"]
    output = {"phase165_readiness_board":{"total":len(rows),"not_ready":sum(1 for r in rows if r["not_ready"]),"ready":sum(1 for r in rows if not r["not_ready"]),"repair_not_approval":True,"rows":[{"ticker":r["ticker"],"primary_blocker":r["primary_blocker"],"blocker_count":r["blocker_count"]} for r in rows],"mock_used":False,"fixture_used":False}}
    if mode=="markdown":
        print("# Readiness Repair Board")
        print(f"| Ticker | Primary Blocker | Blockers |")
        print(f"|--------|-----------------|----------|")
        for r in output["phase165_readiness_board"]["rows"]: print(f"| {r['ticker']} | {r['primary_blocker']} | {r['blocker_count']} |")
    else: print(json.dumps(output, ensure_ascii=False, indent=2))
if __name__=="__main__": main("markdown" if "--markdown" in sys.argv else "json")
