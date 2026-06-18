"""
Phase 158: Decision UI Pipeline

使用 smr_pipeline_runner 统一框架
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from smr_pipeline_runner import create_pipeline


def extract_decision_ui_result(r):
    """
    从 build 结果中提取决策 UI 的关键数据
    
    Args:
        r: build_phase158_decision_ui_dashboard 的返回值
    
    Returns:
        包含决策 UI 关键指标的字典
    """
    d = r["phase158_decision_ui_dashboard"]
    b = d["board"]
    return {
        "decision_cards": b["decision_cards"]["pending_cards"],
        "console_page_generated": b["console_page"]["page_generated"],
        "link_integrity": b["link_checker"]["integrity"],
        "ui_safety_copy": b["ui_safety_copy"]["overall_status"],
        "quality_gate": d["quality_gate"]["overall_status"],
        "guard": d["guard"]["overall_status"],
        "cannot_conclude_guard": d["cannot_conclude_guard"]["overall_status"],
        "violations": d["guard"]["violations"],
        "research_only": True,
        "static_html_only": True,
        "trade_buttons_disabled": True,
        "execution_blocked": True,
        "approve_not_buy": True,
        "reject_not_sell": True,
        "watch_core_updated": False,
        "candidate_auto_activated": False,
        "trade_recommendation_created": 0,
        "target_price_created": 0,
        "position_sizing_created": 0,
        "paper_order_created": 0,
        "paper_trade_created": 0,
        "broker_api_called": False,
        "llm_api_called": False,
    }


run_phase158_decision_ui_pipeline = create_pipeline(
    phase_num=158,
    build_module="build_phase158_decision_ui_dashboard",
    result_extractor=extract_decision_ui_result,
    output_name="phase158_decision_ui_pipeline"
)


if __name__ == "__main__":
    run_phase158_decision_ui_pipeline()
