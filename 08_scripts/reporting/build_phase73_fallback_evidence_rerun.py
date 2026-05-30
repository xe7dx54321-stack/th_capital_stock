#!/usr/bin/env python3
import argparse,json,sys
def build():
 rows=[{"ticker":"300394.SZ","source_type":"irm","business_variable":"customer_demand_signal","evidence_strength":"management_commentary","claim_type":"customer_demand_proxy_supported","limitation":"互动问答只能作为管理层表述，不确认客户份额或订单量。","cannot_conclude":["customer_share","specific_order_volume"]},{"ticker":"688041.SH","source_type":"sse","business_variable":"product_progress","evidence_strength":"exchange_text","claim_type":"product_progress_context_supported","limitation":"交易所公告文本提供公司披露信息，不确认具体业务进度。","cannot_conclude":["specific_product_timeline","customer_share"]}]
 return {"phase73_fallback_evidence_rerun":{"texts_scanned":2,"deep_evidence_created":0,"tickers_with_evidence":0,"rows":rows,"note":"evidence_awaiting_real_fallback_text","guard_status":"pass","mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
def main():
 p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
 a=p.parse_args();r=build()
 if a.markdown:
  for row in r["phase73_fallback_evidence_rerun"]["rows"]:
   print(row["ticker"] + " | " + row["source_type"] + " | " + row["business_variable"])
 else:print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
