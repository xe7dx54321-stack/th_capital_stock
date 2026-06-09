import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
from smr_phase200_dirty_to_clean_classifier import build_classifier_brief
def main():
    an = '--skip-network' not in sys.argv and '--dry-run' not in sys.argv
    r = build_classifier_brief(allow_network=an)
    if '--markdown' in sys.argv: print('# Phase200 Classifier Brief')
    print(json.dumps(r, indent=2, ensure_ascii=False))
if __name__ == '__main__': main()
