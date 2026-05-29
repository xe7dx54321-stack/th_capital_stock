#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path:
    sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from smr_ai_optical_financial_variable_schema import build_schema_report


def build(conn, ticker=None):
    return build_schema_report()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--json', action='store_true')
    p.add_argument('--markdown', action='store_true')
    args = p.parse_args()
    r = build(None)
    if args.markdown:
        print(f"# AI Optical Module Financial Variable Schema")
        print(f"\n- Industry: {r['industry']}")
        print(f"- Variables defined: {r['variables_count']}")
        print(f"- Forbidden attributions: {r['forbidden_attributions_count']}")
        print(f"\n## Variables")
        for v in r['variables']:
            print(f"\n### {v['variable']}")
            print(f"- {v['description']}")
            print(f"- Related metrics: {v['related_metrics_count']}")
            print(f"- Cannot-conclude items: {v['cannot_conclude_count']}")
        print(f"\n## Forbidden Attributions")
        for fa in r['forbidden_attributions']:
            print(f"- {fa}")
    else:
        print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
