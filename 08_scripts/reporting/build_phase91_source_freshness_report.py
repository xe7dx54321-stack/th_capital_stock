import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase91_depth_freshness_reliability_backlog import build_freshness_audit
def main():
    result=build_freshness_audit()
    if "--json" in sys.argv:print(json.dumps(result,ensure_ascii=False,indent=2))
    elif "--markdown" in sys.argv:
        r=result["phase91_source_freshness_reality_audit"]
        print(f"# Source Freshness Audit\n\nSources audited: {r['sources_audited']}\n")
        for s in r["freshness_records"]:
            print(f"- **{s['source_id']}**: freshness={s.get('last_known_fresh_data','')}, risk={s.get('staleness_risk','')}")
    else:print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
