#!/usr/bin/env python3
"""Phase 62: Chinese Business Source Registry.
Loads and validates the Chinese business source registry config.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / 'config'
REGISTRY_PATH = CONFIG_DIR / 'chinese_business_source_registry.json'


def load_registry() -> dict:
    with open(REGISTRY_PATH, 'r', encoding='utf-8-sig') as f:
        return json.load(f)


def get_sources() -> list[dict]:
    return load_registry().get('sources', [])


def get_source_by_id(source_id: str) -> dict | None:
    for s in get_sources():
        if s['source_id'] == source_id:
            return s
    return None


def get_source_types_for_priority(priority: str) -> list[str]:
    types = []
    for s in get_sources():
        if s['priority'] == priority:
            types.extend(s.get('source_types', []))
    return types


def build_registry_report() -> dict:
    sources = get_sources()
    return {
        'registry_version': '1.0',
        'sources_count': len(sources),
        'priorities': {s['priority']: s['source_id'] for s in sources},
        'raw_content_saved': False,
        'ocr_allowed': False,
        'rows': [{
            'source_id': s['source_id'],
            'platform': s['source_platform'],
            'priority': s['priority'],
            'requires_network': s['requires_network'],
            'raw_content_saved': s['raw_content_saved'],
            'ocr_allowed': s['ocr_allowed'],
            'allowed_usage': s['allowed_usage'],
            'source_types_count': len(s.get('source_types', [])),
        } for s in sources],
    }
