from smr_phase88_config import get_daily_delta_config
def build_novelty_detector():
    ddc=get_daily_delta_config()
    return {"phase88_novelty_detector":{"novelty_enabled":ddc["novelty_enabled"],"novelty_categories":{"new_signal":"previously_unseen_topic_or_keyword","significant_update":"existing_topic_with_new_material_information","minor_update":"existing_topic_with_incremental_detail","duplicate":"no_new_information"},"scoring_factors":["keyword_overlap_with_known","source_reliability_weight","temporal_recency","industry_direction_match","signal_type_match","claim_map_alignment"],"mock_used":False,"fixture_used":False}}
