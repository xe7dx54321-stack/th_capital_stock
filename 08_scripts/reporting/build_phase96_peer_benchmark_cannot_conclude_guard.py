import argparse,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_phase96_evidence_loader import load_phase92_95_evidence
from smr_phase96_cannot_conclude_guard import run_peer_benchmark_cannot_conclude_guard

def build():
    ev = load_phase92_95_evidence()
    return run_peer_benchmark_cannot_conclude_guard(ev['phase96_evidence_loader']['records'])

def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true");args=p.parse_args()
    r=build()
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
