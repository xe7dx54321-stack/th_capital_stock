import argparse,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
def main():
    from smr_phase98_source_staleness_monitor import monitor_source_staleness
    r=monitor_source_staleness()
    if "--json" in sys.argv:print(json.dumps(r,ensure_ascii=False,indent=2))
    else:print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
