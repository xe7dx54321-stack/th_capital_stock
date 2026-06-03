import json
from pathlib import Path
def load_phase158_config():
    p = Path(__file__).resolve().parent.parent.parent / "config" / "phase158_owner_decision_ui.json"
    try:
        with open(p, "r", encoding="utf-8") as fh: return json.load(fh)
    except Exception:
        with open(p, "r", encoding="utf-8-sig") as fh: return json.load(fh)
