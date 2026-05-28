#!/usr/bin/env python3
from __future__ import annotations

def build_frame(ticker="300308.SZ"):
    return {"ticker": ticker, "bull_base_bear_frame": {
        "bull_case": ["800G/1.6T放量顺利","高端产品占比提升","毛利率保持稳定","市场预期仍未充分反映利润弹性"],
        "base_case": ["AI光模块需求继续增长","公司受益于产品结构升级","但客户份额和价格趋势仍需验证"],
        "bear_case": ["市场已经充分反映高景气","价格竞争压低毛利率","大客户资本开支节奏放缓","公司份额低于市场预期"],
        "key_swing_factors": ["毛利率","1.6T出货节奏","客户份额","一致预期变化"]
    }}
