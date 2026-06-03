import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase128_pending_source_loader import load_pending_sources
def plan_probe_targets():
 sources=load_pending_sources()["phase128_pending_source_loader"]["sources"]
 targets=[]
 for s in sources:
  t={"source_id":s["id"],"type":s["type"],"market":s["market"],"access":s["access"],"tickers":s["tickers"]}
  if s["id"]=="hkex_news": t.update({"probe_url":"https://www.hkexnews.hk","method":"HEAD","category":"official"})
  elif s["id"]=="hkex_filing": t.update({"probe_url":"https://www.hkexnews.hk/index.htm","method":"HEAD","category":"official"})
  elif s["id"]=="sec_edgar": t.update({"probe_url":"https://www.sec.gov/cgi-bin/browse-edgar","method":"HEAD","category":"official"})
  elif s["id"]=="sec_10k": t.update({"probe_url":"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=NVDA&type=10-K","method":"HEAD","category":"official"})
  elif s["id"]=="sec_10q": t.update({"probe_url":"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=NVDA&type=10-Q","method":"HEAD","category":"official"})
  elif s["id"]=="sec_8k": t.update({"probe_url":"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=NVDA&type=8-K","method":"HEAD","category":"official"})
  elif s["id"]=="yfinance": t.update({"probe_url":"https://finance.yahoo.com","method":"HEAD","category":"third_party"})
  elif s["id"]=="akshare_hk": t.update({"probe_url":"https://pypi.org/project/akshare","method":"HEAD","category":"third_party","note":"library_already_in_use"})
  elif s["id"]=="finviz": t.update({"probe_url":"https://finviz.com","method":"HEAD","category":"third_party"})
  elif s["id"]=="futu_public": t.update({"probe_url":"https://www.futunn.com","method":"HEAD","category":"third_party"})
  elif s["id"]=="marketwatch": t.update({"probe_url":"https://www.marketwatch.com","method":"HEAD","category":"third_party"})
  elif s["id"]=="transcript_guidance_manual": t.update({"probe_url":"N/A","method":"N/A","category":"transcript_guidance","note":"manual_aggregation_required"})
  targets.append(t)
 from smr_phase121_source_gap_register import build_source_gap_register
 gaps=build_source_gap_register()
 return {"phase128_probe_target_planner":{"total":len(targets),"targets":targets,"known_gaps":gaps,"mock_used":False,"fixture_used":False}}
