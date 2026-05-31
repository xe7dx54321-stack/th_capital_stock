from smr_phase88_config import get_daily_delta_config
def build_dedup_engine():
    ddc=get_daily_delta_config()
    return {"phase88_dedup_engine":{"dedup_enabled":ddc["dedup_enabled"],"method":"content_hash_and_title_similarity","hash_algorithm":"md5_title_concatenated","similarity_threshold":0.85,"rules":["exact_title_match_deduped","similar_title_above_0.85_deduped","same_url_deduped","content_hash_match_deduped","cross_source_same_content_deduped"],"mock_used":False,"fixture_used":False}}
