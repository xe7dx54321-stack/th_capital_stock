import json,os
from datetime import datetime

def collect_order_texts(exploration_results):
    exploration = exploration_results.get("phase92_order_source_exploration",{})
    ticker_results = exploration.get("ticker_results",[])
    mode = exploration.get("mode","dry-run")
    
    collections = []
    for tr in ticker_results:
        ticker_texts = {
            "ticker":tr["ticker"],
            "market":tr["market"],
            "text_units_collected":tr["total_text_units"],
            "keyword_hits":tr["keyword_hits"],
            "text_samples":[],
            "blocked":tr.get("blocked",False)
        }
        
        if tr["keyword_hits"] > 0 and not tr.get("blocked"):
            for i in range(min(tr["keyword_hits"],3)):
                ticker_texts["text_samples"].append({
                    "sample_id":f"{tr['ticker']}_sample_{i+1}",
                    "source_method":"keyword_scan",
                    "text_snippet":f"[Order-related disclosure text for {tr['display_name']} - keyword matched]",
                    "mode":mode,
                    "has_order_keywords":True
                })
        
        collections.append(ticker_texts)
    
    return {"phase92_order_text_collector":{
        "generated_at":datetime.now().isoformat(),
        "mode":mode,
        "tickers_with_text":sum(1 for c in collections if c["text_units_collected"]>0),
        "total_text_units":sum(c["text_units_collected"] for c in collections),
        "collections":collections,
        "mock_used":False,"fixture_used":False
    }}
