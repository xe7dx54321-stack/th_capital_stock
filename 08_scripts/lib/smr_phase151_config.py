import json
from pathlib import Path
def load_phase151_config():
 p=Path(__file__).resolve().parent.parent.parent/'config'/'phase151_auto_candidate_discovery.json'
 with open(p,'r',encoding='utf-8') as fh: return json.load(fh)
