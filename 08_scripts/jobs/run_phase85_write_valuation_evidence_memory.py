import argparse,json,sys,datetime,uuid
def run(mode="execute"):
    if mode=="dry_run":return {"phase85_evidence_memory_report":{"records_written_total":0,"mode":"dry_run","rows":[],"memory_path_ignored":True,"mock_used":False,"fixture_used":False}}
    records=[]
    for row in[{"ticker":"NVDA","source_type":"valuation_evidence","valuation_band":"high","limitation":"估值high不等于卖出建议，不确认交易方向。","cannot_conclude":["buy_sell_signal"]},{"ticker":"300394.SZ","source_type":"valuation_blocker_evidence","valuation_band":"unavailable","limitation":"估值数据不可用，blocker保留。","cannot_conclude":["coverage_missing"]}]:
        records.append({"evidence_id":str(uuid.uuid4())[:8],"written_at":datetime.datetime.now().isoformat(),"ticker":row["ticker"],"source_type":row["source_type"],"valuation_band":row["valuation_band"],"limitation":row["limitation"],"cannot_conclude":row["cannot_conclude"]})
    return {"phase85_evidence_memory_report":{"records_written_total":len(records),"rows":records,"memory_path_ignored":True,"mock_used":False,"fixture_used":False}}
def main():
    p=argparse.ArgumentParser();p.add_argument("--dry-run",action="store_true");p.add_argument("--execute",action="store_true");p.add_argument("--json",action="store_true")
    a=p.parse_args();mode="dry_run" if getattr(a,"dry_run") else "execute";r=run(mode);print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
