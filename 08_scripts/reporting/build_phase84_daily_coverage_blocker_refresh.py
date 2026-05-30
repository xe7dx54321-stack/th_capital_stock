import argparse,json,sys
def build():
    return {"phase84_daily_coverage_blocker_refresh":{"blocked_tickers":1,"rows":[{"ticker":"300394.SZ","blocker":"cninfo_org_id_missing","most_specific_blocker":"cninfo_org_id_missing_and_known_url_not_usable","allowed_next_action":"manual_cninfo_identity_resolution_or_alternative_source"}],"mock_used":False,"fixture_used":False}}
def main():p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");a=p.parse_args();print(json.dumps(build(),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
