import json
from pathlib import Path
def load_phase149_config():
 p=Path(__file__).resolve().parent.parent.parent/'config'/'phase149_agent_instructions.json'
 with open(p,'r',encoding='utf-8') as fh: return json.load(fh)
