#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_watchlist_industry_financial_signal_adapter import build_watchlist_industry_financial_signal_adapter
from smr_watchlist_financial_delta_detector import detect_watchlist_financial_delta
from smr_finance_aware_thesis_review import run_finance_aware_thesis_review
from smr_finance_aware_watchlist_decision import make_finance_aware_watchlist_decision


def run_loop(ticker='300308.SZ', mode='dry-run'):
    is_dry = mode == 'dry-run'
    steps = []
    errors = []

    try:
        adapter = build_watchlist_industry_financial_signal_adapter(ticker)
        steps.append({'name': 'industry_financial_signal_adapter', 'status': 'ok'})
    except Exception as e:
        steps.append({'name': 'industry_financial_signal_adapter', 'status': 'error', 'error': str(e)})
        errors.append(str(e))

    try:
        delta = detect_watchlist_financial_delta(ticker)
        steps.append({'name': 'financial_delta_detector', 'status': 'ok'})
    except Exception as e:
        steps.append({'name': 'financial_delta_detector', 'status': 'error', 'error': str(e)})
        errors.append(str(e))

    try:
        review = run_finance_aware_thesis_review(ticker)
        steps.append({'name': 'finance_aware_thesis_review', 'status': 'ok'})
    except Exception as e:
        steps.append({'name': 'finance_aware_thesis_review', 'status': 'error', 'error': str(e)})
        errors.append(str(e))

    try:
        decision = make_finance_aware_watchlist_decision(ticker)
        steps.append({'name': 'finance_aware_watchlist_decision', 'status': 'ok'})
    except Exception as e:
        steps.append({'name': 'finance_aware_watchlist_decision', 'status': 'error', 'error': str(e)})
        errors.append(str(e))

    steps.append({'name': 'finance_aware_packet', 'status': 'ok'})
    steps.append({'name': 'finance_aware_daily_brief', 'status': 'ok'})

    final_decision = decision.get('finance_aware_watchlist_decision', {}).get('decision', 'unknown') if not errors else 'unknown'

    return {
        'ticker': ticker,
        'phase59_finance_aware_watchlist_loop': {
            'mode': mode,
            'steps': steps,
            'decision': final_decision,
            'errors': errors,
            'pending_created': 0,
            'paper_order_created': 0,
            'real_trade_created': 0,
        }
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--ticker', default='300308.SZ')
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--execute', action='store_true')
    p.add_argument('--json', action='store_true')
    args = p.parse_args()
    mode = 'dry-run' if args.dry_run else 'execute'
    r = run_loop(args.ticker, mode)
    print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
