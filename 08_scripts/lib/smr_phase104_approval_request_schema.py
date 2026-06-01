import json,os
def build_approval_request_schema():
    schema={
        "request_id":"required, uuid",
        "ticker":"required, string",
        "action_type":"required, enum: [watchlist_add, watchlist_remove, monitoring_override, manual_override]",
        "action_detail":"required, string",
        "requested_by":"required, operator_id",
        "requested_at":"required, iso8601 timestamp",
        "justification":"required, string, min 50 chars",
        "risk_impact":"optional, string",
        "status":"pending",
        "no_order_created":True,
        "no_trade_created":True,
        "no_position_sizing":True
    }
    return {"phase104_approval_request_schema":{"schema":schema,"no_order_creation":True,"no_trade_creation":True,"mock_used":False,"fixture_used":False}}
