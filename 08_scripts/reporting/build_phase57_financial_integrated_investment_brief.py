#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path:
    sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from smr_investment_logic_brief_builder import build_investment_logic_brief
from smr_refined_quarterly_financial_signal_calculator import calculate_refined_quarterly_signals
from smr_structured_financial_data_adapter import fetch_structured_financial_data


def build(conn, ticker):
    phase54_brief = build_investment_logic_brief(ticker)
    signals_result = calculate_refined_quarterly_signals(ticker)
    signals_data = signals_result.get('refined_quarterly_financial_signals', {})
    fetch_result = fetch_structured_financial_data(ticker, 'execute')
    real_available = fetch_result['structured_financial_data_fetch'].get('real_data_available', False)

    real_data_used = signals_data.get('real_data_used', False)
    fixture_used = signals_data.get('fixture_used', False)
    latest = signals_data.get('latest_period', 'unknown')

    # Add financial data observations to the brief
    p54 = phase54_brief.get('investment_logic_brief', {})

    # Build financial observations paragraph
    financial_obs = []
    if real_data_used and not fixture_used:
        financial_obs.append(
            f'已取得公司真实结构化财务数据（最新期间：{latest}），覆盖利润表、资产负债表和现金流量表。'
        )
        # Latest signal snapshots
        latest_signals = [s for s in signals_data.get('all_signals', []) if s['period'] == latest]
        rev_yoy = next((s for s in latest_signals if s['signal'] == 'single_quarter_revenue_yoy'), None)
        np_yoy = next((s for s in latest_signals if s['signal'] == 'single_quarter_net_profit_yoy'), None)
        gm = next((s for s in latest_signals if s['signal'] == 'gross_margin'), None)
        ocf_ratio = next((s for s in latest_signals if s['signal'] == 'operating_cash_flow_to_net_profit'), None)

        if rev_yoy:
            financial_obs.append(f'最新单季度收入同比：{"+" if rev_yoy["value"]>0 else ""}{rev_yoy["value"]*100:.1f}%')
        if np_yoy:
            financial_obs.append(f'最新单季度净利润同比：{"+" if np_yoy["value"]>0 else ""}{np_yoy["value"]*100:.1f}%')
        if gm:
            financial_obs.append(f'毛利率：{gm["value"]*100:.1f}%')
        if ocf_ratio:
            financial_obs.append(f'经营现金流/净利润比：{ocf_ratio["value"]:.2f}')

    elif fixture_used:
        financial_obs.append('当前财务数据来自fixture，不能用于真实财务判断。真实结构化财务数据源当前不可用。')
    else:
        financial_obs.append('当前未取得真实结构化财务数据，本简报不能形成真实财务判断。')

    # Build implications
    financial_implications = []
    if real_data_used and not fixture_used:
        rev_yoy = next((s for s in signals_data.get('all_signals', []) if s['period'] == latest and s['signal'] == 'single_quarter_revenue_yoy'), None)
        gm = next((s for s in signals_data.get('all_signals', []) if s['period'] == latest and s['signal'] == 'gross_margin'), None)
        np_yoy = next((s for s in signals_data.get('all_signals', []) if s['period'] == latest and s['signal'] == 'single_quarter_net_profit_yoy'), None)

        if rev_yoy and rev_yoy['direction'] == 'positive':
            financial_implications.append('收入端已出现增长兑现，收入增速与AI光模块需求的关联需要进一步用产品数据验证。')
        if np_yoy and np_yoy['direction'] == 'positive':
            financial_implications.append('利润端同步增长，但利润增速与收入增速的关系需要进一步分析成本结构。')
        if gm:
            financial_implications.append(f'毛利率水平为{gm["value"]*100:.1f}%，毛利率是否支持产品结构升级逻辑取决于后续趋势稳定性。')

    # Cannot conclude additions
    financial_cannot = [
        '财务数据不能直接证明客户份额变化',
        '财务数据不能直接证明ASP（平均售价）的绝对值',
        '财务数据不能直接证明800G/1.6T产品占比',
        '财务数据不能直接确认市场预期差',
    ]

    return {
        'ticker': ticker,
        'financial_integrated_investment_brief': {
            'real_data_used': real_data_used,
            'fixture_used': fixture_used,
            'latest_period': latest,
            'one_line_conclusion': p54.get('one_line_conclusion', ''),
            'current_observations': (p54.get('current_observations', []) + financial_obs),
            'implications': (p54.get('implications', []) + financial_implications),
            'can_conclude': p54.get('can_conclude', []),
            'cannot_conclude': (p54.get('cannot_conclude', []) + financial_cannot),
            'business_variable_detail': p54.get('business_variable_detail', []),
            'bull_base_bear': p54.get('bull_base_bear', {}),
            'current_conclusion': p54.get('current_conclusion', []),
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
        d = r['financial_integrated_investment_brief']
        print('# 中际旭创内部投研简报')
        print('')
        print('## 1. 一句话结论')
        print('')
        print(d.get('one_line_conclusion', ''))
        print('')
        print('## 2. 当前已看到的信息')
        print('')
        for o in d.get('current_observations', []):
            print(f'- {o}')
        print('')
        print('## 3. 这些信息意味着什么')
        print('')
        for i in d.get('implications', []):
            print(f'- {i}')
        print('')
        print('## 4. 当前能成立的判断')
        print('')
        for c in d.get('can_conclude', []):
            print(f'- {c}')
        print('')
        print('## 5. 当前不能成立的判断')
        print('')
        for n in d.get('cannot_conclude', []):
            print(f'- {n}')
        print('')
        print('## 6. 关键业务变量拆解')
        print('')
        for v in d.get('business_variable_detail', []):
            print(f'- {v.get("变量", "")}: {v.get("状态", "")}')
        print('')
        print('## 7. 市场预期与差异')
        print('')
        print('市场大概率已经认可AI光模块需求强。')
        print('真正的差异不在"行业有没有需求"，而在公司能否通过高端产品放量实现毛利率稳定和盈利弹性。')
        print('当前这条差异只能判断为可能存在，尚未被硬数据确认。')
        print('')
        print('## 8. 多空分歧')
        print('')
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
        print('')
        for c in d.get('current_conclusion', []):
            print(c)
        print('')
        print(f'> 数据来源：真实结构化财务数据={d.get("real_data_used", False)} fixture={d.get("fixture_used", False)} pending/order/trade=0')
    else:
        print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
