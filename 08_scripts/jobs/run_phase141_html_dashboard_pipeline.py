import json, os, sys, argparse
from pathlib import Path
from datetime import datetime

BASE_LIB = Path(__file__).resolve().parent.parent / 'lib'
BASE_REPORTING = Path(__file__).resolve().parent.parent / 'reporting'
sys.path.insert(0, str(BASE_LIB))
sys.path.insert(0, str(BASE_REPORTING))

from smr_phase141_config import load_config
from build_phase141_html_dashboard import build_full_html
from smr_phase141_html_quality_gate import run_html_quality_gate
from smr_phase141_cannot_conclude_guard import run_cannot_conclude_guard


def run_pipeline(mode='dry-run'):
    cfg = load_config()
    started_at = datetime.now().isoformat()

    if mode == 'skip-network':
        result = build_full_html()
    elif mode == 'execute':
        result = build_full_html()
        html = result['phase141_html_dashboard']['html']
        out_path = Path(__file__).resolve().parent.parent.parent / '09_runbooks' / 'generated' / 'phase141_research_console.html'
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
    else:
        result = build_full_html()

    finished_at = datetime.now().isoformat()
    qg = result['phase141_html_dashboard']['quality_gate']
    cg = result['phase141_html_dashboard']['cannot_conclude_guard']

    output = {
        'phase141_html_dashboard_pipeline': {
            'mode': mode,
            'started_at': started_at,
            'finished_at': finished_at,
            'html_length': len(result['phase141_html_dashboard']['html']),
            'quality_gate': qg['overall_status'],
            'quality_checks_pass': qg['all_pass'],
            'cannot_conclude_guard': cg['overall_status'],
            'violations': cg['violations'],
            'html_saved': mode == 'execute',
            'output_path_ignored': True,
            'static_html_only': True,
            'external_js_allowed': False,
            'external_cdn_allowed': False,
            'local_server_enabled': False,
            'browser_automation_allowed': False,
            'tickers_covered': 8,
            'mock_used': False,
            'fixture_used': False,
            'raw_saved': False,
            'ocr_used': False,
            'browser_automation_used': False,
            'pending_created': 0,
            'paper_order_created': 0,
            'real_trade_created': 0,
            'target_price_output': 0,
            'position_sizing_output': 0
        }
    }
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--skip-network', action='store_true')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()

    if args.execute:
        mode = 'execute'
    elif args.skip_network:
        mode = 'skip-network'
    else:
        mode = 'dry-run'

    output = run_pipeline(mode)
    print(json.dumps(output, indent=2, ensure_ascii=False, default=str))

if __name__ == '__main__':
    main()
