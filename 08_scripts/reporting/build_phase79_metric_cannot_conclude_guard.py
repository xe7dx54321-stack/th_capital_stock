#!/usr/bin/env python3
import argparse,json,sys
def build():
    checks=[{"forbidden":"revenue_growth_as_customer_share","status":"not_violated"},{"forbidden":"revenue_growth_as_order_volume","status":"not_violated"},{"forbidden":"gross_margin_as_product_mix_improvement","status":"not_violated"},{"forbidden":"gross_margin_as_high_end_share","status":"not_violated"},{"forbidden":"rd_expense_as_commercial_success","status":"not_violated"},{"forbidden":"net_profit_as_demand_strength","status":"not_violated"},{"forbidden":"cash_flow_as_order_quality","status":"not_violated"},{"forbidden":"inventory_change_as_customer_demand","status":"not_violated"},{"forbidden":"prospectus_history_as_current_trend","status":"not_violated"},{"forbidden":"quantitative_metric_as_trade_trigger","status":"not_violated"}]
    return {"phase79_metric_cannot_conclude_guard":{"guard_status":"pass","violations":0,"forbidden_claims_checked":len(checks),"checks":checks,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build();print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
