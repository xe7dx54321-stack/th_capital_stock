#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path:
    sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from smr_industry_financial_variable_interpretation import interpret_industry_financial_variables
from smr_refined_quarterly_financial_signal_calculator import calculate_refined_quarterly_signals


def build(conn, ticker):
    interp = interpret_industry_financial_variables(ticker)
    signals = calculate_refined_quarterly_signals(ticker)
    latest = signals['refined_quarterly_financial_signals']['latest_period']
    real_data = signals['refined_quarterly_financial_signals']['real_data_used']

    observations = interp['industry_financial_variable_interpretation']['observations']

    seen = [f"最新季度（{latest}）真实财务数据已取得。"]
    implications = []
    cannot_list = []

    for o in observations:
        seen.append(o['observed_financial_fact'])
        implications.append(o['business_implication'])

    # Deduplicated cannot-conclude
    all_cannot = set()
    for o in observations:
        all_cannot.add(o['cannot_conclude'])
    # Add generic ones
    all_cannot.update([
        '不能仅凭财务数据确认800G/1.6T的具体收入占比。',
        '不能仅凭财务数据确认客户份额提升。',
        '不能仅凭财务数据确认ASP改善。',
        '不能仅凭财务数据确认市场预期差已经成立。',
    ])

    return {
        'ticker': ticker,
        'industry_aware_financial_brief_section': {
            'real_data_used': real_data,
            'latest_period': latest,
            'what_we_see': seen,
            'what_it_means': implications,
            'what_we_cannot_conclude': sorted(all_cannot),
        }
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--ticker', default='300308.SZ')
    p.add_argument('--json', action='store_true')
    p.add_argument('--markdown', action='store_true')
    args = p.parse_args()
    r = build(None, args.ticker)
    if args.markdown:
        d = r['industry_aware_financial_brief_section']
        print('## 财务信号与业务含义')
        print('')
        print('已看到的信息：')
        for s in d['what_we_see']:
            print(f'- {s}')
        print('')
        print('这些信息意味着：')
        for i in d['what_it_means']:
            print(f'- {i}')
        print('')
        print('当前不能推出：')
        for c in d['what_we_cannot_conclude']:
            print(f'- {c}')
    else:
        print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
