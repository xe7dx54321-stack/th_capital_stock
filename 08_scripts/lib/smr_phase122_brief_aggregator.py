def build_brief_aggregator():
 from smr_phase122_load_phase117 import load_phase117_outputs
 from smr_phase122_load_phase121 import load_phase121_outputs
 from smr_phase122_load_phase116 import load_phase116_outputs
 from smr_phase122_load_phase115 import load_phase115_outputs
 from smr_phase122_load_phase114 import load_phase114_outputs
 p117=load_phase117_outputs();p121=load_phase121_outputs();p116=load_phase116_outputs()
 p115=load_phase115_outputs();p114=load_phase114_outputs()
 return {"phase122_brief_aggregator":{"inputs_loaded":5,"modules":["phase117_master","phase121_sources","phase116_watchlist","phase115_candidates","phase114_catalyst"],"aggregation_status":"ready","research_only":True,"mock_used":False,"fixture_used":False}}
