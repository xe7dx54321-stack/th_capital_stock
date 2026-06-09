import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from smr_phase203_hk_us_evidence_chain_expansion import build_additive_source_audit
def main():
    r = build_additive_source_audit()
    print(json.dumps(r, indent=2, ensure_ascii=False))
if __name__ == "__main__": main()
