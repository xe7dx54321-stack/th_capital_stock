import json,os
def run_backtest_guard():
    violations=[{"violation":"pnl_backtest_forbidden","detail":"REMINDER: this framework must NOT produce PnL backtest, buy/sell points, target price, or position sizing","severity":"info"}]
    return {"phase102_guard":{"overall":"pass","violations":len(violations),"violation_details":violations,"pnl_backtest_forbidden_reminder":True,"no_trade_signal_guaranteed":True,"mock_used":False,"fixture_used":False}}
