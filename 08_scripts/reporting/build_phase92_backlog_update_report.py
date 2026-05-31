import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase92_backlog_update import build_backlog_update
def main():
    result=build_backlog_update()
    if "--json" in sys.argv:print(json.dumps(result,ensure_ascii=False,indent=2))
    elif "--markdown" in sys.argv:
        r=result["phase92_backlog_update"]
        print(f"# Backlog Update\n\nItems: {r['backlog_items']}\nPhase93: {r['phase93_recommendation']}\n")
        for b in r["backlog"]:print(f"{b['rank']}. **{b['gap']}**: {b['post_phase92_status']}")
    else:print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
