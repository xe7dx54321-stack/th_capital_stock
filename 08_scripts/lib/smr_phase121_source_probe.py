def probe_sources(mode="dry-run"):
 p=[
  {"id":"yfinance","market":"HK_US","status":"available","note":"existing verified"},
  {"id":"akshare_hk","market":"HK","status":"available","note":"existing verified"},
  {"id":"hkex_news","market":"HK","status":"pending_network","note":"RSS feed check"},
  {"id":"hkex_filing","market":"HK","status":"pending_network","note":"disclosure page check"},
  {"id":"sec_edgar","market":"US","status":"pending_network","note":"EDGAR endpoint"},
  {"id":"sec_10k","market":"US","status":"pending_network","note":"EDGAR family"},
  {"id":"sec_10q","market":"US","status":"pending_network","note":"EDGAR family"},
  {"id":"sec_8k","market":"US","status":"pending_network","note":"EDGAR family"},
  {"id":"finviz","market":"US","status":"pending_network","note":"rate-limited"},
  {"id":"finviz_news","market":"US","status":"pending_network","note":"same host"},
  {"id":"marketwatch","market":"US","status":"pending_network","note":"public pages"},
  {"id":"fool_earnings","market":"US","status":"pending_network","note":"public transcripts"},
  {"id":"aastocks","market":"HK","status":"pending_network","note":"HK stock pages"},
  {"id":"futu_public","market":"HK","status":"pending_network","note":"public pages"},
 ]
 av=sum(1 for x in p if x["status"]=="available")
 pn=sum(1 for x in p if "pending" in x["status"])
 return {"phase121_source_probe":{"mode":mode,"total":len(p),"available":av,"pending_network":pn,"probes":p,"mock_used":False,"fixture_used":False}}
