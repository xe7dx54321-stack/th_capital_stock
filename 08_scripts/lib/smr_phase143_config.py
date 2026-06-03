import json
from pathlib import Path

def load_phase143_config():
    p = Path(__file__).resolve().parent.parent.parent / 'config' / 'phase143_cross_link_navigation.json'
    with open(p, 'r', encoding='utf-8') as fh:
        return json.load(fh)
