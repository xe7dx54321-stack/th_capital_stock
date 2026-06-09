import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
from smr_phase196_ifind_cross_check_bridge import build_bridge_brief
def main():
    an = '--skip-network' not in sys.argv and '--dry-run' not in sys.argv
    r = build_bridge_brief(allow_network=an)
    if '--markdown' in sys.argv:
        print('# Phase196 Cross-check Bridge Brief')
        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(r, indent=2, ensure_ascii=False))
if __name__ == '__main__': main()
