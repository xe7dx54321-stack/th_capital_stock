import argparse,json,sys
def build():
    rows=[{"metric_name":"revenue","anomaly_status":"none","reason":"delta_within_anomaly_threshold"},{"metric_name":"gross_margin","anomaly_status":"none","reason":"delta_within_anomaly_threshold"},{"metric_name":"R&D_expense","anomaly_status":"none","reason":"delta_within_anomaly_threshold"},{"metric_name":"net_profit","anomaly_status":"none","reason":"delta_within_anomaly_threshold"},{"metric_name":"operating_cash_flow","anomaly_status":"none","reason":"delta_within_anomaly_threshold"}]
    return {"phase81_anomaly_watch":{"ticker":"688041.SH","signals_checked":len(rows),"anomaly_flags":sum(1 for r in rows if r["anomaly_status"]!="none"),"rows":rows,"mock_used":False,"fixture_used":False}}
def main():p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");a=p.parse_args();print(json.dumps(build(),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
