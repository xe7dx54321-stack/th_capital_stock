#!/usr/bin/env python3
def build_quantitative_evidence(normalized_metrics):
    rows = []
    for m in normalized_metrics:
        mn = m["metric_name"]
        period = m["period"]
        evidence_type = "financial_metric_observed"
        claim_type = f"{mn}_observed"
        limitation_map = {
            "revenue": "revenue figure reflects reported period, does not confirm customer share or order volume",
            "gross_profit": "gross profit reflects reported period, does not confirm product mix improvement",
            "gross_margin": "gross margin reflects reported period, does not confirm product mix or high-end product share improvement",
            "net_profit": "net profit reflects reported period, does not confirm demand strength",
            "R&D_expense": "R&D expense reflects R&D investment level, does not confirm commercial success or product launch",
            "R&D_expense_ratio": "R&D expense ratio reflects R&D intensity, does not confirm technology leadership",
            "operating_cash_flow": "cash flow reflects reported period, does not confirm order quality",
            "inventory": "inventory level reflects reported balance sheet, does not confirm customer demand",
            "accounts_receivable": "receivable level reflects reported balance sheet, does not confirm order volume",
        }
        cannot_conclude_map = {
            "revenue": ["customer_share", "specific_order_volume"],
            "gross_profit": ["product_mix_improvement"],
            "gross_margin": ["product_mix_improvement", "high_end_product_share"],
            "net_profit": ["demand_strength"],
            "R&D_expense": ["commercial_success", "product_launch"],
            "R&D_expense_ratio": ["technology_leadership"],
            "operating_cash_flow": ["order_quality"],
            "inventory": ["customer_demand"],
            "accounts_receivable": ["order_volume"],
        }
        rows.append({
            "metric_name": mn,
            "period": period,
            "value_normalized": m["value_normalized"],
            "unit_normalized": m["unit_normalized"],
            "evidence_type": evidence_type,
            "claim_type": claim_type,
            "limitation": limitation_map.get(mn, "financial metric observed, limitations apply"),
            "cannot_conclude": cannot_conclude_map.get(mn, [])
        })
    return {
        "phase79_quantitative_evidence": {
            "ticker": "688041.SH",
            "metrics_used": len(normalized_metrics),
            "quantitative_evidence_created": len(rows),
            "rows": rows,
            "mock_used": False,
            "fixture_used": False
        }
    }
