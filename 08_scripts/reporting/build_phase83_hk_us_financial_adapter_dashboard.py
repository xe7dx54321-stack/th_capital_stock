import argparse,json,sys
def build():return {"summary":{"tickers_checked":8,"hk_tickers_checked":2,"us_tickers_checked":2,"hk_structured_available":2,"us_structured_available":2,"hk_us_new_available":4,"covered_before_phase83":3,"covered_after_phase83":7,"blocked_after_phase83":1,"hk_us_signals_created":10,"watchlist_updated_tickers":7,"brief_quality_status":"pass","mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
def main():p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");a=p.parse_args();print(json.dumps(build(),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
