import os, json

def w(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

# === 1. Config loader ===
w('08_scripts/lib/smr_phase121_config.py', '''import json,os
from pathlib import Path
def load_config():
 p=Path(__file__).resolve().parent.parent.parent/"config"/"phase121_external_source_expansion.json"
 with open(p,"r",encoding="utf-8") as fh: return json.load(fh)
''')

# === 2. Domain Registry ===
w('08_scripts/lib/smr_phase121_domain_registry.py', '''def build_domain_registry():
 d={"external_source_candidate_registry":{"desc":"source candidate registry"},"official_filing_registry":{"desc":"official filings"},"market_quote_registry":{"desc":"market quotes"},"news_event_registry":{"desc":"news events"},"transcript_guidance_registry":{"desc":"transcripts"},"source_access_policy":{"desc":"access policy"},"hk_external_adapter":{"desc":"HK adapter"},"us_external_adapter":{"desc":"US adapter"},"source_availability_probe":{"desc":"probe"},"source_coverage_matrix":{"desc":"coverage matrix"},"cross_source_reliability":{"desc":"reliability"}}
 return {"phase121_domain_registry":{"total":len(d),"all_research_only":True,"domains":{k:{**v,"research_only":True} for k,v in d.items()},"mock_used":False,"fixture_used":False}}
''')

# === 3. Target Universe ===
w('08_scripts/lib/smr_phase121_target_universe.py', '''def build_target_universe():
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
''')

print('1-3 done')