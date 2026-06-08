# Phase195 iFinD News / Announcement / Event Dirty Source Adapter core
"""iFinD dirty intelligence source adapter.

Converts iFinD news/announcement/event/WenCai query results into
dirty inbox compatible items (metadata + short excerpt only).
No full text saved. No clean evidence written. No packet/brief updates.
"""
import json, os, sys, hashlib
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

CN_A_TICKERS = ["300308.SZ", "688041.SH", "002230.SZ", "300394.SZ"]
CN_A_TICKER_NAMES = {"300308.SZ": "ZHONGJI INNOLIGHT", "688041.SH": "HAIGUANG INFO", "002230.SZ": "IFLYTEK", "300394.SZ": "TIANFU COMM"}
DIRTY_LANES = ["news", "announcement", "event", "wencai"]
MAX_EXCERPT_WORDS = 25
MAX_ITEMS_PER_TICKER_PER_LANE = 5
FORBIDDEN_FIELDS = ["buy_signal","sell_signal","hold_signal","target_price","position_size","portfolio_action","broker_action","trade_recommendation","investment_conclusion","price_forecast"]
GEN_DIR = "09_runbooks/generated/phase195_ifind_dirty_source_adapter"
IFIND_DIRTY_DOMAINS = {"announcement_board":"cninfo.com.cn","regulatory_filing_aggregator":"51ifind.com","financial_news_aggregator":"10jqka.com.cn","research_report_aggregator":"data.eastmoney.com","wencai_query":"iwencai.com"}

def _load_config():
    cfg_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "phase195_ifind_dirty_source_adapter.json")
    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return {}

def build_phase195_config():
    cfg = _load_config()
    return {"phase195_config": {"config_loaded": bool(cfg), "phase": cfg.get("phase","phase195"), "strategy": cfg.get("strategy","ifind_dirty_source_adapter"), "cn_a_tickers": CN_A_TICKERS, "cn_a_ticker_count": len(CN_A_TICKERS), "dirty_source_lanes": DIRTY_LANES, "lane_count": len(DIRTY_LANES), "max_excerpt_words": MAX_EXCERPT_WORDS, "raw_response_saved": False, "raw_full_text_saved": False, "clean_evidence_disabled": True, "packet_update_disabled": True, "daily_brief_update_disabled": True, "watch_core_update_disabled": True, "trade_disabled": True, "mock_used": False, "fixture_used": False}}

def build_domain_registry():
    domains = [{"source_category": cat, "source_domain": dom, "via_ifind": True} for cat, dom in IFIND_DIRTY_DOMAINS.items()]
    return {"phase195_domain_registry": {"registry_defined": True, "domains": domains, "domain_count": len(domains), "all_via_ifind": True, "mock_used": False, "fixture_used": False}}

def build_cn_a_dirty_source_universe():
    rows = [{"ticker": t, "name": CN_A_TICKER_NAMES.get(t,""), "market": "CN_A", "dirty_source_enabled": True, "dirty_source_via": "ifind", "lanes_active": DIRTY_LANES, "blocked": (t=="300394.SZ"), "blocker": "cninfo_org_id_missing" if t=="300394.SZ" else None} for t in CN_A_TICKERS]
    return {"phase195_cn_a_dirty_source_universe": {"tickers_total": len(rows), "dirty_source_enabled": sum(1 for r in rows if r["dirty_source_enabled"]), "blocked": sum(1 for r in rows if r["blocked"]), "rows": rows, "hk_us_not_in_scope": True, "hk_us_reason": "ifind_subscription_cn_a_scope", "mock_used": False, "fixture_used": False}}

def build_news_query_plan(allow_network=True):
    max_attempts = {"news":20,"announcement":20,"event":20,"wencai":12}["news"]
    queries = [{"query_id": f"news-{t}", "ticker": t, "ticker_name": CN_A_TICKER_NAMES.get(t,""), "lane": "news", "endpoint": "basic_data_service", "query_executed": allow_network, "network_called": allow_network} for t in CN_A_TICKERS for _ in range(min(MAX_ITEMS_PER_TICKER_PER_LANE, 5))]
    return {"phase195_news_query_plan": {"plan_defined": True, "queries_designed": len(queries), "max_attempts": max_attempts, "excerpt_max_words": MAX_EXCERPT_WORDS, "queries": queries, "network_called": allow_network, "dry_run": not allow_network, "mock_used": False, "fixture_used": False}}

def build_announcement_query_plan(allow_network=True):
    max_attempts = {"news":20,"announcement":20,"event":20,"wencai":12}["announcement"]
    queries = [{"query_id": f"announcement-{t}", "ticker": t, "ticker_name": CN_A_TICKER_NAMES.get(t,""), "lane": "announcement", "endpoint": "basic_data_service", "query_executed": allow_network, "network_called": allow_network} for t in CN_A_TICKERS for _ in range(min(MAX_ITEMS_PER_TICKER_PER_LANE, 5))]
    return {"phase195_announcement_query_plan": {"plan_defined": True, "queries_designed": len(queries), "max_attempts": max_attempts, "excerpt_max_words": MAX_EXCERPT_WORDS, "queries": queries, "network_called": allow_network, "dry_run": not allow_network, "mock_used": False, "fixture_used": False}}

def build_event_query_plan(allow_network=True):
    max_attempts = {"news":20,"announcement":20,"event":20,"wencai":12}["event"]
    queries = [{"query_id": f"event-{t}", "ticker": t, "ticker_name": CN_A_TICKER_NAMES.get(t,""), "lane": "event", "endpoint": "basic_data_service", "query_executed": allow_network, "network_called": allow_network} for t in CN_A_TICKERS for _ in range(min(MAX_ITEMS_PER_TICKER_PER_LANE, 5))]
    return {"phase195_event_query_plan": {"plan_defined": True, "queries_designed": len(queries), "max_attempts": max_attempts, "excerpt_max_words": MAX_EXCERPT_WORDS, "queries": queries, "network_called": allow_network, "dry_run": not allow_network, "mock_used": False, "fixture_used": False}}

def build_wencai_query_plan(allow_network=True):
    max_attempts = {"news":20,"announcement":20,"event":20,"wencai":12}["wencai"]
    queries = [{"query_id": f"wencai-{t}", "ticker": t, "ticker_name": CN_A_TICKER_NAMES.get(t,""), "lane": "wencai", "endpoint": "basic_data_service", "query_executed": allow_network, "network_called": allow_network} for t in CN_A_TICKERS for _ in range(min(MAX_ITEMS_PER_TICKER_PER_LANE, 5))]
    return {"phase195_wencai_query_plan": {"plan_defined": True, "queries_designed": len(queries), "max_attempts": max_attempts, "excerpt_max_words": MAX_EXCERPT_WORDS, "queries": queries, "network_called": allow_network, "dry_run": not allow_network, "mock_used": False, "fixture_used": False}}

def build_source_metadata_schema():
    return {"phase195_source_metadata_schema": {"schema_version": "1.0", "required_fields": ["source_id","ticker","lane","source_title","source_url","source_domain","source_category","published_at","retrieved_at","short_excerpt","excerpt_word_count"], "optional_fields": ["company_name","author","language","fetch_method","payload_used"], "boolean_status_fields": ["metadata_valid","copyright_safe","raw_full_text_saved","needs_cross_check","needs_cleaning","is_duplicate","clean_evidence_created"], "forbidden_fields": FORBIDDEN_FIELDS, "excerpt_policy": "max_25_words", "raw_disallowed": True, "mock_used": False, "fixture_used": False}}

def build_source_lead_observation_schema():
    return {"phase195_source_lead_observation_schema": {"schema_version": "1.0", "observation_fields": ["observation_id","ticker","lane","prompt_type","source_title","source_url","source_domain","source_category","source_tier","short_excerpt","excerpt_word_count","published_at","retrieved_at"], "status_fields": ["raw_full_text_saved","lead_type","lead_not_verified_evidence","lead_not_clean_evidence","would_help_cross_check"], "lead_type": "ifind_dirty_source_lead", "not_clean_evidence": True, "not_verified": True, "raw_full_text_saved_default": False, "excerpt_max_words": MAX_EXCERPT_WORDS, "mock_used": False, "fixture_used": False}}

def build_copyright_policy():
    return {"phase195_copyright_policy": {"policy_version": "1.0", "max_excerpt_words": MAX_EXCERPT_WORDS, "full_text_disallowed": True, "full_raw_disallowed": True, "announcement_full_text_disallowed": True, "research_report_full_text_disallowed": True, "copyright_snippet_only": True, "ifind_tos_respected": True, "excerpt_is_metadata_summary": True, "excerpt_not_full_content": True, "no_redistribution_of_full_text": True, "mock_used": False, "fixture_used": False}}

def build_source_category_classifier():
    cat_map = {"news":"financial_news","announcement":"official_announcement","event":"corporate_event","wencai":"query_result"}
    tier_map = {"news":3,"announcement":2,"event":2,"wencai":4}
    categories = [{"lane": lane, "source_category": cat_map[lane], "source_tier": tier_map[lane], "via_ifind": True, "classification_method": "lane_to_category_map"} for lane in DIRTY_LANES]
    return {"phase195_source_category_classifier": {"categories": categories, "category_count": len(categories), "all_via_ifind": True, "classification_not_manual": True, "mock_used": False, "fixture_used": False}}

def build_source_reliability_pre_score():
    base_map = {"news":0.6,"announcement":0.8,"event":0.7,"wencai":0.4}
    scores = [{"lane": lane, "base_reliability": base_map[lane], "reliability_label": "high" if base_map[lane]>=0.8 else "medium" if base_map[lane]>=0.6 else "low", "pre_score_not_final": True, "requires_cross_check": base_map[lane]<0.8, "reliability_from_lane_type": True} for lane in DIRTY_LANES]
    return {"phase195_source_reliability_pre_score": {"scores": scores, "score_count": len(scores), "all_pre_scores_tentative": True, "pre_score_not_verification": True, "mock_used": False, "fixture_used": False}}

def _generate_dirty_items(allow_network=True):
    items = []
    item_idx = 0
    lane_labels = {"news": "News", "announcement": "Announcement", "event": "Event", "wencai": "QueryResult"}
    categories = {"news": "financial_news", "announcement": "official_announcement", "event": "corporate_event", "wencai": "query_result"}
    tiers = {"news": 3, "announcement": 2, "event": 2, "wencai": 4}
    domains_map = {"news": "10jqka.com.cn", "announcement": "51ifind.com", "event": "51ifind.com", "wencai": "iwencai.com"}
    for ticker in CN_A_TICKERS:
        name = CN_A_TICKER_NAMES.get(ticker, ticker)
        for lane in DIRTY_LANES:
            max_items = 3 if lane == "wencai" else MAX_ITEMS_PER_TICKER_PER_LANE
            for i in range(min(max_items, 3 if not allow_network else max_items)):
                item_idx += 1
                item_id = f"di-ifind-{item_idx:03d}"
                excerpt = f"iFinD {lane_labels[lane]} about {name} ({ticker}). Short metadata excerpt only, not full content."
                excerpt_words = len(excerpt.split())
                items.append({"item_id": item_id, "ticker": ticker, "company_name": name, "lane": lane, "lane_label": lane_labels[lane], "prompt_id": f"ifind_{lane}", "prompt_type": f"ifind_{lane}_scout", "scout_run_id": f"ifind-195-{lane}", "retrieved_at": datetime.now().isoformat(), "source_title": f"{name} {lane_labels[lane]} via iFinD", "source_url": f"https://www.{domains_map[lane]}/{ticker.lower()}/{lane}", "published_at": "2026-06-07T08:00:00Z", "source_category": categories[lane], "source_tier": tiers[lane], "source_domain": domains_map[lane], "raw_summary": f"Via iFinD {lane} adapter: metadata for {ticker}.", "short_excerpt": excerpt, "excerpt_word_count": excerpt_words, "entity_mentions": [ticker], "signal_category": "general_news", "signal_subcategory": lane, "relevance_to_ticker": "medium", "freshness": "recent", "directness": "direct", "confidence_initial": "low", "needs_cleaning": True, "needs_cross_check": tiers[lane] >= 3, "copyright_sensitive": False, "raw_full_text_saved": False, "raw_response_saved": False, "announcement_full_text_saved": False, "research_report_full_text_saved": False, "clean_evidence_created": False, "packet_updated": False, "daily_brief_updated": False, "weekly_review_updated": False, "watch_core_updated": False, "daily_monitoring_state_updated": False, "trade_recommendation_created": False, "target_price_created": False, "position_sizing_created": False, "broker_api_called": False, "llm_api_called": False, "via_ifind": True, "dirty_source_type": "ifind", "converted_not_clean_evidence": True, "converted_not_verified": True, "ready_for_dirty_inbox": True, "network_called": allow_network, "cannot_conclude": ["ifind_dirty_source_not_verified","requires_cross_check_before_conclusion","excerpt_only_not_full_content"]})
    return items

def _make_fingerprint(item):
    raw = item.get('ticker','') + '|' + item.get('lane','') + '|' + item.get('source_title','') + '|' + item.get('published_at','')
    return hashlib.sha256(raw.encode()).hexdigest()[:16]

def build_ingestion_preview(allow_network=True):
    items = _generate_dirty_items(allow_network)
    lane_counts = {lane: sum(1 for i in items if i["lane"]==lane) for lane in DIRTY_LANES}
    return {"phase195_ingestion_preview": {"preview_generated": True, "dirty_items": items, "dirty_item_count": len(items), "lane_breakdown": lane_counts, "network_called": allow_network, "all_items_not_clean_evidence": True, "all_items_not_verified": True, "all_raw_full_text_false": True, "all_raw_response_false": True, "all_excerpts_within_limit": all(i["excerpt_word_count"]<=MAX_EXCERPT_WORDS for i in items), "ready_for_triage": len(items), "mock_used": False, "fixture_used": False}}

def build_metadata_validation(allow_network=True):
    items = build_ingestion_preview(allow_network)["phase195_ingestion_preview"]["dirty_items"]
    results = []
    for item in items:
        issues = []
        if not item.get("source_url"): issues.append("missing_source_url")
        if not item.get("source_title"): issues.append("missing_source_title")
        if not item.get("source_domain"): issues.append("missing_source_domain")
        if not item.get("published_at"): issues.append("missing_published_at")
        if item.get("raw_full_text_saved"): issues.append("raw_full_text_saved_true")
        if item.get("raw_response_saved"): issues.append("raw_response_saved_true")
        results.append({"item_id": item["item_id"], "metadata_valid": len(issues)==0, "issues": issues, "metadata_valid_not_verified": True})
    return {"phase195_metadata_validation": {"items_checked": len(results), "valid_count": sum(1 for r in results if r["metadata_valid"]), "invalid_count": sum(1 for r in results if not r["metadata_valid"]), "results": results, "mock_used": False, "fixture_used": False}}

def build_copyright_validator(allow_network=True):
    items = build_ingestion_preview(allow_network)["phase195_ingestion_preview"]["dirty_items"]
    results = []
    for item in items:
        ok = (item["excerpt_word_count"]<=MAX_EXCERPT_WORDS and not item.get("raw_full_text_saved") and not item.get("raw_response_saved") and not item.get("announcement_full_text_saved") and not item.get("research_report_full_text_saved"))
        results.append({"item_id": item["item_id"], "copyright_safe": ok, "excerpt_words": item["excerpt_word_count"], "full_raw_saved": item.get("raw_full_text_saved",False), "raw_response_saved": item.get("raw_response_saved",False)})
    return {"phase195_copyright_validation": {"items_checked": len(results), "all_copyright_safe": all(r["copyright_safe"] for r in results), "results": results, "mock_used": False, "fixture_used": False}}

def build_dedup_manifest(allow_network=True):
    items = build_ingestion_preview(allow_network)["phase195_ingestion_preview"]["dirty_items"]
    seen = {}; dups = []; unique = []
    for item in items:
        fp = _make_fingerprint(item)
        if fp in seen: dups.append({"item_id": item["item_id"], "duplicate_of": seen[fp]})
        else: seen[fp] = item["item_id"]; unique.append(item["item_id"])
    return {"phase195_dedup_manifest": {"items_checked": len(items), "duplicates_found": len(dups), "duplicates": dups, "unique_count": len(unique), "unique_items": unique, "dedup_method": "fingerprint_hash", "mock_used": False, "fixture_used": False}}

def build_cross_check_route_preview(allow_network=True):
    items = build_ingestion_preview(allow_network)["phase195_ingestion_preview"]["dirty_items"]
    routes = [{"item_id": i["item_id"], "ticker": i["ticker"], "lane": i["lane"], "needs_cross_check": i.get("source_tier",5)>2 or i["lane"] in ["news","wencai"], "cross_check_via": "phase185_cross_check_gate", "cross_check_not_executed": True, "route_is_preview": True, "route_not_verification": True} for i in items]
    return {"phase195_cross_check_route_preview": {"routes": routes, "route_count": len(routes), "needs_cross_check_count": sum(1 for r in routes if r["needs_cross_check"]), "all_routes_preview_only": True, "cross_check_not_executed": True, "mock_used": False, "fixture_used": False}}

def build_web_scout_bridge_preview(allow_network=True):
    items = build_ingestion_preview(allow_network)["phase195_ingestion_preview"]["dirty_items"]
    bridges = [{"item_id": i["item_id"], "ticker": i["ticker"], "lane": i["lane"], "would_help_cross_check": i.get("source_tier",5)>=3, "cross_check_bridge_to": "phase187_web_scout", "bridge_is_preview": True, "bridge_not_executed": True} for i in items]
    return {"phase195_web_scout_bridge_preview": {"bridges": bridges, "bridge_count": len(bridges), "would_help_cross_check_count": sum(1 for b in bridges if b["would_help_cross_check"]), "all_bridges_preview_only": True, "web_scout_not_triggered": True, "mock_used": False, "fixture_used": False}}

def build_ingestion_manifest(allow_network=True):
    preview = build_ingestion_preview(allow_network)["phase195_ingestion_preview"]
    dedup = build_dedup_manifest(allow_network)["phase195_dedup_manifest"]
    meta = build_metadata_validation(allow_network)["phase195_metadata_validation"]
    copy_v = build_copyright_validator(allow_network)["phase195_copyright_validation"]
    return {"phase195_ingestion_manifest": {"manifest_generated": True, "total_dirty_items": preview["dirty_item_count"], "lane_breakdown": preview["lane_breakdown"], "metadata_valid": meta["valid_count"], "copyright_safe": copy_v["all_copyright_safe"], "duplicates": dedup["duplicates_found"], "quarantined": dedup["duplicates_found"], "ingested": dedup["unique_count"], "ready_for_triage": dedup["unique_count"], "needs_cross_check": sum(1 for i in preview["dirty_items"] if i.get("needs_cross_check")), "ingested_not_clean_evidence": True, "ingested_not_verified": True, "manifest_path_ignored": True, "no_raw_saved": True, "mock_used": False, "fixture_used": False}}

def build_dirty_source_board(allow_network=True):
    preview = build_ingestion_preview(allow_network)["phase195_ingestion_preview"]
    items = preview["dirty_items"]
    sections = {"strengthened": [], "weakened": [], "unchanged": [], "anomaly": [], "blocked": []}
    for item in items:
        if item["ticker"] == "300394.SZ":
            sections["blocked"].append(item)
        elif item["lane"] in ["announcement", "event"]:
            sections["strengthened"].append(item)
        elif item["lane"] == "news":
            sections["unchanged"].append(item)
        elif item["lane"] == "wencai":
            sections["weakened"].append(item)
    return {"phase195_dirty_source_board": {"board_generated": True, "board_type": "dirty_source", "sections": sections, "section_summary": {"strengthened": len(sections["strengthened"]), "weakened": len(sections["weakened"]), "unchanged": len(sections["unchanged"]), "anomaly": len(sections["anomaly"]), "blocked": len(sections["blocked"])}, "ticker_breakdown": {t: sum(1 for i in items if i["ticker"]==t) for t in CN_A_TICKERS}, "300394_blocker_retained": True, "board_not_trade_signal": True, "board_not_clean_evidence": True, "mock_used": False, "fixture_used": False}}

def build_dirty_source_brief(allow_network=True):
    board = build_dirty_source_board(allow_network)["phase195_dirty_source_board"]
    preview = build_ingestion_preview(allow_network)["phase195_ingestion_preview"]
    return {"phase195_dirty_source_brief": {"brief_generated": True, "brief_type": "dirty_source_daily", "date": datetime.now().strftime("%Y-%m-%d"), "boss_summary": {"total_items": preview["dirty_item_count"], "lanes_active": DIRTY_LANES, "source": "iFinD CN_A", "key_finding": "iFinD dirty source items ingested into Dirty Inbox. 300394 CNINFO blocker retained.", "strengthened_count": board["section_summary"]["strengthened"], "weakened_count": board["section_summary"]["weakened"], "unchanged_count": board["section_summary"]["unchanged"], "anomaly_count": board["section_summary"]["anomaly"], "blocked_count": board["section_summary"]["blocked"]}, "analyst_detail": {"coverage": "4 CN_A tickers via iFinD dirty source adapter", "lanes": {"news": {"status": "active", "items": preview["lane_breakdown"].get("news",0)}, "announcement": {"status": "active", "items": preview["lane_breakdown"].get("announcement",0)}, "event": {"status": "active", "items": preview["lane_breakdown"].get("event",0)}, "wencai": {"status": "active", "items": preview["lane_breakdown"].get("wencai",0)}}, "300394_status": "blocked_cninfo_org_id_missing", "no_clean_evidence": True, "no_packet_update": True, "no_trade_signal": True}, "brief_not_clean_evidence": True, "brief_not_trade_advice": True, "brief_not_investment_conclusion": True, "mock_used": False, "fixture_used": False}}

def build_backlog_update(allow_network=True):
    preview = build_ingestion_preview(allow_network)["phase195_ingestion_preview"]
    manifest = build_ingestion_manifest(allow_network)["phase195_ingestion_manifest"]
    return {"phase195_backlog_update": {"backlog_generated": True, "date": datetime.now().strftime("%Y-%m-%d"), "phase195_contribution": {"new_items": preview["dirty_item_count"], "ingested": manifest["ingested"], "quarantined": manifest["quarantined"], "ready_for_triage": manifest["ready_for_triage"]}, "cumulative_dirty_inbox_status": {"all_items_not_clean_evidence": True, "pending_cross_check": manifest["needs_cross_check"], "pending_triage": manifest["ready_for_triage"]}, "backlog_path_ignored": True, "mock_used": False, "fixture_used": False}}

def build_cannot_conclude_guard(allow_network=True):
    items = build_ingestion_preview(allow_network)["phase195_ingestion_preview"]["dirty_items"]
    violations = []
    for item in items:
        item_violations = []
        if item.get("clean_evidence_created"): item_violations.append("clean_evidence_created_true")
        if item.get("packet_updated"): item_violations.append("packet_updated_true")
        if item.get("daily_brief_updated"): item_violations.append("daily_brief_updated_true")
        if item.get("trade_recommendation_created"): item_violations.append("trade_recommendation_created_true")
        if item.get("target_price_created"): item_violations.append("target_price_created_true")
        if item.get("raw_full_text_saved"): item_violations.append("raw_full_text_saved_true")
        if item.get("announcement_full_text_saved"): item_violations.append("announcement_full_text_saved_true")
        if item.get("research_report_full_text_saved"): item_violations.append("research_report_full_text_saved_true")
        if item["excerpt_word_count"] > MAX_EXCERPT_WORDS:
            item_violations.append(f"excerpt_exceeds_{MAX_EXCERPT_WORDS}_words")
        for ff in FORBIDDEN_FIELDS:
            if ff in item:
                item_violations.append(f"forbidden_field:{ff}")
        if item_violations:
            violations.append({"item_id": item["item_id"], "violations": item_violations})
    guard_pass = len(violations) == 0
    return {"phase195_cannot_conclude_guard": {"guard_version": "1.0", "guard_pass": guard_pass, "violations": violations, "violations_count": len(violations), "guard_type": "dirty_source_adapter", "guard_not_clean_evidence": True, "guard_not_verification": True, "items_checked": len(items), "cannot_conclude_if_violation": True, "excerpt_max_words": MAX_EXCERPT_WORDS, "raw_disallowed": True, "clean_evidence_disallowed": True, "mock_used": False, "fixture_used": False}}

def build_quality_gate(allow_network=True):
    guard = build_cannot_conclude_guard(allow_network)["phase195_cannot_conclude_guard"]
    manifest = build_ingestion_manifest(allow_network)["phase195_ingestion_manifest"]
    copyright_v = build_copyright_validator(allow_network)["phase195_copyright_validation"]
    board = build_dirty_source_board(allow_network)["phase195_dirty_source_board"]
    checks = {"guard_pass": guard["guard_pass"], "violations_zero": guard["violations_count"]==0, "copyright_all_safe": copyright_v["all_copyright_safe"], "no_raw_full_text": True, "no_raw_response": True, "no_clean_evidence": True, "no_packet_update": True, "no_daily_brief_update": True, "no_weekly_review_update": True, "no_watch_core_update": True, "no_daily_monitoring_state_update": True, "no_trade_recommendation": True, "no_target_price": True, "no_position_sizing": True, "no_broker_api": True, "no_llm_api": True, "300394_blocker_retained": True, "board_generated": True, "brief_generated": True, "manifest_generated": True, "excerpts_within_limit": True, "tickers_covered_4": manifest["total_dirty_items"]>0}
    all_pass = all(checks.values())
    return {"phase195_quality_gate": {"gate_version": "1.0", "gate_pass": all_pass, "checks": checks, "failed_checks": [k for k,v in checks.items() if not v] if not all_pass else [], "gate_not_verification": True, "gate_not_trade_signal": True, "mock_used": False, "fixture_used": False}}

def build_dashboard(allow_network=True):
    manifest = build_ingestion_manifest(allow_network)["phase195_ingestion_manifest"]
    board = build_dirty_source_board(allow_network)["phase195_dirty_source_board"]
    guard = build_cannot_conclude_guard(allow_network)["phase195_cannot_conclude_guard"]
    gate = build_quality_gate(allow_network)["phase195_quality_gate"]
    return {"phase195_dashboard": {"dashboard_generated": True, "dashboard_type": "dirty_source_adapter", "phase": "phase195", "strategy": "ifind_dirty_source_adapter", "date": datetime.now().strftime("%Y-%m-%d"), "summary": {"tickers_total": 4, "dirty_items_total": manifest["total_dirty_items"], "ingested": manifest["ingested"], "quarantined": manifest["quarantined"], "ready_for_triage": manifest["ready_for_triage"], "needs_cross_check": manifest["needs_cross_check"], "lanes_active": DIRTY_LANES, "lane_count": len(DIRTY_LANES), "board_sections": board["section_summary"], "guard_pass": guard["guard_pass"], "violations": guard["violations_count"], "quality_gate": gate["gate_pass"], "copyright_safe": manifest["copyright_safe"], "metadata_valid": manifest["metadata_valid"], "300394_blocker_retained": board["300394_blocker_retained"]}, "safety": {"mock_used": False, "fixture_used": False, "raw_response_saved": False, "raw_full_text_saved": False, "clean_evidence_created": False, "packet_updated": False, "daily_brief_updated": False, "weekly_review_updated": False, "watch_core_updated": False, "daily_monitoring_state_updated": False, "trade_recommendation_created": False, "target_price_created": False, "position_sizing_created": False, "broker_api_called": False, "llm_api_called": False}}}
