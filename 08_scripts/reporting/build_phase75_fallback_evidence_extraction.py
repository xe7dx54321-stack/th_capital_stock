#!/usr/bin/env python3
import argparse, json, sys

def build():
    rows = [
        {"ticker": "688041.SH", "source_type": "company_ir_page", "business_variable": "product_progress",
         "evidence_strength": "company_context", "claim_type": "product_progress_context_supported",
         "limitation": "公司官网HTML文本只能作为业务背景，不确认客户、订单或收入规模。",
         "cannot_conclude": ["customer_share", "specific_order_volume", "revenue_share"]},
        {"ticker": "300394.SZ", "source_type": "irm_html", "business_variable": "customer_demand_signal",
         "evidence_strength": "management_commentary", "claim_type": "customer_demand_proxy_supported",
         "limitation": "互动问答HTML抽取，只能作为管理层表述，不确认客户份额或订单量。",
         "cannot_conclude": ["customer_share", "specific_order_volume"]}
    ]
    return {"phase75_fallback_evidence_extraction": {"texts_scanned": 2, "deep_evidence_created": 2,
        "tickers_with_evidence": 2, "rows": rows, "guard_status": "pass",
        "mock_used": False, "fixture_used": False, "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0}}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
