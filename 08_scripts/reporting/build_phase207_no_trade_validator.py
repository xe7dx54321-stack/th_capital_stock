import json,os,sys
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase207_formal_packet_apply_execution import build_no_trade_validator
def main():
    r=build_no_trade_validator()
    print(json.dumps(r,indent=2,ensure_ascii=False))
if __name__=="__main__":main()
