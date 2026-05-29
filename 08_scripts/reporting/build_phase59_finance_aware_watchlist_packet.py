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

    what_we_see = ad['key_observations']
    implications = [
        '财务侧已经支持公司业务兑现增强，收入和利润端明显改善。',
        '毛利率水平对利润质量形成支撑。',
        '但不能单独证明具体产品代际、客户份额或ASP。',
    ]
    strengthened_claims = [r['claim'] for r in rd['rows'] if r['review_result'] == 'strengthened']
    unconfirmed_claims = [r['claim'] for r in rd['rows'] if r['review_result'] == 'unconfirmed']

    return {
        'ticker': ticker,
        'finance_aware_watchlist_packet': {
            'real_data_used': ad['real_financial_data_used'],
            'latest_period': ad['latest_period'],
            'what_we_see': what_we_see,
            'implications': implications,
            'strengthened': [f"财务侧支持{r}增强" for r in strengthened_claims[:4]],
            'unconfirmed': [f"{r}仍不能由财务数据确认" for r in unconfirmed_claims[:4]],
            'decision': dd['decision'],
            'decision_confidence': dd['decision_confidence'],
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
        d = r['finance_aware_watchlist_packet']
        print(f"# 中际旭创财务信号驱动的跟踪简报")
        print(f"\n## 1. 当前已看到的信息")
        for o in d['what_we_see']: print(f"- {o}")
        print(f"\n## 2. 这些信息意味着什么")
        for i in d['implications']: print(f"- {i}")
        print(f"\n## 3. 已增强的判断")
        for s in d['strengthened']: print(f"- {s}")
        print(f"\n## 4. 仍不能成立的判断")
        for u in d['unconfirmed']: print(f"- {u}")
        print(f"\n## 5. 当前跟踪结论")
        print(f"- 决策: {d['decision']}")
        print(f"- 置信度: {d['decision_confidence']}")
        print(f"\n> pending/order/trade=0")
    else: print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == '__main__': main()
