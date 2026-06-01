import argparse,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
def main():
    from smr_phase98_refresh_failure_detector import detect_refresh_failure
    from smr_phase98_endpoint_heartbeat import run_heartbeat_probe
    hb=run_heartbeat_probe("dry-run")
    r=detect_refresh_failure(hb)
    if "--json" in sys.argv:print(json.dumps(r,ensure_ascii=False,indent=2))
    else:print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
