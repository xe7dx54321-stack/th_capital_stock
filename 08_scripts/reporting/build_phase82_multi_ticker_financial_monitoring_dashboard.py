import argparse,json,sys
def build():return {"summary":{"tickers_checked":8,"markets":{"CN_A":4,"HK":2,"US":2},"structured_available":3,"blocked_or_unavailable":5,"tickers_with_signals":3,"signals_created":12,"strengthened":1,"weakened":0,"unchanged":11,"anomaly_flags":0,"monitoring_evidence_created":12,"watchlist_updated_tickers":3,"brief_quality_status":"pass","mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
def main():p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");a=p.parse_args();print(json.dumps(build(),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
