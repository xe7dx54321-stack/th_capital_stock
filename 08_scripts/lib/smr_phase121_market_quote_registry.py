def build_market_quote_registry():
 q=[
  {"id":"yfinance_quote","market":"HK_US","access":"free_no_key","status":"existing","tickers":["09988.HK","00700.HK","NVDA","AVGO"]},
  {"id":"akshare_quote","market":"HK","access":"free_no_key","status":"existing","tickers":["09988.HK","00700.HK"]},
  {"id":"alphavantage_free","market":"US","access":"free_key_needed","status":"candidate","tickers":["NVDA","AVGO"]},
 ]
 return {"phase121_market_quote_registry":{"total":len(q),"quotes":q,"mock_used":False,"fixture_used":False}}
