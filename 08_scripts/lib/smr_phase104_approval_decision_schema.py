import json,os
def build_approval_decision_schema():
    schema={
        "decision_id":"required, uuid",
        "request_id":"required, fk to approval request",
        "decision":"required, enum: [approved, rejected, needs_more_info]",
        "decided_by":"required, approver_id",
        "decided_at":"required, iso8601 timestamp",
        "reason":"required if rejected or needs_more_info",
        "expires_at":"required, 24h from decided_at",
        "revocable_until":"required, 72h from decided_at",
        "order_created":False,
        "trade_created":False,
        "position_sizing_created":False
    }
    return {"phase104_approval_decision_schema":{"schema":schema,"no_order_creation":True,"no_trade_creation":True,"mock_used":False,"fixture_used":False}}
