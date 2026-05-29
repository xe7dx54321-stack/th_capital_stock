#!/usr/bin/env python3
from smr_financial_signal_to_industry_variable_mapper import map_signals_to_industry_variables
from smr_refined_quarterly_financial_signal_calculator import calculate_refined_quarterly_signals


def interpret_industry_financial_variables(ticker='300308.SZ'):
    mapper = map_signals_to_industry_variables(ticker)
    rows = mapper['financial_signal_to_industry_variable_map']['rows']
    signals_result = calculate_refined_quarterly_signals(ticker)
    latest = signals_result['refined_quarterly_financial_signals']['latest_period']
    all_signals = signals_result['refined_quarterly_financial_signals']['all_signals']
    latest_signals = {s['signal']: s for s in all_signals if s['period'] == latest}

    observations = []

    # Revenue observation
    rev_yoy = latest_signals.get('single_quarter_revenue_yoy', {})
    if rev_yoy:
        direction_cn = '大幅增长' if rev_yoy.get('value', 0) > 0.3 else ('增长' if rev_yoy.get('value', 0) > 0 else '下降')
        observations.append({
            'observed_financial_fact': f"最新季度收入同比{direction_cn}",
            'business_implication': '收入端已经出现明显兑现，支持公司处于需求较强的业务环境。',
            'judgment_status': 'supported',
            'cannot_conclude': '不能仅凭收入增长确认800G/1.6T占比提升或客户份额变化。',
        })

    # Gross margin observation
    gm = latest_signals.get('gross_margin', {})
    if gm:
        gm_pct = gm.get('value', 0) * 100
        gm_level = '较高' if gm_pct > 35 else ('中等' if gm_pct > 25 else '偏低')
        observations.append({
            'observed_financial_fact': f"毛利率为{gm_pct:.1f}%，处于{gm_level}水平",
            'business_implication': '毛利率水平对利润弹性形成支持，但不能单独证明ASP改善或产品级价格趋势。',
            'judgment_status': 'partially_supported',
            'cannot_conclude': '不能仅凭毛利率确认ASP改善或产品级毛利率提升。',
        })

    # Net profit observation
    np_yoy = latest_signals.get('single_quarter_net_profit_yoy', {})
    if np_yoy:
        direction_cn = '大幅增长' if np_yoy.get('value', 0) > 0.3 else ('增长' if np_yoy.get('value', 0) > 0 else '下降')
        observations.append({
            'observed_financial_fact': f"最新季度净利润同比{direction_cn}",
            'business_implication': '利润端同步增长，支持盈利弹性正在释放，但需要进一步验证利润增长的持续性。',
            'judgment_status': 'supported',
            'cannot_conclude': '不能仅凭利润增长确认盈利模式已经稳定确立。',
        })

    # OCF observation
    ocf_ratio = latest_signals.get('operating_cash_flow_to_net_profit', {})
    if ocf_ratio:
        ocf_val = ocf_ratio.get('value', 0)
        ocf_level = '良好' if ocf_val > 0.8 else ('一般' if ocf_val > 0.5 else '偏弱')
        observations.append({
            'observed_financial_fact': f"经营现金流/净利润比为{ocf_val:.2f}，现金转化{ocf_level}",
            'business_implication': '现金转化率反映利润的现金质量，需要持续观察是否稳定。',
            'judgment_status': 'partially_supported' if ocf_val > 0.5 else 'weakened',
            'cannot_conclude': '不能仅凭单季度现金转化率确认收入质量无问题。',
        })

    # Determine overall
    statuses = [o['judgment_status'] for o in observations]
    supported_count = sum(1 for s in statuses if s == 'supported')
    if supported_count >= 2:
        overall = 'financials_support_business_momentum_but_do_not_confirm_product_mix_or_customer_share'
    else:
        overall = 'financial_signals_mixed_need_more_evidence'

    return {
        'ticker': ticker,
        'industry_financial_variable_interpretation': {
            'latest_period': latest,
            'observations': observations,
            'overall_interpretation': overall,
        }
    }
