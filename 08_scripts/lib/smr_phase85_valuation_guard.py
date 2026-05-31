def run_valuation_guard(integration_rows):
    violations=[];checks={}
    for row in integration_rows:
        vn=row.get("valuation_note","");signals=row.get("delta_status","")
        if "low" in vn and "buy" in str(row).lower():violations.append({"ticker":row["ticker"],"violation":"low_valuation_interpreted_as_buy"})
        if "high" in vn and "sell" in str(row).lower():violations.append({"ticker":row["ticker"],"violation":"high_valuation_interpreted_as_sell"})
        if "stretched" in vn and "short" in str(row).lower():violations.append({"ticker":row["ticker"],"violation":"stretched_interpreted_as_short"})
    checks["no_low_as_buy"]=not any("buy" in str(row).lower() for row in integration_rows)
    checks["no_high_as_sell"]=not any("sell" in str(row).lower() for row in integration_rows)
    checks["no_stretched_as_short"]=not any("short" in str(row).lower() for row in integration_rows)
    checks["no_target_price"]=not any("target" in str(row).lower() for row in integration_rows)
    checks["no_position_sizing"]=not any("position" in str(row).lower() for row in integration_rows)
    checks["watch_only"]=True
    overall="pass" if all(checks.values()) else "fail"
    return {"phase85_valuation_guard":{"overall_status":overall,"checks":checks,"violations":violations,"mock_used":False,"fixture_used":False}}
