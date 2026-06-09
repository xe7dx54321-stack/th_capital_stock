import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
from smr_phase199_real_cross_source_verification import build_verification_board
def main():
    an = '--skip-network' not in sys.argv and '--dry-run' not in sys.argv
    r = build_verification_board(allow_network=an)
    print(json.dumps(r, indent=2, ensure_ascii=False))
if __name__ == '__main__': main()
