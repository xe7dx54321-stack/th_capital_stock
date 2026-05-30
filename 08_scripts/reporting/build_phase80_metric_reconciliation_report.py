#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"lib"))
from smr_phase80_report_metric_loader import load_report_metrics
from smr_phase80_structured_financial_metric_loader import load_structured_metrics
from smr_phase80_metric_reconciliation import reconcile_metrics
from smr_phase80_metric_consistency_checker import check_consistency
from smr_phase80_time_series_signal_builder import build_time_series_signals

def build_reconciliation():
    rm = load_report_metrics()["phase80_report_metric_loader"]["rows"]
    sm = load_structured_metrics()["phase80_structured_metric_loader"]["rows"]
    return reconcile_metrics(rm, sm)

def build_consistency():
    rec = build_reconciliation()
    return check_consistency(rec["phase80_metric_reconciliation"]["rows"])

def build_diagnostics():
    rec = build_reconciliation()
    rows = rec["phase80_metric_reconciliation"]["rows"]
    diag_rows = []
    reason_mix = {}
    for r in rows:
        if r["comparison_status"] in ("mismatch", "near_match", "report_only", "structured_only"):
            reason = "rounding_difference" if r.get("difference_pct") and r["difference_pct"] < 1 else ("YTD_vs_quarter_mismatch" if "YTD" in r.get("period","") else ("structured_value_missing" if r["comparison_status"] == "report_only" else "metric_definition_difference"))
            reason_mix[reason] = reason_mix.get(reason, 0) + 1
            diag_rows.append({"metric_name": r["metric_name"], "period": r["period"], "comparison_status": r["comparison_status"], "diagnostic_reason": reason, "allowed_next_action": "verify_source_and_period"})
    return {"phase80_metric_mismatch_diagnostics": {"ticker": "688041.SH", "items_diagnosed": len(diag_rows), "reason_mix": reason_mix, "rows": diag_rows, "mock_used": False, "fixture_used": False}}

def build_time_series():
    cons = build_consistency()
    rec = build_reconciliation()
    return build_time_series_signals(cons["phase80_metric_consistency"]["rows"], rec["phase80_metric_reconciliation"]["rows"])

def build_reconciliation_report():
    r = build_reconciliation(); r["phase80_metric_reconciliation"]["source"] = "main_report"; return r
