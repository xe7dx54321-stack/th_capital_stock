import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase91_source_inventory import build_source_inventory
from smr_phase91_source_reality_classifier import classify_sources
def main():
    inv=build_source_inventory()
    result=classify_sources(inv)
    if "--json" in sys.argv:print(json.dumps(result,ensure_ascii=False,indent=2))
    elif "--markdown" in sys.argv:
        r=result["phase91_source_reality_classifier"]
        print(f"# Source Reality Classification\n\nSources classified: {r['sources_classified']}\n")
        for k,v in r["classification_summary"].items():
            if v>0:print(f"- **{k}**: {v}")
    else:print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
