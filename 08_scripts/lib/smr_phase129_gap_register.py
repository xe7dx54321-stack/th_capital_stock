import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase129_fallback_probe_executor import execute_fallback_probe
from smr_phase129_manual_workflow_builder import build_manual_workflow

def build_gap_register(skip_network=False):
    probe=execute_fallback_probe(skip_network)["phase129_fallback_probe_executor"]
    manual=build_manual_workflow(skip_network)["phase129_manual_workflow_builder"]
    gaps=[]
    gaps.append({"id":"sec_8k_material_events","source":"SEC 8-K","tickers":["NVDA","AVGO"],"official_status":"blocked_cn","fallback":"finviz+marketwatch","fallback_coverage":"partial_news","remaining_gap":"raw_filing_text_not_available","severity":"low"})
    gaps.append({"id":"hkex_raw_filing","source":"HKEX filings","tickers":["09988.HK","00700.HK"],"official_status":"degraded_cn","fallback":"akshare+yfinance","fallback_coverage":"financial_data","remaining_gap":"raw_filing_document_not_available","severity":"low"})
    gaps.append({"id":"transcript_manual","source":"Earnings Transcript","tickers":["NVDA","AVGO","09988.HK","00700.HK"],"official_status":"manual_required","fallback":"finviz_news+manual","fallback_coverage":"partial","remaining_gap":"full_transcript_not_automated","severity":"medium"})
    gaps.append({"id":"300394_cninfo","source":"CNINFO","tickers":["300394.SZ"],"status":"retained_blocker","severity":"critical","retained_from_phase128":True})
    gaps.append({"id":"688041_valuation","source":"Owner Research","tickers":["688041.SH"],"status":"retained_partial","severity":"high","retained_from_phase128":True})
    return {"phase129_gap_register":{"total":len(gaps),"new_resolved":probe["available"],"still_manual":probe["manual_required"],"300394_retained":True,"688041_retained":True,"gaps":gaps,"mock_used":False,"fixture_used":False}}
