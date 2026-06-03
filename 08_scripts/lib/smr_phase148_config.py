import json
from pathlib import Path
def load_phase148_config():
 p=Path(__file__).resolve().parent.parent.parent/'config'/'phase148_candidate_activation.json'
 with open(p,'r',encoding='utf-8') as fh: return json.load(fh)
