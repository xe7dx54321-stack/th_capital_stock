import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from smr_phase204_hk_us_real_verification_store_backfill import build_300394_report

def main():
    r = build_300394_report()
    print(json.dumps(r, indent=2, ensure_ascii=False))
if __name__ == "__main__": main()
