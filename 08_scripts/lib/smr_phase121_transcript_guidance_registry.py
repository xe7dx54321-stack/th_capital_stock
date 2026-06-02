def build_transcript_guidance_registry():
 t=[
  {"id":"fool_earnings","type":"transcript","market":"US","access":"free_no_key","tickers":["NVDA","AVGO"]},
  {"id":"seekingalpha","type":"transcript","market":"US","access":"free_limited","tickers":["NVDA","AVGO"]},
  {"id":"hkex_results","type":"guidance","market":"HK","access":"free_no_key","tickers":["09988.HK","00700.HK"]},
  {"id":"company_ir","type":"guidance","market":"HK_US","access":"manual","tickers":["09988.HK","00700.HK","NVDA","AVGO"]},
 ]
 return {"phase121_transcript_guidance_registry":{"total":len(t),"sources":t,"mock_used":False,"fixture_used":False}}
