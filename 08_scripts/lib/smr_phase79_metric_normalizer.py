#!/usr/bin/env python3
def normalize_metrics(metrics):
    normalized = []
    missing = []
    for m in metrics:
        if m.get("value_normalized") is None or m.get("extraction_confidence") == "low":
            missing.append({"metric_name": m["metric_name"], "period": m.get("period"), "reason": "low_confidence_or_not_found"})
            continue
        normalized.append({
            "metric_name": m["metric_name"],
            "period": m["period"],
            "period_type": m.get("period_type", "unknown"),
            "value_normalized": m["value_normalized"],
            "unit_normalized": m["unit_normalized"],
            "confidence": m.get("extraction_confidence", "medium")
        })
    return {
        "phase79_metric_normalization": {
            "metrics_checked": len(metrics),
            "metrics_normalized": len(normalized),
            "metrics_missing_or_low_confidence": len(missing),
            "rows": normalized,
            "missing": missing
        }
    }
