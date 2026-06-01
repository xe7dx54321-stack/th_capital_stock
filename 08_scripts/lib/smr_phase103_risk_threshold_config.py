import json,os
def build_risk_threshold_config():
    thresholds=[{"threshold":"max_position_violation","check":"position_pct <= 20","remediation":"reduce_position_or_block_order","severity":"critical"},{"threshold":"max_drawdown_violation","check":"drawdown_pct <= 15","remediation":"pause_trading_review_exposure","severity":"critical"},{"threshold":"daily_loss_violation","check":"daily_loss_pct <= 5","remediation":"stop_trading_for_day","severity":"critical"},{"threshold":"leverage_violation","check":"leverage <= 1.0","remediation":"block_leveraged_orders","severity":"critical"}]
    return {"phase103_risk_thresholds":{"total_thresholds":len(thresholds),"thresholds":thresholds,"mock_used":False,"fixture_used":False}}
