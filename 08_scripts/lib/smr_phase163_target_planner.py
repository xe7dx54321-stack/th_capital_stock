def plan_live_execute_targets():
    targets = [
        {"ticker":"MRVL","name":"Marvell Technology","market":"US","sector":"Semiconductors","priority":"high"},
        {"ticker":"AMAT","name":"Applied Materials","market":"US","sector":"Semi Equipment","priority":"high"},
        {"ticker":"LRCX","name":"Lam Research","market":"US","sector":"Semi Equipment","priority":"high"},
        {"ticker":"KLAC","name":"KLA Corporation","market":"US","sector":"Semi Equipment","priority":"high"},
        {"ticker":"INTC","name":"Intel","market":"US","sector":"Semiconductors","priority":"medium"},
        {"ticker":"SNPS","name":"Synopsys","market":"US","sector":"EDA Software","priority":"medium"},
        {"ticker":"CDNS","name":"Cadence","market":"US","sector":"EDA Software","priority":"medium"},
        {"ticker":"CRM","name":"Salesforce","market":"US","sector":"Enterprise Software","priority":"medium"},
        {"ticker":"TSM","name":"TSMC","market":"US","sector":"Semiconductors","priority":"high"},
        {"ticker":"ASML","name":"ASML","market":"US","sector":"Semi Equipment","priority":"high"},
        {"ticker":"AMD","name":"AMD","market":"US","sector":"Semiconductors","priority":"high"},
        {"ticker":"SNOW","name":"Snowflake","market":"US","sector":"Cloud Data","priority":"low"},
        {"ticker":"MU","name":"Micron","market":"US","sector":"Memory","priority":"medium"}
    ]
    return {"phase163_target_planner":{"live_execute_targets":len(targets),"minimum_targets_met":len(targets)>=8,"preferred_targets_met":len(targets)>=13,"targets":targets,"mock_used":False,"fixture_used":False}}
