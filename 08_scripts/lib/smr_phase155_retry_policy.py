def build_retry_policy():
    return {"phase155_retry_policy":{"max_retries":3,"retry_delay_hours":[1,4,24],"skip_after_exhausted":True,"skip_reason":"max_retries_exhausted","retry_not_escalated_to_trade":True,"mock_used":False,"fixture_used":False}}
