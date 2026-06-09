import json,os,sys
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase207_formal_packet_apply_execution import build_post_apply_verification
def main():
    ac="--apply-confirmed" in sys.argv
    wp="--write-formal-packet" in sys.argv
    r=build_post_apply_verification(ac,wp)
    print(json.dumps(r,indent=2,ensure_ascii=False))
if __name__=="__main__":main()
