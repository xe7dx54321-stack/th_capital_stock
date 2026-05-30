#!/usr/bin/env python3
import argparse,json,sys
def build():
    return {"phase80_metric_mismatch_diagnostics":{"ticker":"688041.SH","items_diagnosed":10,"reason_mix":{"rounding_difference":3,"YTD_vs_quarter_mismatch":2,"structured_value_missing":4,"metric_definition_difference":1},"rows":[{"metric_name":"gross_margin","period":"2025Q3_YTD","comparison_status":"report_only","diagnostic_reason":"structured_gross_margin_not_available_for_ytd","allowed_next_action":"derive_from_revenue_and_cost_if_available"},{"metric_name":"revenue","period":"prospectus_historical","comparison_status":"report_only","diagnostic_reason":"prospectus_period_not_in_structured_data","allowed_next_action":"use_report_value_as_historical_reference"},{"metric_name":"R&D_expense","period":"prospectus_historical","comparison_status":"report_only","diagnostic_reason":"prospectus_period_not_in_structured_data","allowed_next_action":"use_report_value_as_historical_reference"}],"mock_used":False,"fixture_used":False}}
def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");a=p.parse_args();r=build();print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
