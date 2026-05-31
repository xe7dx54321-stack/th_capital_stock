import json,os
from datetime import datetime
def build_guidance_registry():
    sources=[
        {"source_id":"annual_report_mda","type":"disclosure","provides":"management_discussion_analysis","market":"CN_A,HK,US","network":True},
        {"source_id":"quarterly_report_commentary","type":"disclosure","provides":"quarterly_management_commentary","market":"CN_A","network":True},
        {"source_id":"earnings_call_transcript","type":"earnings","provides":"management_guidance_commentary","market":"US,HK","network":True,"note":"transcript_availability_varies"},
        {"source_id":"investor_day_presentation","type":"ir","provides":"strategic_guidance","market":"CN_A,HK,US","network":True},
        {"source_id":"performance_briefing","type":"ir","provides":"performance_briefing_qa","market":"CN_A","network":True,"blocked_tickers":["300394.SZ"]},
        {"source_id":"ir_interaction_record","type":"ir","provides":"investor_relations_qa","market":"CN_A","network":True,"blocked_tickers":["300394.SZ"]},
        {"source_id":"exchange_inquiry_reply","type":"regulatory","provides":"regulatory_inquiry_response","market":"CN_A","network":True,"blocked_tickers":["300394.SZ"]},
        {"source_id":"company_announcement_guidance","type":"disclosure","provides":"management_outlook_announcement","market":"CN_A,HK","network":True},
        {"source_id":"sec_filing_mda","type":"regulatory","provides":"management_discussion_analysis","market":"US","network":True},
        {"source_id":"hk_disclosure_guidance","type":"regulatory","provides":"HK_management_discussion","market":"HK","network":True},
        {"source_id":"existing_pdf_pool","type":"local","provides":"previously_extracted_guidance_text","market":"CN_A","network":False},
        {"source_id":"yfinance_management_news","type":"api","provides":"management_related_news","market":"HK,US","network":True},
        {"source_id":"manual_guidance_research","type":"manual","provides":"manual_guidance_collection","market":"CN_A,HK,US","network":False,"note":"manual_required"},
    ]
    return {"phase94_guidance_registry":{"generated_at":datetime.now().isoformat(),"guidance_sources":len(sources),"sources":sources,"mock_used":False,"fixture_used":False}}
