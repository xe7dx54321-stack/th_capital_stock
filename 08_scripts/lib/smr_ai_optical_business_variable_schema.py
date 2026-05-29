#!/usr/bin/env python3
import json
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parent.parent.parent / 'config' / 'industry_business_variables_ai_optical_module.json'

def load_business_variable_schema():
    with open(SCHEMA_PATH, 'r', encoding='utf-8-sig') as f:
        return json.load(f)

def get_business_variables():
    return load_business_variable_schema().get('business_variables', [])

def get_business_forbidden_attributions():
    return load_business_variable_schema().get('forbidden_attributions', [])

def build_business_schema_report():
    schema = load_business_variable_schema()
    variables = schema.get('business_variables', [])
    return {
        'industry': schema['industry'],
        'description': schema['description'],
        'variables_count': len(variables),
        'forbidden_count': len(schema.get('forbidden_attributions', [])),
        'variables': [
            {'variable': v['variable'], 'description': v['description'],
             'keywords_count': len(v.get('evidence_keywords', [])),
             'cannot_conclude_count': len(v.get('cannot_conclude_without_direct_disclosure', []))}
            for v in variables
        ],
        'forbidden_attributions': schema.get('forbidden_attributions', []),
    }
