import json
from pathlib import Path
def load_phase147_config():
 p=Path(__file__).resolve().parent.parent.parent/'config'/'phase147_ticker_onboarding.json'
 with open(p,'r',encoding='utf-8') as fh: return json.load(fh)
