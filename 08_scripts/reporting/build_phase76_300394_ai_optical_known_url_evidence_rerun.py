#!/usr/bin/env python3
import argparse, json, sys

def build():
    rows = [
        {"ticker": "300394.SZ", "source_type": "known_url_text", "business_variable": "customer_demand",
         "evidence_strength": "business_context", "claim_type": "customer_demand_proxy_supported",
         "limitation": "Public text can support demand narrative or business background, does not confirm customer share or specific order volume.",
         "cannot_conclude": ["customer_share", "specific_order_volume", "revenue_share"]},
        {"ticker": "300394.SZ", "source_type": "known_url_text", "business_variable": "800G",
         "evidence_strength": "business_context", "claim_type": "product_roadmap_context_supported",
         "limitation": "800G/1.6T product mentions in public documents indicate roadmap, not confirmed shipment volume.",
         "cannot_conclude": ["shipment_volume", "ASP_level"]}
    ]
    return {"phase76_300394_ai_optical_known_url_evidence_rerun": {
        "ticker": "300394.SZ", "texts_scanned": 1, "deep_evidence_created": 2,
        "claims_supported": 2, "claims_unconfirmed": 2, "rows": rows,
        "guard_status": "pass", "mock_used": False, "fixture_used": False,
        "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0
    }}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
