import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from smr_phase205_unified_evidence_packet_coverage_refresh import build_300394_source_limitation_report
def main():
    r = build_300394_source_limitation_report()
    print(json.dumps(r, indent=2, ensure_ascii=False))
if __name__ == "__main__": main()
