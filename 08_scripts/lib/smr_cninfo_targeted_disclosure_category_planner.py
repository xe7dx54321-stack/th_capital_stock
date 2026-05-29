#!/usr/bin/env python3
"""CNINFO targeted disclosure category planner - Phase 66."""
import json
from pathlib import Path
from typing import Any

PLAN_PATH=Path(__file__).resolve().parent.parent.parent/"config"/"cninfo_targeted_disclosure_categories_ai_optical.json"

def load_category_plan()->dict[str,Any]:
    if not PLAN_PATH.exists(): return {"priority_categories":[],"error":"plan not found"}
    with open(PLAN_PATH,"r",encoding="utf-8-sig") as f: return json.load(f)

def get_priority_order()->list[dict]:
    plan=load_category_plan()
    cats=plan.get("priority_categories",[])
    order={"P0":1,"P1":2,"P2":3}
    return sorted(cats,key=lambda c:order.get(c.get("priority",""),99))

def get_max_metadata_default()->int:
    plan=load_category_plan()
    return sum(c.get("max_sources",0) for c in plan.get("priority_categories",[]))
