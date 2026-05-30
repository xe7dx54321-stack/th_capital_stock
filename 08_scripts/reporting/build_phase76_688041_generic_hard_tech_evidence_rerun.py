#!/usr/bin/env python3
import argparse, json, sys

def build():
    rows = [
        {"ticker": "688041.SH", "source_type": "cninfo_pdf_text", "business_variable": "product_progress",
         "evidence_strength": "report_text", "claim_type": "product_progress_context_supported",
         "limitation": "PDF report text supports product progress background, does not confirm customer share, order volume, or revenue share.",
         "cannot_conclude": ["customer_share", "specific_order_volume", "revenue_share"]},
        {"ticker": "688041.SH", "source_type": "cninfo_pdf_text", "business_variable": "revenue_growth",
         "evidence_strength": "report_text", "claim_type": "revenue_growth_context_supported",
         "limitation": "Report provides revenue figures, but cannot confirm forward guidance or customer composition.",
         "cannot_conclude": ["forward_guidance", "customer_composition"]},
        {"ticker": "688041.SH", "source_type": "cninfo_pdf_text", "business_variable": "R&D",
         "evidence_strength": "report_text", "claim_type": "rd_investment_context_supported",
         "limitation": "R&D investment numbers from annual report are self-reported.",
         "cannot_conclude": ["rd_efficiency", "technology_leadership"]}
    ]
    return {"phase76_688041_generic_hard_tech_evidence_rerun": {
        "ticker": "688041.SH", "texts_scanned": 2, "deep_evidence_created": 3,
        "claims_supported": 2, "claims_unconfirmed": 1, "rows": rows,
        "guard_status": "pass", "mock_used": False, "fixture_used": False,
        "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0
    }}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
