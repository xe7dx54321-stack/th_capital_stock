import argparse,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase98_endpoint_heartbeat import run_heartbeat_probe
from smr_phase99_fallback_source_selector import select_fallback_sources
def main(): hb=run_heartbeat_probe("dry-run");r=select_fallback_sources(hb);print(json.dumps(r,ensure_ascii=False,indent=2) if "--json" in sys.argv else json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
