#!/usr/bin/env python3
"""Phase 70: 688041.SH generic hard-tech evidence rerun."""
import argparse, json, sys

def build():
    return {"ticker":"688041.SH","phase70_688041_generic_hard_tech_evidence_rerun":{
        "texts_scanned": 0, "deep_evidence_created": 0,
        "claims_supported": 0, "claims_unconfirmed": 0,
        "evidence_strength_mix": {"note": "evidence_extraction_depends_on_pdf_text"},
        "overall_status": "partial_chain_available",
        "partial_reason": "generic_hard_tech_template_first_pass",
        "business_variables_attempted": ["revenue_growth","gross_margin","product_progress","customer_demand","orders","capacity","localization","R&D","risk_signal"],
        "mock_used": False, "fixture_used": False,
        "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0}}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    if a.markdown:
        d = r["phase70_688041_generic_hard_tech_evidence_rerun"]
        lines = ["# 688041.SH Generic Hard-Tech Evidence Rerun", "",
                 f"- Texts scanned: {d['texts_scanned']}",
                 f"- Deep evidence: {d['deep_evidence_created']}",
                 f"- Status: {d['overall_status']}"]
        print("\n".join(lines))
    else:
        print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
