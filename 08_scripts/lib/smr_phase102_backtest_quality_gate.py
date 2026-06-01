import json,os
def run_backtest_quality_gate(db_integrity, coverage, signal_validator):
    di=db_integrity.get("phase102_db_integrity",{})
    cv=coverage.get("phase102_historical_coverage",{})
    sv=signal_validator.get("phase102_signal_validator",{})
    checks=[{"check":"db_integrity","passed":di.get("integrity_issues",0)==0,"detail":f"issues={di.get('integrity_issues',0)}"},{"check":"coverage_threshold","passed":cv.get("coverage_pct",0)>=50,"detail":f"coverage={cv.get('coverage_pct',0)}%"},{"check":"signal_validation","passed":sv.get("tickers_pass",0)>=4,"detail":f"pass={sv.get('tickers_pass',0)}"},{"check":"no_pnl_backtest","passed":not sv.get("pnl_backtest_attempted",True),"detail":"pnl_backtest_not_attempted"}]
    return {"phase102_quality_gate":{"overall":"pass" if all(c["passed"] for c in checks) else "fail","checks":checks,"mock_used":False,"fixture_used":False}}
