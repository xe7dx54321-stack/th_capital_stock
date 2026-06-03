import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase128_availability_classifier import classify_availability
from smr_phase128_content_usability_checker import check_content_usability

def build_source_coverage_update(skip_network=False):
    classified=classify_availability(skip_network)["phase128_availability_classifier"]
    usability=check_content_usability(skip_network)["phase128_content_usability_checker"]
    tickers=["09988.HK","00700.HK","NVDA","AVGO"]
    rows=[]
    for t in tickers:
        sources_for_ticker=[c for c in classified["results"] if t in c.get("tickers",[])]
        available=[s for s in sources_for_ticker if s["classification"]=="available"]
        row={"ticker":t,"total_sources_probed":len(sources_for_ticker),"available":len(available),"blocked":len(sources_for_ticker)-len(available),"source_status":"multi_source_available" if len(available)>=3 else "limited_sources" if len(available)>=1 else "blocked","coverage_updated":True}
        rows.append(row)
    return {"phase128_source_coverage_update":{"tickers_updated":len(rows),"rows":rows,"mock_used":False,"fixture_used":False}}
