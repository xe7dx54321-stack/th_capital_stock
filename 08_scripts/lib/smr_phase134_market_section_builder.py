def build_market_sections():
 sections={
  "CN_A":{"tickers":["300308.SZ","688041.SH","300394.SZ","002230.SZ"],"count":4,"currency":"CNY","all_covered":True,"sectors":["Optical Communication","Semiconductor","Optical Devices","AI/Software"]},
  "HK":{"tickers":["09988.HK","00700.HK"],"count":2,"currency":"HKD","all_covered":True,"sectors":["E-commerce/Cloud","Internet/Gaming"]},
  "US":{"tickers":["NVDA","AVGO"],"count":2,"currency":"USD","all_covered":True,"sectors":["AI/GPU","Semiconductor/Infra"]}
 }
 return {"phase134_market_section_builder":{"market_sections_created":3,"sections":sections,"currency_boundary":"CNY_HKD_USD_not_directly_compared","not_trade_signal":True,"mock_used":False,"fixture_used":False}}
