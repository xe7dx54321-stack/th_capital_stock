import json, sys, os
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))
from smr_phase151_config import load_phase151_config
from smr_phase151_discovery_sources import build_discovery_sources
from smr_phase151_discovery_queue import build_discovery_queue
from smr_phase151_quality_gate import run_phase151_quality_gate
from smr_phase151_guard import run_phase151_guard
from smr_phase151_backlog import build_phase151_backlog

# 新增：三个真实数据驱动的发现模块
from smr_phase151_news_scanner import build_news_scanner_result
from smr_phase151_financial_change import build_financial_change_result
from smr_phase151_external_list import build_external_list_result


def build():
    """构建 Phase 151 发现管线仪表板。

    【小白讲解】
    这个函数把三个发现模块的结果汇总起来：
    1. 新闻扫描器（BL-151-01）：从新闻中发现热门股票
    2. 财务变化检测（BL-151-02）：从财务因子中发现动量变化
    3. 外部列表导入（BL-151-03）：从分析师研报和ETF新闻中发现候选

    这三个模块都使用真实数据，不再依赖 mock 数据。
    """
    return {"phase151_discovery_dashboard": {
        "config": load_phase151_config(),
        "discovery_sources": build_discovery_sources()["phase151_discovery_sources"],
        # BL-151-01: 新闻扫描器（真实数据）
        "news_scanner": build_news_scanner_result()["phase151_news_scanner"],
        # BL-151-02: 财务变化检测（真实数据）
        "financial_change_detector": build_financial_change_result()["phase151_financial_change_detector"],
        # BL-151-03: 外部列表导入（真实数据）
        "external_list_importer": build_external_list_result()["phase151_external_list_importer"],
        "discovery_queue": build_discovery_queue()["phase151_discovery_queue"],
        "quality_gate": run_phase151_quality_gate()["phase151_quality_gate"],
        "guard": run_phase151_guard()["phase151_cannot_conclude_guard"],
        "backlog": build_phase151_backlog()["phase151_backlog"],
        "research_only": True, "mock_used": False, "fixture_used": False,
        "trade_recommendation_created": 0, "paper_order_created": 0,
    }}


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, ensure_ascii=False, default=str))
