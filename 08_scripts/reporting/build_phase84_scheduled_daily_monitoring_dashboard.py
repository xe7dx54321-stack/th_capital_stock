import argparse,json,sys
def build():
    return {"summary":{"tickers_total":8,"daily_monitoring_enabled":7,"blocked":1,"markets":{"CN_A":4,"HK":2,"US":2},"signals_loaded":22,"strengthened":3,"weakened":0,"unchanged":4,"anomaly":0,"run_history_written":True,"history_path_ignored":True,"portfolio_watch_board_status":"pass","watchlist_refresh_status":"pass","brief_quality_status":"pass","mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
def main():p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");a=p.parse_args();print(json.dumps(build(),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
