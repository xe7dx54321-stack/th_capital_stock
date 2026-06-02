def build_target_universe():
 rows=[
  {"ticker":"09988.HK","market":"HK","name":"Alibaba Group","status":"covered","existing_source":"yfinance","expansion_needed":True},
  {"ticker":"00700.HK","market":"HK","name":"Tencent Holdings","status":"covered","existing_source":"yfinance","expansion_needed":True},
  {"ticker":"NVDA","market":"US","name":"NVIDIA Corp","status":"covered","existing_source":"yfinance","expansion_needed":True},
  {"ticker":"AVGO","market":"US","name":"Broadcom Inc","status":"covered","existing_source":"yfinance","expansion_needed":True},
  {"ticker":"300308.SZ","market":"CN_A","name":"Zhongji Innolight","status":"covered","existing_source":"akshare","expansion_needed":False},
  {"ticker":"688041.SH","market":"CN_A","name":"Hygon Information","status":"covered_partial_valuation","existing_source":"akshare","expansion_needed":False},
  {"ticker":"002230.SZ","market":"CN_A","name":"iFlytek","status":"covered","existing_source":"akshare","expansion_needed":False},
  {"ticker":"300394.SZ","market":"CN_A","name":"Tianfu Communication","status":"blocked","existing_source":"none","expansion_needed":False,"blocker":"cninfo_org_id_missing"},
 ]
 return {"phase121_target_universe":{"tickers_total":len(rows),"hk_targets":2,"us_targets":2,"cn_a_covered":3,"cn_a_blocked":1,"rows":rows,"mock_used":False,"fixture_used":False}}
