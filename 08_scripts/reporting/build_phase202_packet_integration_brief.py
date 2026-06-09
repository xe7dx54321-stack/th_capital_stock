import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from smr_phase202_evidence_packet_integration_preview import build_packet_integration_brief
def main():
    r = build_packet_integration_brief()
    print(json.dumps(r, indent=2, ensure_ascii=False))
if __name__ == "__main__": main()
