import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase92_order_source_exploration import explore_order_sources
from smr_phase92_order_coverage_matrix import build_order_coverage_matrix
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
    exp=explore_order_sources(mode)
    result=build_order_coverage_matrix(exp)
    if "--json" in sys.argv:print(json.dumps(result,ensure_ascii=False,indent=2))
    elif "--markdown" in sys.argv:
        r=result["phase92_order_source_coverage_matrix"]
        print(f"# Order Source Coverage Matrix\n\nTickers: {r['tickers_total']}\nOrder text found: {r['order_text_found']}\nBlocked: {r['blocked']}\nNo text: {r['no_order_text_found']}\n")
        for row in r["coverage_rows"]:print(f"- **{row['ticker']}**: {row['order_contract_coverage_status']}")
    else:print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
