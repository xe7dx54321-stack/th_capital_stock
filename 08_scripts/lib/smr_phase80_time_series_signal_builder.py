#!/usr/bin/env python3
def build_time_series_signals(consistency_rows, reconciliation_rows):
    signal_metrics = {}
    for cr in consistency_rows:
        if cr.get("can_use_for_time_series"):
            mn = cr["metric_name"]
            related = [r for r in reconciliation_rows if r["metric_name"] == mn]
            values = []
            for r in related:
                v = r.get("report_value") or r.get("structured_value")
                if v is not None: values.append({"period": r["period"], "value": v})
            if values:
                latest = values[-1]
                yoy = None
                if len(values) >= 2:
                    pv = values[-2]["value"]
                    if pv and pv != 0: yoy = round((latest["value"] - pv) / abs(pv) * 100, 1)
                trend = "improving" if yoy and yoy > 5 else ("declining" if yoy and yoy < -5 else "stable")
                anomaly = False
                if len(values) >= 3:
                    avg = sum(v["value"] for v in values[:-1]) / (len(values) - 1)
                    if avg and abs(avg) > 0 and abs((latest["value"] - avg) / avg * 100) > 30:
                        anomaly = True
                cannot_conclude_map = {"revenue": ["customer_share", "specific_order_volume"], "gross_margin": ["product_mix_confirmed"], "R&D_expense": ["commercial_success"], "net_profit": ["demand_strength"], "operating_cash_flow": ["order_quality"]}
                signal_metrics[mn] = {"metric_name": mn, "periods_count": len(values), "latest_period": latest["period"], "latest_value": latest["value"], "yoy_change": yoy, "trend_direction": trend, "anomaly_flag": anomaly, "signal_confidence": cr.get("confidence", "medium"), "can_support": [f"{mn}_observed"], "cannot_conclude": cannot_conclude_map.get(mn, [])}
    return {"phase80_time_series_signal": {"ticker": "688041.SH", "signals_created": len(signal_metrics), "rows": list(signal_metrics.values()), "mock_used": False, "fixture_used": False}}
