def build_connector_skeleton():
 c=[
  {"id":"hkex_rss","type":"rss","market":"HK","status":"skeleton","sources":["hkex_news","hkex_announcements"],"access":"free_public"},
  {"id":"sec_edgar","type":"http","market":"US","status":"skeleton","sources":["sec_10k","sec_10q","sec_8k"],"access":"free_public"},
  {"id":"finviz","type":"http","market":"US","status":"skeleton","sources":["finviz","finviz_news"],"access":"free_public"},
  {"id":"aastocks","type":"http","market":"HK","status":"skeleton","sources":["aastocks"],"access":"free_public"},
  {"id":"fool","type":"http","market":"US","status":"skeleton","sources":["fool_earnings"],"access":"free_public"},
 ]
 return {"phase121_connector_skeleton":{"total":len(c),"connectors":c,"mock_used":False,"fixture_used":False}}
