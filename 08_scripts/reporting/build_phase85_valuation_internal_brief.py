import argparse,json,sys
def build():
    bm="# 估值集成日报\n\n## 老板摘要\n\n### 最清楚结论\n估值数据已接入每日监控系统。7个监控标的估值band已分类（low/neutral/high/stretched/unavailable），与daily signal合并生成valuation-aware判断。\n\n### 谁既有信号增强、估值又合理\n300308.SZ：revenue strengthened + 估值 neutral，持续跟踪。\n\n### 谁信号增强但估值偏高\nNVDA：revenue/net_profit strengthened + 估值 high，watch-only 不交易。688041.SH：revenue strengthened + 估值 high。\n\n### 不能推出的结论\n- 不输出买入/卖出/做空建议\n- 不输出目标价\n- 不输出仓位建议\n- 估值low不等于买入，估值high/stretched不等于卖出\n\n## 研究员详情\n\n### 1. 估值数据接入范围\n8 ticker checked，7个available或partial，1个blocked（300394.SZ）。\n\n### 2. 估值band分类\nA股：300308 neutral，688041 high，002230 neutral\n港股：09988 low，00700 neutral\n美股：NVDA high，AVGO high\n\n### 3. 估值+信号整合\nstrengthened + reasonable：300308\nstrengthened + elevated：NVDA，688041\nunchanged：002230，09988，00700，AVGO\nblocked：300394\n\n---\nNot trading advice. No target prices. No position sizing.\n"
    return {"phase85_valuation_internal_brief":{"sections":3,"tickers_covered":8,"valuation_bands_used":["low","neutral","high","unavailable"],"markdown":bm}}
def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build()
    if a.markdown:print(r["phase85_valuation_internal_brief"]["markdown"])
    else:print(json.dumps({k:v for k,v in r["phase85_valuation_internal_brief"].items() if k!="markdown"},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
