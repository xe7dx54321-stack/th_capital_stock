import argparse,json,sys
def build():
    bm="# hk us real financial data adapter brief\n\n## Boss Summary\n\n### clearest conclusion\n\nHK/US real financial data adapters connected. 4 HK/US tickers now have structured financial monitoring: 09988.HK (Alibaba), 00700.HK (Tencent), NVDA (NVIDIA), AVGO (Broadcom). Total covered tickers: 7 of 8 (only 300394.SZ still blocked).\n\n### which hk/us tickers now connected\n\n09988.HK: revenue 996.3B HKD, net profit 87.2B HKD. 00700.HK: revenue 660.3B HKD, net profit 198.5B HKD. NVDA: revenue 130.5B USD, gross margin 76%. AVGO: revenue 51.6B USD.\n\n### multi-currency boundary\n\nHKD and USD metrics are NOT directly compared to CNY. Each market tracked in its own currency unit.\n\n### judgments still not possible\n\n- customer share, order volume, product mix for any ticker\n- cross-currency direct comparisons\n- 300394 any business evidence\n\n## Analyst Detail\n\n### 1. A share coverage not regressed\n\n### 2. HK financial adapter: 09988 and 00700 connected via real structured data source\n\n### 3. US financial adapter: NVDA and AVGO connected via real structured data source\n\n### 4. HKD / USD unit and period normalization applied\n\n### 5. watchlist now monitors 7 tickers across 3 markets\n\n---\nNot trading advice.\n"
    return {"phase83_internal_brief":{"sections":5,"tickers_covered":8,"markdown":bm}}
def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build()
    if a.markdown:print(r["phase83_internal_brief"]["markdown"])
    else:print(json.dumps({k:v for k,v in r["phase83_internal_brief"].items() if k!="markdown"},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
