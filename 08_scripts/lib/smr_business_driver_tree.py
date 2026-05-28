#!/usr/bin/env python3
from __future__ import annotations

def build_driver_tree(ticker="300308.SZ"):
    return {"ticker": ticker, "business_driver_tree": {
        "root_driver": "AI算力资本开支",
        "industry_drivers": ["高速光模块需求","800G放量","1.6T迭代"],
        "company_drivers": ["高端产品占比","出货节奏","客户份额","ASP/价格趋势","毛利率"],
        "financial_outputs": ["收入增长","毛利率稳定性","利润弹性","预期上修空间"],
        "most_important_open_questions": ["公司在核心客户中的份额是多少","高端产品放量是否伴随价格压力","毛利率能否稳定"]
    }}
