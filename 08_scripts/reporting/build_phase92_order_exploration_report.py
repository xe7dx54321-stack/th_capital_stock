import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase92_order_source_exploration import explore_order_sources
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    result=explore_order_sources(mode)
    if "--json" in sys.argv:print(json.dumps(result,ensure_ascii=False,indent=2))
    elif "--markdown" in sys.argv:
        r=result["phase92_order_source_exploration"]
        print(f"# Order Source Exploration\n\nMode: {r['mode']}\nSources attempted: {r['sources_attempted']}\nText units: {r['text_units_collected']}\nKeyword hits: {r['order_keyword_hits']}\n")
        for tr in r["ticker_results"]:print(f"- **{tr['ticker']}**: hits={tr['keyword_hits']}, texts={tr['total_text_units']}")
    else:print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
