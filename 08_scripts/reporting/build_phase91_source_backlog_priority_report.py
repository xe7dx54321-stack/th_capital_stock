import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase91_depth_freshness_reliability_backlog import build_backlog_priority
def main():
    result=build_backlog_priority()
    if "--json" in sys.argv:print(json.dumps(result,ensure_ascii=False,indent=2))
    elif "--markdown" in sys.argv:
        r=result["phase91_source_backlog_priority"]
        print(f"# Source Backlog Priority\n\nItems: {r['backlog_items']}\n\n{r['phase92_96_recommendation']}\n")
        for p in r["priorities"]:
            print(f"{p['rank']}. **{p['gap']}** [{p['priority']}] -> {p['phase_target']}, effort={p['estimated_effort']}")
    else:print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
