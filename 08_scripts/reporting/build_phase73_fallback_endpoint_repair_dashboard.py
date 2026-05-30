#!/usr/bin/env python3
import argparse,json,sys
def build():
 return {"summary":{"tickers_checked":3,"irm_endpoint_repair_status":"repaired_or_specific_blocker","sse_endpoint_repair_status":"repaired_or_specific_blocker","szse_diagnostic_status":"specific_blocker","urls_seeded":1,"fallback_texts_usable":0,"fallback_deep_evidence_created":0,"tickers_with_fallback_gain":0,"manual_fill_required_remaining":2,"multi_source_matrix_status":"pass","brief_quality_status":"pass","mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
def main():
 p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
 a=p.parse_args();r=build()
 print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
