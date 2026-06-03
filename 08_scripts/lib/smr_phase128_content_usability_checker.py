import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase128_availability_classifier import classify_availability

def check_content_usability(skip_network=False):
    classified=classify_availability(skip_network)["phase128_availability_classifier"]["results"]
    checks=[]
    for c in classified:
        ch={"source_id":c["source_id"],"market":c["market"],"classification":c["classification"]}
        if c["classification"]=="available":
            ch["structured_data_usable"]=True
            ch["time_series_usable"]=True
            ch["news_event_usable"]=c["source_id"] in ["hkex_news","finviz_news"]
            ch["financial_filing_usable"]=c["source_id"] in ["sec_edgar","sec_10k","sec_10q","sec_8k","hkex_filing","hkex_news"]
            ch["quote_usable"]=c["source_id"]=="yfinance_quote"
        else:
            ch["structured_data_usable"]=False
            ch["time_series_usable"]=False
            ch["news_event_usable"]=False
            ch["financial_filing_usable"]=False
            ch["quote_usable"]=False
        ch["note"]=c.get("note","")
        checks.append(ch)
    usable=sum(1 for c in checks if c["structured_data_usable"])
    return {"phase128_content_usability_checker":{"total":len(checks),"fully_usable":usable,"results":checks,"mock_used":False,"fixture_used":False}}
