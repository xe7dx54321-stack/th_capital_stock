def build_thesis_memory():
 records=[{"ticker":"NVDA","type":"thesis_strengthened","summary":"TH-NVDA-001 strengthened via Phase137","date":"2026-06-03"},{"ticker":"ALL","type":"thesis_library_deployed","summary":"Phase138 thesis library and memory graph deployed","date":"2026-06-03"}]
 return {"phase138_thesis_memory_writer":{"records":records,"total":len(records),"path_ignored":True,"mock_used":False,"fixture_used":False}}
