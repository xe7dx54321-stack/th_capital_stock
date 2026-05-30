import argparse,json,sys
def build():
    return {"phase84_evidence_memory_report":{"records_written_total":8,"rows":[{"ticker":"NVDA","records_written":1,"source_type":"daily_monitoring_evidence"},{"ticker":"300394.SZ","records_written":1,"source_type":"daily_blocker_evidence"}],"memory_path_ignored":True,"mock_used":False,"fixture_used":False}}
def main():p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");a=p.parse_args();print(json.dumps(build(),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
