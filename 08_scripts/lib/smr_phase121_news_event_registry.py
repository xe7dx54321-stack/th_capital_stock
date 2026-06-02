def build_news_event_registry():
 n=[
  {"id":"hkex_announcements","type":"official","market":"HK","access":"free_no_key","status":"candidate","tickers":["09988.HK","00700.HK"]},
  {"id":"sec_press","type":"official","market":"US","access":"free_no_key","status":"candidate","tickers":["NVDA","AVGO"]},
  {"id":"finviz_news","type":"aggregator","market":"US","access":"free_no_key","status":"candidate","tickers":["NVDA","AVGO"]},
  {"id":"google_finance","type":"aggregator","market":"HK_US","access":"free_no_key","status":"candidate","tickers":["09988.HK","00700.HK","NVDA","AVGO"]},
  {"id":"aastocks","type":"aggregator","market":"HK","access":"free_no_key","status":"candidate","tickers":["09988.HK","00700.HK"]},
 ]
 return {"phase121_news_event_registry":{"total":len(n),"news":n,"mock_used":False,"fixture_used":False}}
