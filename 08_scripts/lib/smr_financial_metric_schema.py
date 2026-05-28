#!/usr/bin/env python3
import json
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parents[2] / 'config' / 'financial_metric_schema.json'

def load_schema():
    if SCHEMA_PATH.exists():
        return json.loads(SCHEMA_PATH.read_text(encoding='utf-8'))
    return {}

def get_generic_metrics():
    s = load_schema()
    return s.get('metric_groups', {})

def get_period_types():
    s = load_schema()
    return s.get('period_types', [])

def get_calculated_metrics():
    s = load_schema()
    return s.get('calculated_metrics', [])

def build_schema_report():
    s = load_schema()
    return {'financial_metric_schema': {'metric_groups': s.get('metric_groups', {}), 'period_types': s.get('period_types', []), 'calculated_metrics': s.get('calculated_metrics', []), 'industry_extension_points': s.get('industry_template_extension_points', []), 'total_raw_metrics': sum(len(v) for v in s.get('metric_groups', {}).values()), 'note': 'Generic base schema. Industry and ticker-level extensions supported via industry_template_extension_points.'}}
