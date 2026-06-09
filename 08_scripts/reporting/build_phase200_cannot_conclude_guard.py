import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
from smr_phase200_dirty_to_clean_classifier import build_cannot_conclude_guard
def main():
    an = '--skip-network' not in sys.argv and '--dry-run' not in sys.argv
    r = build_cannot_conclude_guard(allow_network=an)
    print(json.dumps(r, indent=2, ensure_ascii=False))
if __name__ == '__main__': main()
