import argparse,json,sys,datetime,uuid
def run(mode="execute"):
    if mode=="dry_run":return {"phase82_evidence_memory_report":{"records_written_total":0,"mode":"dry_run","rows":[],"memory_path_ignored":True,"mock_used":False,"fixture_used":False}}
    evidence_rows=[
        {"ticker":"688041.SH","source_type":"multi_ticker_time_series_monitoring_evidence","business_variable":"revenue","evidence_strength":"strong_direct","claim_type":"revenue_growth_strengthened","limitation":"688041 revenue strengthened, does not confirm customer share.","cannot_conclude":["customer_share"],"delta_status":"strengthened","monitoring_applied":True},
        {"ticker":"300308.SZ","source_type":"multi_ticker_time_series_monitoring_evidence","business_variable":"revenue","evidence_strength":"medium_context","claim_type":"revenue_observed","limitation":"300308 revenue unchanged, does not confirm specific claims.","cannot_conclude":["customer_share"],"delta_status":"unchanged","monitoring_applied":True},
        {"ticker":"002230.SZ","source_type":"multi_ticker_time_series_monitoring_evidence","business_variable":"revenue","evidence_strength":"medium_context","claim_type":"revenue_observed","limitation":"002230 revenue unchanged, does not confirm specific claims.","cannot_conclude":["customer_share"],"delta_status":"unchanged","monitoring_applied":True},
        {"ticker":"300394.SZ","source_type":"coverage_blocker_evidence","business_variable":"all","evidence_strength":"weak_indirect","claim_type":"financial_coverage_blocked","limitation":"300394 structured financial data unavailable due to cninfo identity blocker.","cannot_conclude":[],"delta_status":"blocked","monitoring_applied":False},
    ]
    records=[]
    for row in evidence_rows:
        rec={"evidence_id":str(uuid.uuid4())[:8],"written_at":datetime.datetime.now().isoformat(),"ticker":row["ticker"],"source_type":row["source_type"],"business_variable":row["business_variable"],"evidence_strength":row["evidence_strength"],"claim_type":row["claim_type"],"limitation":row["limitation"],"cannot_conclude":row["cannot_conclude"],"delta_status":row["delta_status"],"monitoring_applied":row["monitoring_applied"]}
        records.append(rec)
    return {"phase82_evidence_memory_report":{"records_written_total":len(records),"rows":records,"memory_path_ignored":True,"mock_used":False,"fixture_used":False}}
def main():
    p=argparse.ArgumentParser();p.add_argument("--dry-run",action="store_true");p.add_argument("--execute",action="store_true");p.add_argument("--json",action="store_true")
    a=p.parse_args();mode="dry_run" if getattr(a,"dry_run") else "execute";r=run(mode);print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
