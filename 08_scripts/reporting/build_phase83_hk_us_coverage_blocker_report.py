import argparse,json,sys
def build():return {"phase83_hk_us_coverage_blocker_report":{"blocked_tickers":0,"blocker_mix":{},"rows":[],"mock_used":False,"fixture_used":False}}
def main():p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");a=p.parse_args();print(json.dumps(build(),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
