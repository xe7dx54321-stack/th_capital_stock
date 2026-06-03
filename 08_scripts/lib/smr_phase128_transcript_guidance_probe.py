def probe_transcript_guidance_sources(skip_network=False):
    status="manual_required" if not skip_network else "skipped"
    note="earnings_call_transcripts_require_manual_aggregation_or_paid_api" if not skip_network else "skip_network_mode"
    return {"phase128_transcript_guidance_probe":{"total":1,"available":0,"blocked":0,"manual_required":1 if not skip_network else 0,"skipped":1 if skip_network else 0,"results":[{"source_id":"transcript_guidance_manual","type":"transcript_guidance","market":"HK_US","tickers":["09988.HK","00700.HK","NVDA","AVGO"],"probe_status":status,"reachable":False,"note":note}],"mock_used":False,"fixture_used":False,"raw_saved":False}}
