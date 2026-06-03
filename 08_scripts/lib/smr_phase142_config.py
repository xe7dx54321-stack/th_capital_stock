import json
from pathlib import Path

def load_phase142_config():
    p = Path(__file__).resolve().parent.parent.parent / 'config' / 'phase142_ticker_detail_pages.json'
    with open(p, 'r', encoding='utf-8') as fh:
        return json.load(fh)
