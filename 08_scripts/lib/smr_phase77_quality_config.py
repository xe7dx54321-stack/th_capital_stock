#!/usr/bin/env python3
import json
from pathlib import Path
CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "phase77_pdf_evidence_quality_rules.json"

def load(): 
    with open(CONFIG_PATH,"r",encoding="utf-8") as f: return json.load(f)

def get_reliability(doc_type):
    cfg = load()
    return cfg.get("source_reliability",{}).get(doc_type, 0.20)

def get_business_relevance(doc_type, text=""):
    cfg = load()
    rel = cfg.get("business_relevance_policy",{})
    txt = (text or "").lower()
    if doc_type == "legal_opinion": return "low"
    if doc_type == "shareholder_meeting_resolution": return "low"
    if doc_type in ("governance_policy","administrative_announcement"): return "low"
    if doc_type == "supervision_report": return "medium"
    if doc_type in ("annual_report","semiannual_report","quarterly_report"): return "high"
    high_kw = rel.get("high",[])
    if any(k in txt for k in high_kw): return "high"
    med_kw = rel.get("medium",[])
    if any(k in txt for k in med_kw): return "medium"
    return "low"

def get_evidence_strength(doc_type):
    cfg = load()
    pol = cfg.get("evidence_strength_policy",{})
    strong = pol.get("strong_direct",[])
    medium = pol.get("medium_context",[])
    weak = pol.get("weak_context",[])
    not_biz = pol.get("not_business_evidence",[])
    if doc_type in ("annual_report","quarterly_report"): return "strong_direct"
    if doc_type == "supervision_report": return "medium_context"
    if doc_type in ("legal_opinion","shareholder_meeting_resolution"): return "weak_context"
    return "weak_context"

def validate_config():
    cfg = load()
    checks = {}
    safety = cfg.get("safety",{})
    checks["mock_allowed"] = safety.get("mock_allowed",True) is False
    checks["fixture_allowed"] = safety.get("fixture_allowed",True) is False
    checks["ocr_allowed"] = safety.get("ocr_allowed",True) is False
    checks["raw_save_allowed"] = safety.get("raw_save_allowed",True) is False
    all_pass = all(checks.values())
    return {"all_pass":all_pass,"checks":checks}
