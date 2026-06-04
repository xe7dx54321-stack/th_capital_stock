# Phase175 cannot-conclude guard report
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase175_guard import build_phase175_cannot_conclude_guard

def build_cc_guard_report():
    return build_phase175_cannot_conclude_guard()

if __name__=="__main__":
    import argparse
    p = argparse.ArgumentParser(); p.add_argument("--json",action="store_true")
    args = p.parse_args()
    print(json.dumps(build_cc_guard_report(),ensure_ascii=False,indent=2))
