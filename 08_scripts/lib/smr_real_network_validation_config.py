#!/usr/bin/env python3
"""Phase 63: Real Network Validation Config loader."""
import json
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / 'config'
CONFIG_PATH = CONFIG_DIR / 'real_network_source_validation_rules.json'

def load_config() -> dict:
    with open(CONFIG_PATH, 'r', encoding='utf-8-sig') as f:
        return json.load(f)

def get_network_validation() -> dict:
    return load_config().get('network_validation', {})

def get_source_limits() -> dict:
    return load_config().get('source_limits', {})

def build_validation_config_report() -> dict:
    cfg = load_config()
    nv = cfg.get('network_validation', {})
    return {
        'config_version': cfg['version'],
        'network_validation': {
            'timeout': nv['default_timeout_seconds'],
            'max_sources': nv['max_sources_per_run'],
            'save_raw': nv['save_raw_content'],
            'ocr_allowed': nv['ocr_allowed'],
            'pdf_extraction': nv['allow_pdf_text_extraction'],
            'mock_fallback': nv['allow_mock_fallback'],
            'fixture_fallback': nv['allow_fixture_fallback'],
        },
        'source_limits': cfg.get('source_limits', {}),
        'fetch_statuses_count': len(cfg.get('fetch_statuses', [])),
    }
