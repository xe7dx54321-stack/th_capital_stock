#!/usr/bin/env python3
import json
from pathlib import Path
REGISTRY_PATH = Path(__file__).resolve().parents[2] / 'config' / 'financial_source_registry.json'
def load_registry():
    if REGISTRY_PATH.exists(): return json.loads(REGISTRY_PATH.read_text(encoding='utf-8'))
    return {'sources': [], 'preferred_primary': ''}
def get_real_sources():
    r = load_registry()
    return [s for s in r.get('sources', []) if s.get('confidence') == 'real_structured']
def get_fallback_sources():
    r = load_registry()
    return [s for s in r.get('sources', []) if s.get('confidence') == 'real_report_text_extracted']
def build_registry_report():
    r = load_registry()
    return {'real_financial_source_registry': r}
