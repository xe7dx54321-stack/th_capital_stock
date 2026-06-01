import json,os
def run_production_guard(operator_summary):
    md=operator_summary.get("phase100_operator_summary",{}).get("markdown","")
    violations=[]
    for term in ["buy","sell","target price","position","recommend","allocation"]:
        if term.lower() in md.lower():
            violations.append({"violation":f"investment_term_{term}","detail":f"operator summary contains '{term}'"})
    return {"phase100_guard":{"overall":"pass" if len(violations)==0 else "fail","violations":len(violations),"violation_details":violations,"mock_used":False,"fixture_used":False}}
