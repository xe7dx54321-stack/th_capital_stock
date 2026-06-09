import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

from smr_phase207b_owner_approval_simulation import build_quality_gate


def main():
    simulated_packet_written = "--simulated-packet-written" in sys.argv
    print(json.dumps(build_quality_gate(simulated_packet_written), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
