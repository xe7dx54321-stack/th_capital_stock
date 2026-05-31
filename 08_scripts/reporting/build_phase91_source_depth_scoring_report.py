import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase91_depth_freshness_reliability_backlog import build_source_depth_scores
def main():
    result=build_source_depth_scores()
    if "--json" in sys.argv:print(json.dumps(result,ensure_ascii=False,indent=2))
    elif "--markdown" in sys.argv:
        r=result["phase91_source_depth_scoring"]
        print(f"# Source Depth Scoring\n\nSources scored: {r['sources_scored']}\n")
        for s in sorted(r["scores"],key=lambda x:-x["depth_score"]):
            print(f"- **{s['source_id']}**: depth={s['depth_score']} ({s['score_rationale']})")
    else:print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
