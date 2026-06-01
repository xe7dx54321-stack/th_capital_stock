import json,os
def build_paper_portfolio_boundary():
    pb={
        "schema_defined":True,
        "fields":["portfolio_id","ticker","position","avg_cost","market_value","unrealized_pnl"],
        "execution_blocked":True,
        "position_creation_forbidden":True,
        "boundary_rule":"paper portfolio schema defined but position creation is FORBIDDEN",
        "readiness_status":"boundary_defined"
    }
    return {"phase107_paper_portfolio_boundary":pb}
