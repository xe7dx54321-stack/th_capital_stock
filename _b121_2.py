import os
def w(p,c): os.makedirs(os.path.dirname(p),exist_ok=True); open(p,'w',encoding='utf-8').write(c)

# === 4. Source Candidate Registry ===
w('08_scripts/lib/smr_phase121_source_candidate_registry.py', '''def build_source_candidate_registry():
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
''')

# === 5. Official Filing Registry ===
w('08_scripts/lib/smr_phase121_official_filing_registry.py', '''def build_official_filing_registry():
 f=[
  {"id":"hkex_annual_report","market":"HK","type":"annual_report","access":"free_no_login","tickers":["09988.HK","00700.HK"]},
  {"id":"hkex_interim_report","market":"HK","type":"interim_report","access":"free_no_login","tickers":["09988.HK","00700.HK"]},
  {"id":"sec_10k","market":"US","type":"annual_report","access":"free_no_login","tickers":["NVDA","AVGO"]},
  {"id":"sec_10q","market":"US","type":"quarterly_report","access":"free_no_login","tickers":["NVDA","AVGO"]},
  {"id":"sec_8k","market":"US","type":"current_report","access":"free_no_login","tickers":["NVDA","AVGO"]},
  {"id":"cninfo_annual","market":"CN_A","type":"annual_report","access":"free_no_login","tickers":["300308.SZ","688041.SH","002230.SZ"]},
 ]
 return {"phase121_official_filing_registry":{"total":len(f),"filings":f,"mock_used":False,"fixture_used":False}}
''')

# === 6. Market Quote Registry ===
w('08_scripts/lib/smr_phase121_market_quote_registry.py', '''def build_market_quote_registry():
 q=[
  {"id":"yfinance_quote","market":"HK_US","access":"free_no_key","status":"existing","tickers":["09988.HK","00700.HK","NVDA","AVGO"]},
  {"id":"akshare_quote","market":"HK","access":"free_no_key","status":"existing","tickers":["09988.HK","00700.HK"]},
  {"id":"alphavantage_free","market":"US","access":"free_key_needed","status":"candidate","tickers":["NVDA","AVGO"]},
 ]
 return {"phase121_market_quote_registry":{"total":len(q),"quotes":q,"mock_used":False,"fixture_used":False}}
''')

# === 7. News/Event Registry ===
w('08_scripts/lib/smr_phase121_news_event_registry.py', '''def build_news_event_registry():
 n=[
  {"id":"hkex_announcements","type":"official","market":"HK","access":"free_no_key","status":"candidate","tickers":["09988.HK","00700.HK"]},
  {"id":"sec_press","type":"official","market":"US","access":"free_no_key","status":"candidate","tickers":["NVDA","AVGO"]},
  {"id":"finviz_news","type":"aggregator","market":"US","access":"free_no_key","status":"candidate","tickers":["NVDA","AVGO"]},
  {"id":"google_finance","type":"aggregator","market":"HK_US","access":"free_no_key","status":"candidate","tickers":["09988.HK","00700.HK","NVDA","AVGO"]},
  {"id":"aastocks","type":"aggregator","market":"HK","access":"free_no_key","status":"candidate","tickers":["09988.HK","00700.HK"]},
 ]
 return {"phase121_news_event_registry":{"total":len(n),"news":n,"mock_used":False,"fixture_used":False}}
''')

# === 8. Transcript Registry ===
w('08_scripts/lib/smr_phase121_transcript_guidance_registry.py', '''def build_transcript_guidance_registry():
 t=[
  {"id":"fool_earnings","type":"transcript","market":"US","access":"free_no_key","tickers":["NVDA","AVGO"]},
  {"id":"seekingalpha","type":"transcript","market":"US","access":"free_limited","tickers":["NVDA","AVGO"]},
  {"id":"hkex_results","type":"guidance","market":"HK","access":"free_no_key","tickers":["09988.HK","00700.HK"]},
  {"id":"company_ir","type":"guidance","market":"HK_US","access":"manual","tickers":["09988.HK","00700.HK","NVDA","AVGO"]},
 ]
 return {"phase121_transcript_guidance_registry":{"total":len(t),"sources":t,"mock_used":False,"fixture_used":False}}
''')

print('4-8 done')