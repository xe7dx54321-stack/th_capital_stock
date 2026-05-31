import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase91_ticker_source_profile import build_ticker_source_profiles
def main():
    result=build_ticker_source_profiles()
    if "--json" in sys.argv:print(json.dumps(result,ensure_ascii=False,indent=2))
    elif "--markdown" in sys.argv:
        r=result["phase91_ticker_source_profile"]
        print(f"# Ticker Source Profiles\n\nTickers profiled: {r['tickers_profiled']}\nAvg depth: {r['average_source_depth_score']}\n")
        for p in r["profiles"]:
            print(f"- **{p['ticker']}** ({p['market']}): depth={p.get('source_depth_score',0)}, status={p.get('profile_status','')}")
    else:print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
