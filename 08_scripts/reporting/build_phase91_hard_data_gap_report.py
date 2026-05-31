import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase91_dimension_coverage import build_dimension_coverage_matrix
def main():
    result=build_dimension_coverage_matrix()
    gap_rpt=result["phase91_hard_data_gap_report"]
    if "--json" in sys.argv:print(json.dumps(gap_rpt,ensure_ascii=False,indent=2))
    elif "--markdown" in sys.argv:
        print(f"# Hard Data Gap Report\n\nTotal gaps: {gap_rpt['total_gaps']}\n")
        for g in gap_rpt["gaps"]:
            print(f"- **{g['dimension']}**: gap={g['gap_count']}, blocked={g['blocked_count']}, priority={g['priority_for_phase92_96']}")
            print(f"  affected: {g['affected_tickers']}")
    else:print(json.dumps(gap_rpt,ensure_ascii=False))
if __name__=="__main__":main()
