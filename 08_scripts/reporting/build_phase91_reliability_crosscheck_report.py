import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase91_depth_freshness_reliability_backlog import build_reliability_crosscheck
def main():
    result=build_reliability_crosscheck()
    if "--json" in sys.argv:print(json.dumps(result,ensure_ascii=False,indent=2))
    elif "--markdown" in sys.argv:
        r=result["phase91_reliability_vs_reality_crosscheck"]
        print(f"# Reliability vs Reality Crosscheck\n\nClaims: {r['claims_checked']}, Gaps: {r['reliability_gaps_found']}\n")
        for c in r["crosscheck_records"]:
            flag="!!GAP!!" if c["reliability_gap"] else "OK"
            print(f"- {flag} {c['registry_claim'][:80]}")
    else:print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
