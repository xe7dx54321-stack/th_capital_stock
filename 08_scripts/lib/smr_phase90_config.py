import json
from pathlib import Path
def load_config():
    p=Path(__file__).resolve().parent.parent.parent/"config"/"phase90_scheduled_automation_delivery.json"
    with open(p,"r",encoding="utf-8-sig") as f:return json.load(f)
def get_schedule():return load_config()["schedule"]
def get_pipeline():return load_config()["pipeline"]
def get_preflight():return load_config()["preflight"]
def get_delivery():return load_config()["delivery"]
def get_notification():return load_config()["notification"]
