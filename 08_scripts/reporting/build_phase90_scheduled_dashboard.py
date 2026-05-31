import argparse,json,sys
from pathlib import Path;L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase90_integration import build_scheduled_integration
def build():
    r=build_scheduled_integration();d=r["phase90_scheduled_integration"]
    return {"summary":{"preflight":d["preflight_status"],"checks":d["preflight_checks"],"scheduler_mode":d["scheduler_commands"],"artifacts":d["delivery_artifacts"],"failure_scenarios":d["failure_scenarios"],"notification_adapters":d["notification_adapters_enabled"],"watch_only":True,"mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
def main():p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");a=p.parse_args();print(json.dumps(build(),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
