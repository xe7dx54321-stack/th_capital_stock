import json
from pathlib import Path

def load_phase162_config():
    p = Path(__file__).resolve().parent.parent.parent / "config" / "phase162_real_network_candidate_hydration.json"
    try:
        with open(p, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        with open(p, "r", encoding="utf-8-sig") as fh:
            return json.load(fh)
