import json,os,sys
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase206_formal_packet_apply_owner_approval_workflow import build_final_pre_apply_checklist
def main():
    r=build_final_pre_apply_checklist()
    print(json.dumps(r,indent=2,ensure_ascii=False))
if __name__=="__main__":main()
