import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase92_order_source_exploration import explore_order_sources
from smr_phase92_order_text_collector import collect_order_texts
from smr_phase92_order_signal_classifier import classify_order_signals
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
    exp=explore_order_sources(mode)
    texts=collect_order_texts(exp)
    result=classify_order_signals(texts)
    if "--json" in sys.argv:print(json.dumps(result,ensure_ascii=False,indent=2))
    elif "--markdown" in sys.argv:
        r=result["phase92_order_signal_classifier"]
        print(f"# Order Signal Classification\n\nTotal: {r['total_signals_classified']}\n")
        for st,c in r["signal_type_counts"].items():
            if c>0:print(f"- **{st}**: {c}")
    else:print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
