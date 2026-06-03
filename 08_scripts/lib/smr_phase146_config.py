import json
from pathlib import Path
def load_phase146_config():
    p = Path(__file__).resolve().parent.parent.parent / 'config' / 'phase146_agent_memory_queue.json'
    with open(p, 'r', encoding='utf-8') as fh: return json.load(fh)
