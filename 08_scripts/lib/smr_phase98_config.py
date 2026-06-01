import json,os
from pathlib import Path
def load_config():
    p=Path(__file__).resolve().parent.parent.parent/"config"/"phase98_live_source_monitoring.json"
    with open(p,"r",encoding="utf-8-sig") as fh: return json.load(fh)
def get_sources_to_monitor(): return load_config()["monitoring"]["sources_to_monitor"]
def get_health_levels(): return load_config()["monitoring"]["health_status_levels"]
def is_alerting_enabled(): return load_config()["alerting"]["enabled"]
def get_alert_history_path(): return load_config()["alerting"]["routing"]["alert_history_path"]
def is_external_notification_enabled(): return load_config()["alerting"]["routing"]["external_notification_enabled"]
