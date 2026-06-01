import json,os
from pathlib import Path
def load_config():
    p=Path(__file__).resolve().parent.parent.parent/"config"/"phase111_personal_owner_mode.json"
    with open(p,"r",encoding="utf-8") as fh: return json.load(fh)
def is_personal_use_system(): return load_config()["personal_use"]["personal_use_system"]
def is_owner_mode_enabled(): return load_config()["personal_use"]["owner_mode_enabled"]
def is_multi_user_disabled(): return not load_config()["multi_user"]["multi_user_assignment_required"]
def is_paper_execution_disabled(): return not load_config()["execution"]["paper_execution_enabled"]
