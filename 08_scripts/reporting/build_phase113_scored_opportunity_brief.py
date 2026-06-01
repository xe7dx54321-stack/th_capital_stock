import json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase113_composite_priority_scorer import build_composite_priority_scorer
def main():
    comp=build_composite_priority_scorer()
    if "--markdown" in sys.argv:
        print("# 机会评分日报")
        print("## 老板摘要")
        print("### 今日最值得看的机会")
        for s in comp["phase113_composite_priority_scorer"]["scored_candidates_list"]:
            if s["priority_level"]=="high": print("- **"+s["ticker"]+"** ("+str(s["risk_adjusted_composite"])+"/100): 高优先级研究机会")
        print("### 系统边界")
        print("本次评分为研究优先级，不构成任何买卖建议、目标价或仓位建议。")
    else:
        out={"phase113_scored_opportunity_brief":{"generated_at":datetime.now().isoformat(),"scored_candidates":comp["phase113_composite_priority_scorer"]["scored_candidates"],"research_only":True,"trade_recommendation":0,"target_price":0,"position_sizing":0,"mock_used":False,"fixture_used":False}}
        if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
        else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
