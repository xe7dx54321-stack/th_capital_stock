#!/usr/bin/env python3
import json
from pathlib import Path

TARGETS_PATH = Path(__file__).resolve().parents[2] / "config" / "phase78_688041_high_value_report_targets.json"

def load_targets():
    with open(TARGETS_PATH, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def build_harvest_plan():
    targets = load_targets()
    plan_rows = []
    for tr in targets.get("target_reports", []):
        plan_rows.append({
            "report_type": tr["report_type"],
            "priority": tr["priority"],
            "search_terms": tr["search_terms"],
            "status": "planned"
        })
    return {
        "phase78_688041_high_value_report_harvest_plan": {
            "ticker": targets.get("ticker", "688041.SH"),
            "company_name": targets.get("company_name", "海光信息"),
            "total_targets": len(plan_rows),
            "p0_targets": sum(1 for r in plan_rows if r["priority"] == "P0"),
            "p1_targets": sum(1 for r in plan_rows if r["priority"] == "P1"),
            "rows": plan_rows,
            "safety": targets.get("safety", {}),
            "mock_used": False,
            "fixture_used": False
        }
    }
