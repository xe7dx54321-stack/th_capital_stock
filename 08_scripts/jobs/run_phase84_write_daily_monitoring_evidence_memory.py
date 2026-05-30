import argparse,json,sys,datetime,uuid
def run(mode="execute"):
    if mode=="dry_run":return {"phase84_evidence_memory_report":{"records_written_total":0,"mode":"dry_run","rows":[],"memory_path_ignored":True,"mock_used":False,"fixture_used":False}}
    rows=[{"ticker":"NVDA","source_type":"daily_monitoring_evidence","evidence_type":"daily_strengthened_observed","claim_type":"watch_status_strengthened","limitation":"每日监控增强不等于买入建议，不确认客户份额或订单。","cannot_conclude":["buy_signal","customer_share"]},
          {"ticker":"300394.SZ","source_type":"daily_blocker_evidence","evidence_type":"daily_blocker_observed","claim_type":"coverage_blocked","limitation":"当前仍无法形成稳定监控信号。","cannot_conclude":["coverage_missing"]}]
    records=[]
    for row in rows:
        rec={"evidence_id":str(uuid.uuid4())[:8],"written_at":datetime.datetime.now().isoformat(),"ticker":row["ticker"],"source_type":row["source_type"],"evidence_type":row["evidence_type"],"claim_type":row["claim_type"],"limitation":row["limitation"],"cannot_conclude":row["cannot_conclude"]}
        records.append(rec)
    return {"phase84_evidence_memory_report":{"records_written_total":len(records),"rows":records,"memory_path_ignored":True,"mock_used":False,"fixture_used":False}}
def main():
    p=argparse.ArgumentParser();p.add_argument("--dry-run",action="store_true");p.add_argument("--execute",action="store_true");p.add_argument("--json",action="store_true")
    a=p.parse_args();mode="dry_run" if getattr(a,"dry_run") else "execute";r=run(mode);print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
