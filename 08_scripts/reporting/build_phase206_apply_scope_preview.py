import json,os,sys
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase206_formal_packet_apply_owner_approval_workflow import build_apply_scope_preview
def main():
    r=build_apply_scope_preview()
    print(json.dumps(r,indent=2,ensure_ascii=False))
if __name__=="__main__":main()
