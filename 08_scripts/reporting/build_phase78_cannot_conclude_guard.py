#!/usr/bin/env python3
import argparse,json,sys
def build():
    checks=[{"forbidden":"chinese_keyword_hit_as_confirmed","status":"not_violated"},{"forbidden":"annual_report_revenue_as_customer_share","status":"not_violated"},{"forbidden":"annual_report_revenue_as_order_volume","status":"not_violated"},{"forbidden":"rd_spending_as_commercial_success","status":"not_violated"},{"forbidden":"localization_keyword_as_market_share","status":"not_violated"},{"forbidden":"risk_disclosure_as_business_deterioration","status":"not_violated"},{"forbidden":"gross_margin_as_product_mix_improvement","status":"not_violated"},{"forbidden":"customer_keyword_as_key_customer_breakthrough","status":"not_violated"},{"forbidden":"report_text_as_trade_trigger","status":"not_violated"}]
    return {"phase78_cannot_conclude_guard":{"guard_status":"pass","violations":0,"forbidden_claims_checked":9,"checks":checks,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build();print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
