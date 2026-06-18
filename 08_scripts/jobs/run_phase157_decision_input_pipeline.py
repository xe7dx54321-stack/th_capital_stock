"""
Phase 157: Decision Input Pipeline

使用 smr_pipeline_runner 统一框架
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from smr_pipeline_runner import create_pipeline


def extract_decision_input_result(r):
    """
    从 build 结果中提取决策输入的关键数据
    
    Args:
        r: build_phase157_decision_dashboard 的返回值
    
    Returns:
        包含决策输入关键指标的字典
    """
    d = r["phase157_decision_dashboard"]
    b = d["board"]
    sm = b["decision_summary"]["summary"]
    return {
        "owner_input_present": b["decision_summary"]["owner_input_present"],
        "pending": sm["pending"],
        "approved": sm["approved"],
        "deferred": sm["deferred"],
        "rejected": sm["rejected"],
        "simulation_only": True,
        "execution_blocked": b["execution_blocked"],
        "quality_gate": d["quality_gate"]["overall_status"],
        "guard": d["guard"]["overall_status"],
        "cannot_conclude_guard": d["cannot_conclude_guard"]["overall_status"],
        "violations": d["guard"]["violations"],
        "research_only": True,
        "approve_not_buy": True,
        "reject_not_sell": True,
        "simulation_not_execution": True,
        "tier_not_executed": True,
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


run_phase157_decision_input_pipeline = create_pipeline(
    phase_num=157,
    build_module="build_phase157_decision_dashboard",
    result_extractor=extract_decision_input_result,
    output_name="phase157_decision_input_pipeline"
)


if __name__ == "__main__":
    run_phase157_decision_input_pipeline()
