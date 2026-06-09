import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
from smr_phase201_clean_evidence_store import build_quality_gate
def main():
    ws = '--write-store' in sys.argv
    r = build_quality_gate(write_store=ws)
    print(json.dumps(r, indent=2, ensure_ascii=False))
if __name__ == '__main__': main()
