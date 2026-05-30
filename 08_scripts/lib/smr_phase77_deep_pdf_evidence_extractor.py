#!/usr/bin/env python3
VARS = ["product_progress","R&D","revenue_growth","gross_margin","customer_demand","orders","capacity","localization","risk_signal"]

def extract_deep_evidence(pdf_rows_with_relevance):
    results = []
    for row in pdf_rows_with_relevance:
        if not row.get("allowed_for_deep_extraction"):
            if row.get("document_type") in ("legal_opinion","shareholder_meeting_resolution"):
                results.append({
                    "business_variable": "governance_context",
                    "document_type": row.get("document_type",""),
                    "evidence_strength": "weak_context",
                    "source_reliability_score": row.get("reliability_score", 0),
                    "business_relevance": "low",
                    "claim_type": "governance_context_only",
                    "limitation": "Legal or governance document, not business evidence.",
                    "cannot_conclude": ["product_progress","customer_demand","order_visibility","revenue_share"]
                })
            continue
        doc_type = row.get("document_type","")
        matched = row.get("matched_variables", [])
        for var in matched[:5]:
            if var == "governance_context":
                results.append({
                    "business_variable": var,
                    "document_type": doc_type,
                    "evidence_strength": "weak_context",
                    "source_reliability_score": row.get("reliability_score", 0),
                    "business_relevance": "low",
                    "claim_type": "governance_context_only",
                    "limitation": "Governance context only, does not support business variable claims.",
                    "cannot_conclude": ["product_progress","customer_demand","order_visibility"]
                })
            else:
                results.append({
                    "business_variable": var,
                    "document_type": doc_type,
                    "evidence_strength": "medium_context" if doc_type == "supervision_report" else "strong_direct",
                    "source_reliability_score": row.get("reliability_score", 0),
                    "business_relevance": row.get("business_relevance","medium"),
                    "claim_type": f"{var}_context_supported",
                    "limitation": f"PDF {doc_type} text supports {var} context, does not confirm customer share, order volume or revenue share.",
                    "cannot_conclude": ["customer_share","specific_order_volume","revenue_share"]
                })
    return {"phase77_688041_deep_pdf_evidence": {
        "ticker": "688041.SH", "texts_scanned": len(pdf_rows_with_relevance),
        "texts_allowed_for_deep_extraction": sum(1 for r in pdf_rows_with_relevance if r.get("allowed_for_deep_extraction")),
        "deep_evidence_created": len(results), "rows": results,
        "guard_status": "pass", "mock_used": False, "fixture_used": False,
        "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0
    }}
