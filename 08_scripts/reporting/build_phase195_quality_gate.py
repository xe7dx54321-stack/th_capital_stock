import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
from smr_phase195_ifind_dirty_source_adapter import build_quality_gate
def main():
    an = '--skip-network' not in sys.argv and '--dry-run' not in sys.argv
    r = build_quality_gate(allow_network=an)
    print(json.dumps(r, indent=2, ensure_ascii=False))
if __name__ == '__main__': main()
