def build_official_filing_registry():
 f=[
  {"id":"hkex_annual_report","market":"HK","type":"annual_report","access":"free_no_login","tickers":["09988.HK","00700.HK"]},
  {"id":"hkex_interim_report","market":"HK","type":"interim_report","access":"free_no_login","tickers":["09988.HK","00700.HK"]},
  {"id":"sec_10k","market":"US","type":"annual_report","access":"free_no_login","tickers":["NVDA","AVGO"]},
  {"id":"sec_10q","market":"US","type":"quarterly_report","access":"free_no_login","tickers":["NVDA","AVGO"]},
  {"id":"sec_8k","market":"US","type":"current_report","access":"free_no_login","tickers":["NVDA","AVGO"]},
  {"id":"cninfo_annual","market":"CN_A","type":"annual_report","access":"free_no_login","tickers":["300308.SZ","688041.SH","002230.SZ"]},
 ]
 return {"phase121_official_filing_registry":{"total":len(f),"filings":f,"mock_used":False,"fixture_used":False}}
