"""
Phase 154: Multi Agent Loop Pipeline

使用 smr_pipeline_runner 统一框架
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from smr_pipeline_runner import create_pipeline


def extract_multi_agent_result(r):
    """
    从 build 结果中提取多 Agent 循环的关键数据
    
    Args:
        r: build_phase154_loop_research_dashboard 的返回值
    
    Returns:
        包含多 Agent 循环关键指标的字典
    """
    d = r["phase154_loop_research_dashboard"]
    b = d["board"]
    j = b["agents"]["judge"]
    return {
        "loop_targets_total": b["loop_targets_total"],
        "judge_passed": j["passed"],
        "judge_blocked": j["blocked"],
        "quality_gate": d["quality_gate"]["overall_status"],
        "guard": d["guard"]["overall_status"],
        "cannot_conclude_guard": d["cannot_conclude_guard"]["overall_status"],
        "violations": d["guard"]["violations"],
        "research_only": True,
        "agent_simulation_only": True,
        "live_llm_call_made": False,
        "watch_core_updated": False,
        "candidate_auto_activated": False,
        "confirmed_thesis_created": b["thesis_proposals"]["confirmed_thesis_created"],
        "owner_actions_contain_trade": False,
        "trade_recommendation_created": 0,
        "target_price_created": 0,
        "position_sizing_created": 0,
        "paper_order_created": 0,
        "paper_trade_created": 0,
        "broker_api_called": False,
        "llm_api_called": False,
    }


run_phase154_multi_agent_loop_pipeline = create_pipeline(
    phase_num=154,
    build_module="build_phase154_loop_research_dashboard",
    result_extractor=extract_multi_agent_result,
    output_name="phase154_multi_agent_loop_pipeline"
)


if __name__ == "__main__":
    run_phase154_multi_agent_loop_pipeline()
