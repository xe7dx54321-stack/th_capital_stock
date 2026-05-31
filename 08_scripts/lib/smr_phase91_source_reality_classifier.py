import json
from datetime import datetime

CLASSIFICATION_RULES = {
    "third_party_api": "real_on_demand_source",
    "regulatory_disclosure": "real_on_demand_source",
    "local_database": "partial_real_source",
    "derived_adapter": "partial_real_source",
    "keyword_catalog_with_api": "partial_real_source",
    "connector_registry": "real_on_demand_source",
    "curated_catalog": "curated_catalog_source",
    "history_pool": "history_pool_source",
    "fallback_text": "fallback_only_source",
    "manual_required": "manual_required_source",
    "derived_output": "registry_only_source",
    "delivery_outbox": "registry_only_source",
}

def classify_sources(inventory):
    """Classify each source according to reality audit taxonomy."""
    sources = inventory.get("phase91_existing_source_inventory", {}).get("sources", [])
    classification_counts = {c:0 for c in [
        "real_daily_source","real_on_demand_source","partial_real_source",
        "fallback_only_source","history_pool_source","registry_only_source",
        "curated_catalog_source","blocked_source","manual_required_source",
        "unknown_needs_probe"
    ]}
    
    classified = []
    for src in sources:
        sid = src.get("source_id","")
        stype = src.get("source_type","")
        base_class = CLASSIFICATION_RULES.get(stype, "unknown_needs_probe")
        
        # Override for special cases
        if src.get("known_issue") == "blocked" or src.get("blocker"):
            base_class = "blocked_source"
        if src.get("note") == "history_pool_not_live_source":
            base_class = "history_pool_source"
        if src.get("note") in ("catalog_not_data_source","curated_catalog_not_hard_data","registry_not_data_source"):
            base_class = "curated_catalog_source"
        if src.get("note") == "fallback_only_not_primary":
            base_class = "fallback_only_source"
        if src.get("note") == "manual_required_no_automation":
            base_class = "manual_required_source"
        if src.get("note") in ("output_not_source","delivery_outbox_not_source"):
            base_class = "registry_only_source"
        
        src["classified_as"] = base_class
        src["classification_rationale"] = f"source_type={stype}"
        classification_counts[base_class] = classification_counts.get(base_class, 0) + 1
        classified.append(src)
    
    return {
        "phase91_source_reality_classifier": {
            "generated_at": datetime.now().isoformat(),
            "sources_classified": len(classified),
            "classification_summary": classification_counts,
            "taxonomy_used": list(classification_counts.keys()),
            "classified_sources": classified
        }
    }
