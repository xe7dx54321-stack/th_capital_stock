import argparse,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase98_config import load_config
def main():
    cfg=load_config()
    out={"phase98_config":{"phase":cfg["phase"],"sources_to_monitor":len(cfg["monitoring"]["sources_to_monitor"]),"heartbeat_enabled":cfg["monitoring"]["heartbeat"]["enabled"],"schema_drift_enabled":cfg["monitoring"]["schema_drift"]["enabled"],"alerting_enabled":cfg["alerting"]["enabled"],"external_notification_enabled":cfg["alerting"]["routing"]["external_notification_enabled"],"mock_used":False,"fixture_used":False}}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
