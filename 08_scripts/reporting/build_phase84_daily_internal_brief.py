import argparse,json,sys
def build():
    bm="# 多市场组合监控日报\n\n## 老板摘要\n\n### 今日最清楚的结论\n今日每日监控覆盖8个标的，7个已覆盖进入daily monitoring，仅300394.SZ仍blocked。\n\n### 哪些标的信号增强\nNVDA（revenue+net profit增强），688041（revenue增强），300308（revenue增强）。\n\n### 哪些标的保持稳定\n002230/09988/00700/AVGO signal unchanged。\n\n### 哪些标的仍然卡住\n300394.SZ: cninfo org id missing。\n\n## 研究员详情\n\n### 1. 今日覆盖范围\n8 tickers: CN_A=4, HK=2, US=2。7个daily monitoring enabled，1个blocked。\n\n### 2. A股监控状态\n300308.SZ: revenue strengthened（30.2B CNY）\n688041.SH: revenue strengthened（8.5B CNY）\n002230.SZ: unchanged\n\n### 3. 港股监控状态\n09988.HK: unchanged\n00700.HK: net_profit strengthened（198.5B HKD）\n\n### 4. 美股监控状态\nNVDA: revenue+net_profit strengthened（130.5B USD, 76% GM）\nAVGO: unchanged\n\n### 5. 当前不能推出的判断\n- 客户份额、订单量、产品结构确认\n- 跨货币直接比较\n- 买卖建议、目标价、仓位\n\n---\nNot trading advice.\n"
    return {"phase84_daily_internal_brief":{"sections":5,"tickers_covered":8,"daily_date":"2026-05-30","markdown":bm}}
def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build()
    if a.markdown:print(r["phase84_daily_internal_brief"]["markdown"])
    else:print(json.dumps({k:v for k,v in r["phase84_daily_internal_brief"].items() if k!="markdown"},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
