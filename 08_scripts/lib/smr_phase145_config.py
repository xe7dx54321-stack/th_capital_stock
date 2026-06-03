import json
from pathlib import Path

def load_phase145_config():
    p = Path(__file__).resolve().parent.parent.parent / 'config' / 'phase145_agent_orchestration.json'
    with open(p, 'r', encoding='utf-8') as fh:
        return json.load(fh)
