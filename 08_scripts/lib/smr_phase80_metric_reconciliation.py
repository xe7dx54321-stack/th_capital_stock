#!/usr/bin/env python3
def reconcile_metrics(report_metrics, structured_metrics):
    tolerance_map = {"revenue": 3.0, "net_profit": 5.0, "gross_margin": 2.0, "R&D_expense": 5.0, "operating_cash_flow": 5.0}
    results = []
    matched = near_match = mismatch = report_only = structured_only = 0
    for rm in report_metrics:
        mn = rm["metric_name"]; period = rm["period"]; rv = rm["value_normalized"]
        sm_list = [s for s in structured_metrics if s["metric_name"] == mn and s["period"] == period]
        if not sm_list:
            report_only += 1
            results.append({"metric_name": mn, "period": period, "report_value": rv, "structured_value": None, "unit": rm["unit_normalized"], "difference_pct": None, "comparison_status": "report_only", "confidence": "low", "reason": "structured_value_not_available_for_period"})
            continue
        sm = sm_list[0]; sv = sm["value_normalized"]
        if sv is None:
            report_only += 1
            results.append({"metric_name": mn, "period": period, "report_value": rv, "structured_value": None, "unit": rm["unit_normalized"], "difference_pct": None, "comparison_status": "report_only", "confidence": "low"})
            continue
        tol = tolerance_map.get(mn, 5.0)
        if sv != 0:
            diff = abs(rv - sv) / abs(sv) * 100
        else:
            diff = abs(rv - sv)
        status = "matched" if diff <= tol else ("near_match" if diff <= tol * 2 else "mismatch")
        conf = "high" if diff <= tol else ("medium" if diff <= tol * 2 else "low")
        if status == "matched": matched += 1
        elif status == "near_match": near_match += 1
        else: mismatch += 1
        results.append({"metric_name": mn, "period": period, "report_value": rv, "structured_value": sv, "unit": rm["unit_normalized"], "difference_pct": round(diff, 2), "comparison_status": status, "confidence": conf})
    for sm in structured_metrics:
        mn = sm["metric_name"]; period = sm["period"]
        if not any(r["metric_name"] == mn and r["period"] == period for r in results):
            structured_only += 1
            results.append({"metric_name": mn, "period": period, "report_value": None, "structured_value": sm["value_normalized"], "unit": sm["unit_normalized"], "difference_pct": None, "comparison_status": "structured_only", "confidence": "medium"})
    return {"phase80_metric_reconciliation": {"ticker": "688041.SH", "report_metrics_checked": len(report_metrics), "structured_metrics_checked": len(structured_metrics), "matched": matched, "near_match": near_match, "mismatch": mismatch, "report_only": report_only, "structured_only": structured_only, "rows": results, "mock_used": False, "fixture_used": False}}
