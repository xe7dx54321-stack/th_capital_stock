import json
from pathlib import Path
def load_phase150_config():
 p=Path(__file__).resolve().parent.parent.parent/'config'/'phase150_watchlist_tiering.json'
 with open(p,'r',encoding='utf-8') as fh: return json.load(fh)
