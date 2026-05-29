#!/usr/bin/env python3
'''Evidence memory schema loader.'''
import json
from pathlib import Path
from typing import Any

SCHEMA_PATH = Path(__file__).resolve().parents[2] / 'config' / 'evidence_memory_schema.json'

def load_schema() -> dict[str, Any]:
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_record(rec: dict) -> tuple[bool, list[str]]:
    schema = load_schema()
    required = schema.get('required_fields', [])
    missing = [f for f in required if f not in rec or rec[f] is None]
    return len(missing) == 0, missing

def validate_strength(s: str) -> bool:
    schema = load_schema()
    return s in schema.get('evidence_strength_enum', [])

def validate_usage(u: str) -> bool:
    schema = load_schema()
    return u in schema.get('allowed_usage_enum', [])
