import argparse,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
def main():
    from smr_phase98_endpoint_heartbeat import run_heartbeat_probe
    from smr_phase98_source_staleness_monitor import monitor_source_staleness
    from smr_phase98_source_reliability_decay import compute_reliability_decay
    from smr_phase98_daily_source_health_board import build_health_board
    hb=run_heartbeat_probe("dry-run");st=monitor_source_staleness();rd=compute_reliability_decay()
    r=build_health_board(hb,st,rd)
    if "--json" in sys.argv:print(json.dumps(r,ensure_ascii=False,indent=2))
    else:print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
