import json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase92_order_source_exploration import explore_order_sources
from smr_phase92_order_text_collector import collect_order_texts
from smr_phase92_order_signal_classifier import classify_order_signals
from smr_phase92_order_evidence_extraction import extract_order_evidence
from smr_phase92_order_quality_gate import run_quality_gate

MEMORY_PATH = "09_runbooks/generated/phase92_order_evidence_memory.jsonl"

def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    
    exp=explore_order_sources(mode)
    texts=collect_order_texts(exp)
    sigs=classify_order_signals(texts)
    ev=extract_order_evidence(sigs)
    gate=run_quality_gate(ev)
    
    records_written = 0
    if mode=="execute":
        os.makedirs(os.path.dirname(MEMORY_PATH),exist_ok=True)
        with open(MEMORY_PATH,"a",encoding="utf-8") as f:
            for rec in ev["phase92_order_evidence_extraction"]["evidence_records"]:
                for item in rec["evidence_items"]:
                    entry={"timestamp":datetime.now().isoformat(),"phase":"phase92","ticker":rec["ticker"],"market":rec["market"],"evidence":item}
                    f.write(json.dumps(entry,ensure_ascii=False)+"\n")
                    records_written += 1
    
    out={"phase92_evidence_memory":{"mode":mode,"records_written_total":records_written,"memory_path":MEMORY_PATH,"memory_path_ignored":True,"mock_used":False,"fixture_used":False}}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
