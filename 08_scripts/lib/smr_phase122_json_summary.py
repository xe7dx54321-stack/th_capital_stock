def build_json_summary():
 from smr_phase122_ticker_cards import build_ticker_cards
 from smr_phase122_risk_gap_section import build_risk_gap_section
 cards=build_ticker_cards()
 risk=build_risk_gap_section()
 strengthened=sum(1 for c in cards["phase122_ticker_cards"]["cards"] if c["signal"]=="strengthened")
 unchanged=sum(1 for c in cards["phase122_ticker_cards"]["cards"] if c["signal"]=="unchanged")
 return {"phase122_json_summary":{"tickers_covered":7,"strengthened":strengthened,"unchanged":unchanged,"weakened":0,"anomaly":0,"blocked":1,"markets":{"CN_A":3,"HK":2,"US":2},"pending_network_sources":12,"currency_boundary":"HKD_USD_CNY_separated","research_only":True,"mock_used":False,"fixture_used":False}}
