import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase95_688041_valuation import harden_valuation
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
    r=harden_valuation(mode)
    if "--json" in sys.argv:print(json.dumps(r,ensure_ascii=False,indent=2))
    else:print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
