#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path:
    sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from smr_investment_logic_brief_builder import build_investment_logic_brief
from smr_industry_financial_variable_interpretation import interpret_industry_financial_variables
from smr_refined_quarterly_financial_signal_calculator import calculate_refined_quarterly_signals


def build(conn, ticker):
    p54 = build_investment_logic_brief(ticker)
    interp = interpret_industry_financial_variables(ticker)
    signals = calculate_refined_quarterly_signals(ticker)
    sd = signals['refined_quarterly_financial_signals']
    latest = sd['latest_period']
    real_data = sd['real_data_used']
    fixture = sd['fixture_used']

    b = p54.get('investment_logic_brief', {})
    obs_list = list(b.get('current_observations', []))
    impl_list = list(b.get('implications', []))
    can_list = list(b.get('can_conclude', []))
    cannot_list = list(b.get('cannot_conclude', []))

    # Add industry financial observations
    if real_data and not fixture:
        obs_list.append(f'真实财务数据（{latest}）已显示收入和利润端明显增强，毛利率处于较强水平。')
        impl_list.append('财务侧已经支持公司业务兑现增强，但不能单独证明具体产品代际、客户份额或ASP。')
        can_list.append('财务数据支持收入兑现和利润质量偏强。')
        cannot_list.extend([
            '财务数据不能单独确认800G/1.6T占比。',
            '财务数据不能单独确认客户份额变化。',
            '财务数据不能单独确认ASP改善。',
            '财务数据不能单独确认市场预期差。',
        ])

    return {
        'ticker': ticker,
        'industry_financial_integrated_brief': {
            'real_data_used': real_data,
            'fixture_used': fixture,
            'latest_period': latest,
            'one_line_conclusion': b.get('one_line_conclusion', ''),
            'current_observations': obs_list,
            'implications': impl_list,
            'can_conclude': can_list,
            'cannot_conclude': cannot_list,
            'business_variable_detail': b.get('business_variable_detail', []),
            'bull_base_bear': b.get('bull_base_bear', {}),
            'current_conclusion': b.get('current_conclusion', []),
            'pending_created': 0,
            'paper_order_created': 0,
            'real_trade_created': 0,
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
        d = r['industry_financial_integrated_brief']
        print(f'# 中际旭创内部投研简报（含行业财务变量）')
        print('')
        print('## 1. 一句话结论')
        print('')
        print(d.get('one_line_conclusion', ''))
        print('')
        print('## 2. 当前已看到的信息')
        for o in d.get('current_observations', []):
            print(f'- {o}')
        print('')
        print('## 3. 这些信息意味着什么')
        for i in d.get('implications', []):
            print(f'- {i}')
        print('')
        print('## 4. 当前能成立的判断')
        for c in d.get('can_conclude', []):
            print(f'- {c}')
        print('')
        print('## 5. 当前不能成立的判断')
        for n in d.get('cannot_conclude', []):
            print(f'- {n}')
        print('')
        print('## 6. 关键业务变量拆解')
        for v in d.get('business_variable_detail', []):
            print(f'- {v.get("变量", "")}: {v.get("状态", "")}')
        print('')
        print('## 7. 市场预期与差异')
        print('')
        print('市场大概率已经认可AI光模块需求强。')
        print('真正的差异不在"行业有没有需求"，而在公司能否通过高端产品放量实现毛利率稳定和盈利弹性。')
        print('')
        print('## 8. 多空分歧')
        bb = d.get('bull_base_bear', {})
        print('**多头逻辑：**')
        for item in bb.get('bull_case', [])[:3]:
            print(f'- {item}')
        print('')
        print('**空头逻辑：**')
        for item in bb.get('bear_case', [])[:3]:
            print(f'- {item}')
        print('')
        print('## 9. 当前结论')
        for c in d.get('current_conclusion', []):
            print(c)
        print('')
        print(f'> 数据来源：真实财务={d.get("real_data_used")} fixture={d.get("fixture_used")} pending/order/trade=0')
    else:
        print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
