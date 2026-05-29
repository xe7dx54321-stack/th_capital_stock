#!/usr/bin/env python3
# Capex field matching: identifies capex-like columns from cash flow statements
# Supports Chinese & English column name variants

CAPEX_CN_VARIANTS = [
    '购建固定资产、无形资产和其他长期资产支付的现金',
    '购建固定资产、无形资产和其他长期资产所支付的现金',
    '购建固定资产、无形资产和其他长期资产支付现金',
    '购建固定资产、无形资产和其他长期资产所支付现金',
    '购买固定资产、无形资产和其他长期资产支付的现金',
    '购建固定资产无形资产和其他长期资产支付的现金',
]

CAPEX_EN_VARIANTS = [
    'capex',
    'capital_expenditure',
    'cash_paid_for_fixed_assets',
    'purchase_of_fixed_assets_intangible_assets_and_other_long_term_assets',
]


def fuzzy_match_capex_column(column_name):
    if not column_name or not isinstance(column_name, str):
        return (False, '')
    cn = column_name.strip().lower()
    for v in CAPEX_CN_VARIANTS:
        if cn == v:
            return (True, 'exact_cn')
    for v in CAPEX_EN_VARIANTS:
        if cn == v:
            return (True, 'exact_en')
    if '\u56fa\u5b9a\u8d44\u4ea7' in cn and '\u652f\u4ed8' in cn and '\u5904\u7f6e' not in cn:
        return (True, 'fuzzy_cn_keyword')
    if 'fixed_asset' in cn and 'paid' in cn:
        return (True, 'fuzzy_en_keyword')
    return (False, '')


def find_capex_columns(column_names):
    matched = {}
    for col in column_names:
        is_match, method = fuzzy_match_capex_column(col)
        if is_match:
            matched[col] = method
    return matched


def match_capex_fields(ticker='300308.SZ', column_names=None):
    candidates_checked = len(column_names) if column_names else 0
    matched = find_capex_columns(column_names) if column_names else {}
    result = {
        'ticker': ticker,
        'capex_field_matching': {
            'candidate_columns_checked': candidates_checked,
            'matched_capex_columns': list(matched.keys()),
            'match_methods': matched,
            'capex_records_found': len(matched),
            'match_confidence': 'high' if matched else 'none',
            'capex_missing_after_match': len(matched) == 0,
            'notes': []
        }
    }
    if not matched:
        result['capex_field_matching']['missing_reason'] = 'no_capex_like_column_found_in_cash_flow_statement'
    return result
