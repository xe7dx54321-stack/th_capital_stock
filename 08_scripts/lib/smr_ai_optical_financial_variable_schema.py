#!/usr/bin/env python3
import json
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parent.parent.parent / 'config' / 'industry_financial_variables_ai_optical_module.json'


def load_ai_optical_financial_variable_schema():
    with open(SCHEMA_PATH, 'r', encoding='utf-8-sig') as f:
        return json.load(f)


def get_industry_variables():
    schema = load_ai_optical_financial_variable_schema()
    return schema.get('financial_variables', [])


def get_forbidden_attributions():
    schema = load_ai_optical_financial_variable_schema()
    return schema.get('forbidden_attributions', [])


def build_schema_report():
    schema = load_ai_optical_financial_variable_schema()
    variables = schema.get('financial_variables', [])
    return {
        'industry': schema['industry'],
        'description': schema['description'],
        'variables_count': len(variables),
        'forbidden_attributions_count': len(schema.get('forbidden_attributions', [])),
        'variables': [
            {
                'variable': v['variable'],
                'description': v['description'],
                'related_metrics_count': len(v.get('related_financial_metrics', [])),
                'cannot_conclude_count': len(v.get('cannot_conclude_from_financials_alone', [])),
            }
            for v in variables
        ],
        'forbidden_attributions': schema.get('forbidden_attributions', []),
    }
