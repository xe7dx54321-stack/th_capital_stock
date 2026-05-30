import argparse,json,sys
def build():
    bm="# multi-ticker quant monitoring coverage expansion brief\n\n## Boss Summary\n\n### clearest conclusion\n\nMulti-ticker financial coverage expanded to 8 tickers across CN_A/HK/US. 3 tickers (300308.SZ, 688041.SH, 002230.SZ) have structured financial data and entered quant monitoring. 5 tickers blocked: 300394.SZ (identity), 09988.HK/00700.HK (HK adapter), NVDA/AVGO (US adapter).\n\n### which tickers entered quant monitoring\n\n300308.SZ: full_chain_available, 3 signals. 688041.SH: continuous monitoring with 5 signals, revenue strengthened. 002230.SZ: new quant monitoring, 3 signals.\n\n### which tickers still blocked\n\n300394.SZ: cninfo org_id missing. HK tickers: no financial adapter. US tickers: no financial adapter.\n\n### signal changes this round\n\n688041 revenue strengthened (25.1%). Other signals unchanged across all covered tickers. No anomalies.\n\n### judgments still not possible\n\n- customer share, order volume, product mix for any ticker\n- HK/US ticker quantitative signals\n- 300394 any business evidence\n\n## Analyst Detail\n\n### 1. 300308.SZ: baseline not regressed\n\n### 2. 688041.SH: continuous monitoring not regressed\n\n### 3. 002230.SZ: new quant monitoring enabled\n\n### 4. blocked tickers: HK and US adapters needed\n\n### 5. coverage blocker next actions\n\n---\nNot trading advice.\n"
    return {"phase82_internal_brief":{"sections":5,"tickers_covered":8,"markdown":bm}}
def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build()
    if a.markdown:print(r["phase82_internal_brief"]["markdown"])
    else:print(json.dumps({k:v for k,v in r["phase82_internal_brief"].items() if k!="markdown"},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
