import json,os
def build_paper_pnl_boundary():
    pb={
        "schema_defined":True,
        "fields":["pnl_id","ticker","realized_pnl","unrealized_pnl","total_pnl","period"],
        "execution_blocked":True,
        "pnl_calculation_forbidden":True,
        "boundary_rule":"paper PnL schema defined but calculation is FORBIDDEN",
        "readiness_status":"boundary_defined"
    }
    return {"phase107_paper_pnl_boundary":pb}
