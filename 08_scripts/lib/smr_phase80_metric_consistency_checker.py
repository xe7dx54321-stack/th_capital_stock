#!/usr/bin/env python3
def check_consistency(reconciliation_rows):
    metric_groups = {}
    for row in reconciliation_rows:
        metric_groups.setdefault(row["metric_name"], []).append(row)
    results = []
    consistent = mostly = inconsistent = insufficient = 0
    for mn, rows in metric_groups.items():
        matched_count = sum(1 for r in rows if r["comparison_status"] == "matched")
        total = len(rows)
        if total == 0:
            insufficient += 1; results.append({"metric_name": mn, "consistency_status": "insufficient_data", "matched_periods": 0, "mismatch_periods": 0, "confidence": "low", "can_use_for_time_series": False})
            continue
        ratio = matched_count / total
        if ratio >= 0.8:
            status = "consistent"; consistent += 1; conf = "high"; can_use = True
        elif ratio >= 0.5:
            status = "mostly_consistent"; mostly += 1; conf = "medium"; can_use = True
        elif ratio > 0:
            status = "inconsistent"; inconsistent += 1; conf = "low"; can_use = False
        else:
            status = "insufficient_data"; insufficient += 1; conf = "low"; can_use = False
        mismatch_count = sum(1 for r in rows if r["comparison_status"] in ("mismatch", "report_only"))
        results.append({"metric_name": mn, "consistency_status": status, "matched_periods": matched_count, "mismatch_periods": mismatch_count, "confidence": conf, "can_use_for_time_series": can_use})
    return {"phase80_metric_consistency": {"ticker": "688041.SH", "metrics_checked": len(metric_groups), "consistent_metrics": consistent, "mostly_consistent_metrics": mostly, "inconsistent_metrics": inconsistent, "insufficient_data_metrics": insufficient, "rows": results, "mock_used": False, "fixture_used": False}}
