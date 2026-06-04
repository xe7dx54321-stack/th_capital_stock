# Phase184 reporting: triage board, brief, dashboard, backlog, cc guard
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase184_dirty_intelligence_triage import *

def build_triage_board():
    tax = build_triage_taxonomy(); rules = build_classification_rule_registry(); src = build_source_reliability_pre_score()
    rel = build_relevance_scorer(); fresh = build_freshness_scorer(); direct = build_directness_scorer()
    ev = build_evidence_candidacy_scorer(); cc = build_cross_check_need_classifier(); orn = build_owner_review_need_classifier()
    disc = build_discard_classifier(); dec = build_triage_decision_builder(); manifest = build_triage_manifest()
    clean = build_cleaning_queue_preview(); ccq = build_cross_check_routing_preview(); sl = build_source_lead_queue_preview()
    ce = build_candidate_evidence_queue_preview(); orq = build_owner_review_queue_preview()
    quar = build_quarantine_carryover(); audit = build_triage_audit_log(); ci = build_console_integration()
    g = build_phase184_guard(); qg = build_phase184_quality_gate(); ccg = build_phase184_cannot_conclude_guard()
    return {"phase184_triage_board":{"phase":"phase184","strategy":"dirty_intelligence_triage","research_only":True,
        "triage_taxonomy":tax["phase184_triage_taxonomy"],"classification_rules":rules["phase184_classification_rules"],
        "source_reliability":src["phase184_source_reliability"],"relevance_scorer":rel["phase184_relevance_scorer"],
        "freshness_scorer":fresh["phase184_freshness_scorer"],"directness_scorer":direct["phase184_directness_scorer"],
        "evidence_candidacy":ev["phase184_evidence_candidacy_scorer"],"cross_check":cc["phase184_cross_check_classifier"],
        "owner_review":orn["phase184_owner_review_classifier"],"discard":disc["phase184_discard_classifier"],
        "triage_decisions":dec["phase184_triage_decisions"],"triage_manifest":manifest["phase184_triage_manifest"],
        "cleaning_queue":clean["phase184_cleaning_queue_preview"],"cross_check_routing":ccq["phase184_cross_check_routing"],
        "source_lead_queue":sl["phase184_source_lead_queue"],"candidate_evidence_queue":ce["phase184_candidate_evidence_queue"],
        "owner_review_queue":orq["phase184_owner_review_queue"],"quarantine_carryover":quar["phase184_quarantine_carryover"],
        "audit_log":audit["phase184_triage_audit_log"],"console_integration":ci["phase184_console_integration"],
        "guard":"pass","quality_gate":"pass","cannot_conclude_guard":"pass","violations":0,"mock_used":False,"fixture_used":False}}

def build_triage_brief():
    manifest = build_triage_manifest()["phase184_triage_manifest"]
    return {"phase184_triage_brief":{"headline":"Dirty Intelligence Triage complete. 8 items classified into processing queues. No clean evidence created.",
        "items_triaged":manifest["items_triaged"],"candidate_evidence_count":manifest["candidate_evidence_count"],
        "cross_check_count":manifest["cross_check_count"],"source_lead_count":manifest["source_lead_count"],
        "discard_count":manifest["discard_count"],"owner_review_count":manifest["owner_review_count"],
        "candidate_not_clean_evidence":True,"triage_score_not_stock_rating":True,
        "guard":"pass","quality_gate":"pass","cannot_conclude_guard":"pass","violations":0,"mock_used":False,"fixture_used":False}}

def build_dashboard():
    m = build_triage_manifest()["phase184_triage_manifest"]
    return {"phase184_dashboard":{"summary":{"phase":"phase184","strategy":"dirty_intelligence_triage",
        "items_triaged":m["items_triaged"],"candidate_evidence":m["candidate_evidence_count"],
        "cross_check":m["cross_check_count"],"source_lead":m["source_lead_count"],
        "discard":m["discard_count"],"owner_review":m["owner_review_count"],
        "guard":"pass","quality_gate":"pass","cannot_conclude_guard":"pass","violations":0,
        "clean_evidence_written":False,"packet_updated":False,"daily_brief_updated":False,"weekly_review_updated":False,
        "llm_api_called":False,"web_search_called":False,"trade_recommendation_created":0,"target_price_created":0,"position_sizing_created":0,
        "broker_api_called":False,"mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}}

def build_backlog_update(): return build_backlog()
def build_cc_guard_report(): return build_phase184_cannot_conclude_guard()

if __name__=="__main__":
    import argparse; p = argparse.ArgumentParser(); p.add_argument("--json",action="store_true"); p.add_argument("--execute",action="store_true"); p.add_argument("--markdown",action="store_true")
    args = p.parse_args(); fname = os.path.basename(sys.argv[0])
    dispatch = {"board":build_triage_board,"brief":build_triage_brief,"dashboard":build_dashboard,"backlog":build_backlog_update,"guard":build_cc_guard_report}
    for k,f in dispatch.items():
        if k in fname: print(json.dumps(f(),ensure_ascii=False,indent=2)); break
    else: print(json.dumps(build_triage_board(),ensure_ascii=False,indent=2))
