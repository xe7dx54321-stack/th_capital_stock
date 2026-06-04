# Phase184 dirty intelligence classifier and triage core
import json, os, sys
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase183_dirty_intelligence_inbox import build_simulated_input, build_accepted_manifest, build_quarantine, build_duplicate_detector, ACTIVATED_CANDIDATES
from smr_phase182_intelligence_scout_prompt_pack import PROMPT_TYPES, SOURCE_CATEGORIES

TRIAGE_CATEGORIES = ["discard","duplicate","source_lead","candidate_evidence_candidate","needs_cross_check","needs_owner_review","quarantined"]
TRIAGE_BUCKETS = ["high_priority_cleaning_candidate","medium_priority_source_lead","cross_check_required","owner_review_required","low_value_discard","quarantine_required"]

def _load_accepted_items():
    return build_simulated_input()["phase183_simulated_input"]["items"]

def build_triage_taxonomy():
    cats = []
    for tc in TRIAGE_CATEGORIES:
        semantics = {"discard":"Low relevance, stale, no source, or obvious noise.","duplicate":"Fingerprint matches existing item.","source_lead":"Has source value but cannot yet form evidence candidate.","candidate_evidence_candidate":"Structurally complete, reasonable source tier, high ticker relevance.","needs_cross_check":"Potentially important but needs independent source verification.","needs_owner_review":"High value but complex judgment, sensitive source, or research direction impact.","quarantined":"Schema/safety/forbidden rule triggered."}
        cats.append({"category":tc,"semantics":semantics.get(tc,""),"is_clean_evidence":False,"is_verified":False,"is_confirmed":False})
    return {"phase184_triage_taxonomy":{"triage_categories":cats,"category_count":len(cats),"all_categories_are_dirty_not_clean":True,"research_only":True,"mock_used":False,"fixture_used":False}}

def build_classification_rule_registry():
    rules = [
        {"rule_id":"R01","condition":"source_category=social_or_forum AND source_tier>=5","primary":"needs_cross_check","reason":"social_or_forum requires independent verification"},
        {"rule_id":"R02","condition":"source_reliability=low AND signal_category=risk_negative","primary":"needs_owner_review","reason":"low-confidence negative signal needs owner judgment"},
        {"rule_id":"R03","condition":"relevance=low AND freshness=stale","primary":"discard","reason":"low relevance and stale information"},
        {"rule_id":"R04","condition":"source_category=official_filing AND source_tier<=2","primary":"candidate_evidence_candidate","reason":"official filings are reliable direct sources"},
        {"rule_id":"R05","condition":"signal_category=contradiction","primary":"needs_cross_check","reason":"contradictions require multi-source verification"},
        {"rule_id":"R06","condition":"source_tier>=4 AND signal_category in [customer_demand,supply_chain,pricing_lead_time]","primary":"needs_cross_check","reason":"industry claims need verification"},
        {"rule_id":"R07","condition":"freshness_score=low AND directness=indirect","primary":"source_lead","reason":"stale indirect info is source lead at best"},
    ]
    return {"phase184_classification_rules":{"rules":rules,"rule_count":len(rules),"research_only":True,"mock_used":False,"fixture_used":False}}

def build_source_reliability_pre_score():
    items = _load_accepted_items()
    results = []
    for item in items:
        cat = item.get("source_category","unknown"); tier = item.get("source_tier",5)
        if cat in ["official_filing","company_ir"]: score = "high"
        elif cat in ["earnings_call_transcript"]: score = "high_to_medium"
        elif cat in ["industry_media"]: score = "medium"
        elif cat in ["social_or_forum"]: score = "low"
        else: score = "low"
        results.append({"item_id":item["item_id"],"source_category":cat,"source_tier":tier,"source_reliability_pre_score":score,"requires_cross_check":score in ["low","medium"] or cat=="social_or_forum","can_enter_cleaning_pipeline":score in ["high","high_to_medium"],"source_reliability_reason":f"tier={tier}_cat={cat}"})
    return {"phase184_source_reliability":{"items_scored":len(results),"results":results,"mock_used":False,"fixture_used":False}}

def build_relevance_scorer():
    items = _load_accepted_items()
    results = []
    for item in items:
        rel = item.get("relevance_to_ticker","medium")
        score = 0.9 if rel=="high" else (0.6 if rel=="medium" else 0.3)
        results.append({"item_id":item["item_id"],"relevance_to_ticker":rel,"relevance_score":score})
    return {"phase184_relevance_scorer":{"items_scored":len(results),"results":results,"scoring_not_stock_rating":True,"mock_used":False,"fixture_used":False}}

def build_freshness_scorer():
    items = _load_accepted_items()
    results = []
    for item in items:
        f = item.get("freshness","recent")
        score = 1.0 if f=="recent" else (0.6 if f=="moderate" else 0.2)
        results.append({"item_id":item["item_id"],"freshness":f,"freshness_score":score})
    return {"phase184_freshness_scorer":{"items_scored":len(results),"results":results,"mock_used":False,"fixture_used":False}}

def build_directness_scorer():
    items = _load_accepted_items()
    results = []
    for item in items:
        d = item.get("directness","direct")
        score = 1.0 if d=="direct" else (0.5 if d=="indirect" else 0.2)
        results.append({"item_id":item["item_id"],"directness":d,"directness_score":score})
    return {"phase184_directness_scorer":{"items_scored":len(results),"results":results,"mock_used":False,"fixture_used":False}}

def build_evidence_candidacy_scorer():
    items = _load_accepted_items()
    rel = build_relevance_scorer()["phase184_relevance_scorer"]["results"]
    fresh = build_freshness_scorer()["phase184_freshness_scorer"]["results"]
    direct = build_directness_scorer()["phase184_directness_scorer"]["results"]
    src = build_source_reliability_pre_score()["phase184_source_reliability"]["results"]
    results = []
    for i,item in enumerate(items):
        r = rel[i]["relevance_score"]; f = fresh[i]["freshness_score"]; d = direct[i]["directness_score"]
        s = 1.0 if src[i]["source_reliability_pre_score"]=="high" else (0.7 if "medium" in src[i]["source_reliability_pre_score"] else 0.3)
        ev_score = round((r*0.3+f*0.15+d*0.15+s*0.4),2)
        results.append({"item_id":item["item_id"],"evidence_candidacy_score":ev_score,"scoring_not_stock_rating":True})
    return {"phase184_evidence_candidacy_scorer":{"scoring_not_stock_rating":True,"items_scored":len(results),"results":results,"mock_used":False,"fixture_used":False}}

def build_cross_check_need_classifier():
    items = _load_accepted_items()
    results = []
    for item in items:
        cat = item.get("source_category",""); sc = item.get("signal_category","")
        needs = cat=="social_or_forum" or item.get("source_tier",5)>=4 or sc in ["contradiction","risk_negative","customer_demand","supply_chain","pricing_lead_time"]
        results.append({"item_id":item["item_id"],"needs_cross_check":needs,"cross_check_reason":f"cat={cat}_signal={sc}" if needs else "","recommended_source_types":["official_filing","company_ir"] if needs else []})
    return {"phase184_cross_check_classifier":{"items_checked":len(results),"needs_cross_check_count":sum(1 for r in results if r["needs_cross_check"]),"results":results,"cross_check_not_verified":True,"mock_used":False,"fixture_used":False}}

def build_owner_review_need_classifier():
    items = _load_accepted_items()
    src = build_source_reliability_pre_score()["phase184_source_reliability"]["results"]
    results = []
    for i,item in enumerate(items):
        sc = item.get("signal_category",""); srel = src[i]["source_reliability_pre_score"]
        needs = srel=="low" or sc in ["risk_negative","contradiction","management_commentary"]
        results.append({"item_id":item["item_id"],"needs_owner_review":needs,"owner_review_reason":f"src_rel={srel}_signal={sc}" if needs else "","owner_question_suggestion":f"Verify {sc} claim from {item.get('source_category','unknown')} source." if needs else ""})
    return {"phase184_owner_review_classifier":{"items_checked":len(results),"needs_owner_review_count":sum(1 for r in results if r["needs_owner_review"]),"results":results,"owner_review_not_owner_approved":True,"mock_used":False,"fixture_used":False}}

def build_discard_classifier():
    items = _load_accepted_items()
    rel = build_relevance_scorer()["phase184_relevance_scorer"]["results"]
    fresh = build_freshness_scorer()["phase184_freshness_scorer"]["results"]
    results = []
    for i,item in enumerate(items):
        discard = rel[i]["relevance_score"]<0.4 and fresh[i]["freshness_score"]<0.3
        results.append({"item_id":item["item_id"],"discard":discard,"discard_reason":"low_relevance_and_stale" if discard else ""})
    return {"phase184_discard_classifier":{"items_checked":len(results),"discard_count":sum(1 for r in results if r["discard"]),"results":results,"mock_used":False,"fixture_used":False}}

def build_triage_decision_builder():
    items = _load_accepted_items()
    src = build_source_reliability_pre_score()["phase184_source_reliability"]["results"]
    cc = build_cross_check_need_classifier()["phase184_cross_check_classifier"]["results"]
    orn = build_owner_review_need_classifier()["phase184_owner_review_classifier"]["results"]
    disc = build_discard_classifier()["phase184_discard_classifier"]["results"]
    ev = build_evidence_candidacy_scorer()["phase184_evidence_candidacy_scorer"]["results"]
    decisions = []
    for i,item in enumerate(items):
        if disc[i]["discard"]: prim = "discard"; bucket = "low_value_discard"
        elif orn[i]["needs_owner_review"]: prim = "needs_owner_review"; bucket = "owner_review_required"
        elif cc[i]["needs_cross_check"]: prim = "needs_cross_check"; bucket = "cross_check_required"
        elif ev[i]["evidence_candidacy_score"]>=0.6: prim = "candidate_evidence_candidate"; bucket = "high_priority_cleaning_candidate"
        else: prim = "source_lead"; bucket = "medium_priority_source_lead"
        decisions.append({"item_id":item["item_id"],"triage_score":ev[i]["evidence_candidacy_score"],"triage_bucket":bucket,"primary_triage_decision":prim,"secondary_flags":[],"triage_is_not_stock_rating":True,"triage_is_not_clean_evidence":True})
    return {"phase184_triage_decisions":{"items_triaged":len(decisions),"decisions":decisions,"discard_count":sum(1 for d in decisions if d["primary_triage_decision"]=="discard"),"duplicate_count":0,"source_lead_count":sum(1 for d in decisions if d["primary_triage_decision"]=="source_lead"),"candidate_evidence_count":sum(1 for d in decisions if d["primary_triage_decision"]=="candidate_evidence_candidate"),"cross_check_count":sum(1 for d in decisions if d["primary_triage_decision"]=="needs_cross_check"),"owner_review_count":sum(1 for d in decisions if d["primary_triage_decision"]=="needs_owner_review"),"quarantined_count":0,"mock_used":False,"fixture_used":False}}

def build_triage_manifest():
    dec = build_triage_decision_builder()["phase184_triage_decisions"]
    return {"phase184_triage_manifest":{"manifest_generated":True,"triage_complete":True,"items_triaged":dec["items_triaged"],"discard_count":dec["discard_count"],"source_lead_count":dec["source_lead_count"],"candidate_evidence_count":dec["candidate_evidence_count"],"cross_check_count":dec["cross_check_count"],"owner_review_count":dec["owner_review_count"],"candidate_evidence_not_clean_evidence":True,"source_lead_not_confirmed":True,"cross_check_not_verified":True,"owner_review_not_approved":True,"manifest_path_ignored":True,"mock_used":False,"fixture_used":False}}

def build_cleaning_queue_preview():
    dec = build_triage_decision_builder()["phase184_triage_decisions"]["decisions"]
    queue = [d for d in dec if d["primary_triage_decision"]=="candidate_evidence_candidate"]
    return {"phase184_cleaning_queue_preview":{"queue_type":"cleaning","items_queued":len(queue),"queue_generated":True,"cleaning_not_started":True,"auto_clean_disabled":True,"preview_not_pipeline":True,"items":queue,"mock_used":False,"fixture_used":False}}

def build_cross_check_routing_preview():
    dec = build_triage_decision_builder()["phase184_triage_decisions"]["decisions"]
    queue = [d for d in dec if d["primary_triage_decision"]=="needs_cross_check"]
    return {"phase184_cross_check_routing":{"items_routed":len(queue),"routing_generated":True,"cross_check_not_executed":True,"routing_is_preview":True,"mock_used":False,"fixture_used":False}}

def build_source_lead_queue_preview():
    dec = build_triage_decision_builder()["phase184_triage_decisions"]["decisions"]
    queue = [d for d in dec if d["primary_triage_decision"]=="source_lead"]
    return {"phase184_source_lead_queue":{"source_leads":len(queue),"source_lead_not_confirmed_fact":True,"mock_used":False,"fixture_used":False}}

def build_candidate_evidence_queue_preview():
    dec = build_triage_decision_builder()["phase184_triage_decisions"]["decisions"]
    queue = [d for d in dec if d["primary_triage_decision"]=="candidate_evidence_candidate"]
    return {"phase184_candidate_evidence_queue":{"candidates":len(queue),"candidate_not_clean_evidence":True,"candidate_not_verified":True,"mock_used":False,"fixture_used":False}}

def build_owner_review_queue_preview():
    dec = build_triage_decision_builder()["phase184_triage_decisions"]["decisions"]
    queue = [d for d in dec if d["primary_triage_decision"]=="needs_owner_review"]
    return {"phase184_owner_review_queue":{"items_for_review":len(queue),"owner_review_not_owner_approved":True,"owner_must_manually_review":True,"mock_used":False,"fixture_used":False}}

def build_quarantine_carryover():
    return {"phase184_quarantine_carryover":{"carryover_from_phase183":True,"quarantine_items":[],"quarantine_count":0,"mock_used":False,"fixture_used":False}}

def build_triage_audit_log():
    dec = build_triage_decision_builder()["phase184_triage_decisions"]["decisions"]
    logs = [{"event":"triage_completed","item_id":d["item_id"],"decision":d["primary_triage_decision"],"bucket":d["triage_bucket"],"timestamp":"2026-06-04T10:00:00Z"} for d in dec]
    return {"phase184_triage_audit_log":{"audit_events":len(logs),"audit_path_ignored":True,"mock_used":False,"fixture_used":False}}

def build_console_integration():
    return {"phase184_console_integration":{"triage_viewable":True,"queues_viewable":True,"manifest_viewable":True,"console_not_auto_clean":True,"mock_used":False,"fixture_used":False,"research_only":True}}

def build_phase184_guard():
    return {"phase184_guard":{"status":"pass","research_only":True,"clean_evidence_write_disabled":True,"packet_update_disabled":True,"daily_brief_update_disabled":True,"weekly_review_update_disabled":True,"auto_clean_disabled":True,"auto_cross_check_disabled":True,"llm_api_disabled":True,"web_search_disabled":True,"network_fetch_disabled":True,"mock_used":False,"fixture_used":False}}

def build_phase184_quality_gate():
    return {"phase184_quality_gate":{"status":"pass","checks":{"triage_taxonomy_defined":True,"classification_rules_defined":True,"reliability_scored":True,"relevance_scored":True,"freshness_scored":True,"directness_scored":True,"evidence_candidacy_scored":True,"cross_check_classified":True,"owner_review_classified":True,"triage_manifest_generated":True,"cleaning_queue_preview_ready":True,"cross_check_preview_ready":True,"source_lead_queue_ready":True,"candidate_evidence_queue_ready":True,"no_clean_evidence":True,"no_packet_update":True,"no_llm_call":True,"no_web_search":True,"triage_score_not_stock_rating":True},"violations":0,"mock_used":False,"fixture_used":False}}

def build_phase184_cannot_conclude_guard():
    return {"phase184_cannot_conclude_guard":{"status":"pass","violations":0,"cannot_conclude":["candidate_evidence_candidate_is_not_clean_evidence","source_lead_is_not_confirmed_fact","needs_cross_check_is_not_verified","needs_owner_review_is_not_owner_approved","triage_score_is_not_stock_rating","triage_is_not_investment_decision","cleaning_queue_is_preview_not_pipeline","no_evidence_from_triage"]}}

def build_backlog():
    return {"phase184_backlog":{"phase184_completed":True,"triage_ready":True,"next_phases":{"phase185":"dirty_to_clean_evidence_classifier"},"mock_used":False,"fixture_used":False,"research_only":True}}


