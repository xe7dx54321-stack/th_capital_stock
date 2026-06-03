import json
from pathlib import Path

def load_phase144_config():
    p = Path(__file__).resolve().parent.parent.parent / 'config' / 'phase144_feedback_workflow.json'
    with open(p, 'r', encoding='utf-8') as fh:
        return json.load(fh)
