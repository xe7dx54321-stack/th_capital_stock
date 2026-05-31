import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase92_order_source_exploration import explore_order_sources
from smr_phase92_order_text_collector import collect_order_texts
from smr_phase92_order_signal_classifier import classify_order_signals
from smr_phase92_order_evidence_extraction import extract_order_evidence
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
    exp=explore_order_sources(mode)
    texts=collect_order_texts(exp)
    sigs=classify_order_signals(texts)
    result=extract_order_evidence(sigs)
    if "--json" in sys.argv:print(json.dumps(result,ensure_ascii=False,indent=2))
    else:print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
