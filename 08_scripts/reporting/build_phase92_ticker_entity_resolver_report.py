import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase92_ticker_entity_resolver import build_ticker_entity_resolver
def main():
    result=build_ticker_entity_resolver()
    if "--json" in sys.argv:print(json.dumps(result,ensure_ascii=False,indent=2))
    elif "--markdown" in sys.argv:
        r=result["phase92_ticker_entity_resolver"]
        print(f"# Ticker Entity Resolver\n\nTickers resolved: {r['tickers_resolved']}\n")
        for e in r["entities"]:print(f"- **{e['ticker']}**: {e['display_name']} [{'BLOCKED' if e['blocked'] else 'resolved'}]")
    else:print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
