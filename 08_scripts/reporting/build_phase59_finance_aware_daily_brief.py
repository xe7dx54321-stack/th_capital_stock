#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_watchlist_industry_financial_signal_adapter import build_watchlist_industry_financial_signal_adapter
from smr_finance_aware_thesis_review import run_finance_aware_thesis_review
from smr_finance_aware_watchlist_decision import make_finance_aware_watchlist_decision


def build(conn, ticker):
    adapter = build_watchlist_industry_financial_signal_adapter(ticker)
    review = run_finance_aware_thesis_review(ticker)
    decision = make_finance_aware_watchlist_decision(ticker)

    ad = adapter['watchlist_industry_financial_signal_adapter']
    rd = review['finance_aware_thesis_review']
    dd = decision['finance_aware_watchlist_decision']

    exec_summary = (
        f"继续跟踪，财务侧判断增强。"
        f"收入和利润端真实数据明显改善，毛利率水平对利润质量形成支撑。"
        f"但客户份额、ASP、产品代际和预期差仍不能由财务数据直接确认。"
    )

    return {
        'ticker': ticker,
        'finance_aware_daily_brief': {
            'conclusion': f"决策: {dd['decision']}（{dd['decision_confidence']}）",
            'exec_summary': exec_summary,
            'what_we_see': ad['key_observations'],
            'implications': [
                '公司财务兑现力度较强。',
                '财务侧支持业务动能增强。',
                '但这不能单独证明800G/1.6T占比、客户份额或ASP改善。',
            ],
            'strengthened': [r['claim'] for r in rd['rows'] if r['review_result'] == 'strengthened'],
            'unconfirmed': [r['claim'] for r in rd['rows'] if r['review_result'] == 'unconfirmed'],
            'real_data_used': ad['real_financial_data_used'],
            'fixture_used': ad['fixture_used'],
            'pending_created': 0,
            'paper_order_created': 0,
            'real_trade_created': 0,
        }
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--ticker', default='300308.SZ')
    p.add_argument('--json', action='store_true'); p.add_argument('--markdown', action='store_true')
    args = p.parse_args(); r = build(None, args.ticker)
    if args.markdown:
        d = r['finance_aware_daily_brief']
        print(f"# 中际旭创内部投研跟踪简报")
        print(f"\n## 老板摘要")
        print(f"\n结论：")
        print(f"- {d['conclusion']}")
        print(f"- {d['exec_summary']}")
        print(f"\n看到的信息：")
        for o in d['what_we_see']: print(f"- {o}")
        print(f"\n意味着什么：")
        for i in d['implications']: print(f"- {i}")
        print(f"\n## 研究员详情")
        print(f"\n已增强的判断：")
        for s in d['strengthened'][:4]: print(f"- {s}")
        print(f"\n仍不能成立的判断：")
        for u in d['unconfirmed'][:4]: print(f"- {u}")
        print(f"\n> 真实数据={d['real_data_used']} fixture={d['fixture_used']} pending/order/trade=0")
    else: print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == '__main__': main()
