import json,os,sys
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase206_formal_packet_apply_owner_approval_workflow import build_additive_source_audit_v4
def main():
    r=build_additive_source_audit_v4()
    print(json.dumps(r,indent=2,ensure_ascii=False))
if __name__=="__main__":main()
