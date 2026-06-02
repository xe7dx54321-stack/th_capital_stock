def build_source_candidate_registry():
 s=[
  {"id":"hkex_news","type":"official","market":"HK","desc":"HKEX news/announcement RSS","access":"free_no_key","tickers":["09988.HK","00700.HK"]},
  {"id":"sec_edgar","type":"official","market":"US","desc":"SEC EDGAR filings","access":"free_no_key","tickers":["NVDA","AVGO"]},
  {"id":"hkex_filing","type":"official","market":"HK","desc":"HKEX published financial filings","access":"free_no_key","tickers":["09988.HK","00700.HK"]},
  {"id":"sec_10k","type":"official","market":"US","desc":"SEC 10-K annual report","access":"free_no_key","tickers":["NVDA","AVGO"]},
  {"id":"sec_10q","type":"official","market":"US","desc":"SEC 10-Q quarterly report","access":"free_no_key","tickers":["NVDA","AVGO"]},
  {"id":"sec_8k","type":"official","market":"US","desc":"SEC 8-K current report","access":"free_no_key","tickers":["NVDA","AVGO"]},
  {"id":"yfinance","type":"third_party","market":"HK_US","desc":"Yahoo Finance (existing)","access":"free_no_key","tickers":["09988.HK","00700.HK","NVDA","AVGO"]},
  {"id":"akshare_hk","type":"third_party","market":"HK","desc":"Akshare HK (existing)","access":"free_no_key","tickers":["09988.HK","00700.HK"]},
  {"id":"finviz","type":"third_party","market":"US","desc":"Finviz screener/news","access":"free_no_key","tickers":["NVDA","AVGO"]},
  {"id":"futu_public","type":"third_party","market":"HK","desc":"Futu public stock pages","access":"free_no_key","tickers":["09988.HK","00700.HK"]},
  {"id":"marketwatch","type":"third_party","market":"US","desc":"MarketWatch financials","access":"free_no_key","tickers":["NVDA","AVGO"]},
 ]
 return {"phase121_source_candidate_registry":{"total":len(s),"official":sum(1 for x in s if x["type"]=="official"),"third_party":sum(1 for x in s if x["type"]=="third_party"),"sources":s,"mock_used":False,"fixture_used":False}}
