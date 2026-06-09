import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from smr_phase205_unified_evidence_packet_coverage_refresh import build_post_apply_checklist_preview
def main():
    r = build_post_apply_checklist_preview()
    print(json.dumps(r, indent=2, ensure_ascii=False))
if __name__ == "__main__": main()
