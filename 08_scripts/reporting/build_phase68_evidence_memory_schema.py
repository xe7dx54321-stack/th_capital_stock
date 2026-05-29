#!/usr/bin/env python3
'''Phase 68 evidence memory schema report.'''
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
from smr_evidence_memory_schema import load_schema

def build():
    s = load_schema()
    return {'schema_version': s.get('schema_version', ''), 'required_fields_count': len(s.get('required_fields', [])),
            'evidence_strength_enum': s.get('evidence_strength_enum', []),
            'allowed_usage_enum': s.get('allowed_usage_enum', []),
            'business_variables': s.get('business_variables', [])}

def main():
    p = argparse.ArgumentParser(); p.add_argument('--json', action='store_true'); p.add_argument('--markdown', action='store_true')
    a = p.parse_args(); r = build()
    if a.json: print(json.dumps(r, ensure_ascii=False, indent=2))
    elif a.markdown: print('# Evidence Memory Schema\n\nRequired fields: {}\nStrengths: {}'.format(r['required_fields_count'], ','.join(r['evidence_strength_enum'])))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == '__main__': main()
