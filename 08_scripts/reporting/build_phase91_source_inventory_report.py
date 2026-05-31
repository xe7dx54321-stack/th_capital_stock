import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase91_source_inventory import build_source_inventory
def main():
    inv=build_source_inventory()
    if "--json" in sys.argv:print(json.dumps(inv,ensure_ascii=False,indent=2))
    elif "--markdown" in sys.argv:
        s=inv["phase91_existing_source_inventory"]
        print(f"# Phase 91 Source Inventory\n\nSources inventoried: {s['sources_inventoried']}\n")
        for src in s["sources"]:
            print(f"- **{src['source_id']}**: {src['source_type']} ({src.get('provides','')})")
    else:print(json.dumps(inv,ensure_ascii=False))
if __name__=="__main__":main()
