from smr_phase88_config import get_daily_delta_config
def build_freshness_detector():
    ddc=get_daily_delta_config()
    return {"phase88_freshness_detector":{"freshness_enabled":ddc["freshness_enabled"],"freshness_categories":{"fresh_today":"published_within_24h","recent":"published_within_7d","aging":"published_7d_to_30d","stale":">30d"},"default_max_age_days":30,"check_timestamps":True,"require_publish_date":True,"mock_used":False,"fixture_used":False}}
