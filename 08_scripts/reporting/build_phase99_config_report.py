import argparse,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase99_config import *
def main():
    r={}
    if "build" in repr(globals()):
        exec("global r; r=build_"+'config'+"()")
    elif "run" in repr(globals()):
        exec("global r; r=run_"+'config'+"('dry-run')")
    elif "map" in repr(globals()):
        exec("global r; r=map_"+'config'+"({})")
    elif "select" in repr(globals()):
        exec("global r; r=select_"+'config'+"({})")
    elif "classify" in repr(globals()):
        exec("global r; r=classify_"+'config'+"({},{},{},{},{},{})")
    elif "update" in repr(globals()):
        exec("global r; r=update_"+'config'+"({})")
    elif "refresh" in repr(globals()):
        exec("global r; r=refresh_"+'config'+"({},{})")
    if "--json" in sys.argv:print(json.dumps(r,ensure_ascii=False,indent=2))
    else:print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
