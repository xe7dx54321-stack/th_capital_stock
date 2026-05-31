import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase91_dimension_coverage import build_dimension_coverage_matrix
def main():
    result=build_dimension_coverage_matrix()
    r=result["phase91_information_dimension_coverage_matrix"]
    if "--json" in sys.argv:print(json.dumps(r,ensure_ascii=False,indent=2))
    elif "--markdown" in sys.argv:
        print(f"# Information Dimension Coverage\n\nDimensions audited: {r['dimensions_audited']}\n")
        for d in r["dimension_coverage"]:
            print(f"- **{d['dimension']}**: {d['coverage']}")
    else:print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
