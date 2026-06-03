import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase128_official_source_probe import probe_official_sources
from smr_phase128_third_party_source_probe import probe_third_party_sources
from smr_phase128_quote_source_probe import probe_quote_sources
from smr_phase128_news_event_probe import probe_news_event_sources
from smr_phase128_transcript_guidance_probe import probe_transcript_guidance_sources

def normalize_probe_results(skip_network=False):
    official=probe_official_sources(skip_network)["phase128_official_source_probe"]["results"]
    third_party=probe_third_party_sources(skip_network)["phase128_third_party_source_probe"]["results"]
    quote=probe_quote_sources(skip_network)["phase128_quote_source_probe"]["results"]
    news=probe_news_event_sources(skip_network)["phase128_news_event_probe"]["results"]
    transcript=probe_transcript_guidance_sources(skip_network)["phase128_transcript_guidance_probe"]["results"]
    all_results=official+third_party+quote+news+transcript
    normalized=[]
    for r in all_results:
        n={"source_id":r["source_id"],"market":r.get("market",""),"tickers":r.get("tickers",[]),"probe_status":r.get("probe_status","unknown"),"reachable":r.get("reachable",False),"http_code":r.get("http_code"),"error":r.get("error"),"note":r.get("note",""),"raw_saved":False}
        normalized.append(n)
    available=sum(1 for n in normalized if n["probe_status"]=="available")
    blocked=sum(1 for n in normalized if n["probe_status"]=="blocked")
    manual=sum(1 for n in normalized if n["probe_status"]=="manual_required")
    skipped=sum(1 for n in normalized if n["probe_status"]=="skipped")
    return {"phase128_probe_result_normalizer":{"total":len(normalized),"available":available,"blocked":blocked,"manual_required":manual,"skipped":skipped,"results":normalized,"mock_used":False,"fixture_used":False,"raw_saved":False}}
