def build_transcript_fallback():
 strategies=[
  {"source_id":"transcript_guidance_manual","data_need":"earnings_call_transcript","fallback_1":"finviz_news","fallback_1_status":"available","fallback_1_note":"Finviz news aggregator covers earnings-related news, partial transcript equivalence"},
  {"source_id":"transcript_guidance_manual","data_need":"management_guidance","fallback_1":"marketwatch","fallback_1_status":"available","fallback_1_note":"MarketWatch covers management guidance summaries in news articles"},
  {"source_id":"transcript_guidance_manual","data_need":"conference_call_summary","fallback_1":"manual_required","fallback_1_status":"manual_required","fallback_1_note":"Full transcripts require Seeking Alpha or Motley Fool (free tier limited) or manual web search"},
 ]
 return {"phase129_transcript_fallback":{"total":len(strategies),"strategies":strategies,"resolution":"partial_third_party_available_with_manual_gap","transcript_full_manual_required":True,"guidance_partial_available":True,"mock_used":False,"fixture_used":False}}
