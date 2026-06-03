def build_domain_registry():
 domains={
  "official_source_probe":{"desc":"Probe HKEX/SEC official filing endpoints","category":"official"},
  "third_party_source_probe":{"desc":"Probe Yahoo Finance/Finviz/MarketWatch/Futu","category":"third_party"},
  "quote_market_probe":{"desc":"Probe quote/market data endpoints","category":"quote_market"},
  "news_event_probe":{"desc":"Probe news/event endpoints","category":"news_event"},
  "transcript_guidance_probe":{"desc":"Probe transcript/guidance endpoints","category":"transcript_guidance"},
  "probe_result_normalizer":{"desc":"Normalize probe results to standard schema","category":"pipeline"},
  "availability_classifier":{"desc":"Classify source into available/blocked/manual_required/etc","category":"pipeline"},
  "failure_reason_classifier":{"desc":"Classify failure reasons","category":"pipeline"},
  "content_usability_checker":{"desc":"Check if probed content is usable","category":"pipeline"},
  "coverage_update_builder":{"desc":"Update source coverage matrix after probe","category":"pipeline"},
  "pending_closeout_report":{"desc":"Closeout pending_network status","category":"pipeline"},
  "validation_gap_register":{"desc":"Register remaining gaps after probe","category":"pipeline"},
  "integration_update":{"desc":"Update Phase121/122/126/127 after probe","category":"pipeline"},
  "validation_board":{"desc":"External source validation board","category":"output"},
  "validation_brief":{"desc":"External source validation brief","category":"output"},
  "validation_memory":{"desc":"Write validation evidence to memory","category":"output"},
  "cannot_conclude_guard":{"desc":"Guard against overclaim from probe results","category":"safety"},
  "backlog_update":{"desc":"Update backlog after phase128","category":"output"}
 }
 return {"phase128_domain_registry":{"total":len(domains),"all_research_only":True,"domains":{k:{**v,"research_only":True} for k,v in domains.items()},"mock_used":False,"fixture_used":False}}
