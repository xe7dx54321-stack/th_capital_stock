import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase92_order_source_registry import build_order_source_registry
def main():
    result=build_order_source_registry()
    if "--json" in sys.argv:print(json.dumps(result,ensure_ascii=False,indent=2))
    elif "--markdown" in sys.argv:
        r=result["phase92_order_source_registry"]
        print(f"# Order Source Registry\n\nSources registered: {r['order_sources_registered']}\n")
        for s in r["sources"]:print(f"- **{s['source_id']}**: {s['source_type']} ({s['market']})")
    else:print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
