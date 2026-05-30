#!/usr/bin/env python3
import json
from pathlib import Path
SCHEMA_PATH = Path(__file__).resolve().parents[2] / "config" / "phase79_quantitative_metric_schema.json"
def load_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8-sig") as f:
        return json.load(f)
def get_metric_aliases():
    schema = load_schema()
    result = {}
    for m in schema.get("metrics", []):
        result[m["metric_name"]] = m.get("aliases", [])
    return result
def get_metric_cannot_conclude():
    schema = load_schema()
    return {m["metric_name"]: m.get("cannot_conclude", []) for m in schema.get("metrics", [])}
def get_metric_count():
    schema = load_schema()
    return len(schema.get("metrics", []))
