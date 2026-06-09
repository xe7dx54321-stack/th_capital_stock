import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
from smr_phase197_cn_a_web_scout_expansion import build_scout_brief
def main():
    an = '--skip-network' not in sys.argv and '--dry-run' not in sys.argv
    r = build_scout_brief(allow_network=an)
    if '--markdown' in sys.argv:
        print('# Phase197 CN_A Web Scout Brief')
    print(json.dumps(r, indent=2, ensure_ascii=False))
if __name__ == '__main__': main()
