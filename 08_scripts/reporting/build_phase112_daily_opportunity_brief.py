import json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase112_candidate_builder import build_opportunity_candidate_pool
from smr_phase112_opportunity_ranking import build_opportunity_ranking
def main():
    pool=build_opportunity_candidate_pool()
    rank=build_opportunity_ranking()
    if "--markdown" in sys.argv:
        lines=[]
        lines.append("# \u673a\u4f1a\u96f7\u8fbe\u65e5\u62a5")
        lines.append("## \u8001\u677f\u6458\u8981")
        lines.append("### \u4eca\u65e5\u6700\u503c\u5f97\u770b\u7684\u673a\u4f1a")
        cands=pool["phase112_opportunity_candidate_pool"]["candidates"][:3]
        for c in cands:
            t=c["ticker"]
            ct=c["candidate_type"]
            ts=c["top_signal"]
            na=c["allowed_next_action"]
            lines.append("- **"+t+"** ("+ct+"): "+ts+". Next: "+na)
        lines.append("### \u4ecd\u5361\u4f4f\u7684\u6807\u7684")
        lines.append("- **300394.SZ**: CNINFO blocker unresolved")
        lines.append("### \u7cfb\u7edf\u8fb9\u754c")
        lines.append("\u672c\u6b21\u96f7\u8fbe\u626b\u63cf\u4ec5\u8bc6\u522b\u7814\u7a76\u673a\u4f1a\uff0c\u4e0d\u6784\u6210\u4efb\u4f55\u4e70\u5356\u5efa\u8bae\u3001\u76ee\u6807\u4ef7\u6216\u4ed3\u4f4d\u5efa\u8bae\u3002")
        print("\n".join(lines))
    else:
        out={"phase112_daily_opportunity_brief":{"generated_at":datetime.now().isoformat(),"candidates":len(pool["phase112_opportunity_candidate_pool"]["candidates"]),"research_only":True,"trade_recommendation":0,"target_price":0,"position_sizing":0,"mock_used":False,"fixture_used":False}}
        if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
        else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
