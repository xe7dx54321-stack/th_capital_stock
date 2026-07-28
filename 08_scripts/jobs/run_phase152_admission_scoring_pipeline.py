"""
Phase 152: Admission Scoring Pipeline

使用 smr_pipeline_runner 统一框架
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from smr_pipeline_runner import create_pipeline


def extract_admission_result(r):
    """
    从 build 结果中提取入池评分的关键数据
    
    Args:
        r: build_phase152_admission_scoring_dashboard 的返回值
    
    Returns:
        包含入池评分关键指标的字典
    """
    d = r["phase152_admission_scoring_dashboard"]
    board = d["board"]
    bsum = board["buckets"]
    return {
        "scored_candidates": board["scored_candidates"],
        "admit_to_onboarding_review": bsum.get("admit_to_onboarding_review", 0),
        "watch_for_more_evidence": bsum.get("watch_for_more_evidence", 0),
        "manual_identity_or_source_review": bsum.get("manual_identity_or_source_review", 0),
        "defer": bsum.get("defer", 0),
        "reject_for_now": bsum.get("reject_for_now", 0),
        "quality_gate": d["quality_gate"]["overall_status"],
        "guard": d["guard"]["overall_status"],
        "cannot_conclude_guard": d["cannot_conclude_guard"]["overall_status"],
        "violations": d["guard"]["violations"],
        "agent_routing": {
            "evidence_agent": d["agent_routing"]["evidence_agent"]["candidates_routed"],
            "risk_agent": d["agent_routing"]["risk_agent"]["candidates_routed"],
            "judge_agent": d["agent_routing"]["judge_agent"]["candidates_routed"],
        },
        "research_only": True,
        "auto_add_to_watchlist_allowed": False,
        "auto_promote_to_core_allowed": False,
        "admission_score_not_investment_rating": True,
        "admission_bucket_not_buy_sell": True,
        "trade_recommendation_created": 0,
        "paper_order_created": 0,
        "paper_trade_created": 0,
        "target_price_created": 0,
        "position_sizing_created": 0,
        "broker_api_called": False,
        "llm_api_called": False,
    }


run_phase152_admission_scoring_pipeline = create_pipeline(
    phase_num=152,
    build_module="build_phase152_admission_scoring_dashboard",
    result_extractor=extract_admission_result,
    output_name="phase152_admission_scoring_pipeline"
)


def run(mode_or_args="dry-run"):
    """
    给测试用的便捷入口：兼容 3 种调用方式。

    小白讲解：
    因为底层 smr_pipeline_runner.run_pipeline(args) 的 args 必须是 'list of str'（比如 ["--dry-run"]），
    但 test_phase152_admission_scoring.py 里写的是 run("dry-run") 这种传字符串的形式。
    所以在这一层做"智能识别"，不管你传哪种都能跑。

    Args:
        mode_or_args: 支持三种格式
            1) str == "dry-run"  → 内部转成 ["--dry-run"]
            2) str == "execute"  → 内部转成 ["--execute"]
            3) list[str]         → 直接透传（完全按 argparse 来）

    Returns:
        dict: 同底层 pipeline 返回结构（phase152_admission_scoring_pipeline 字段）
    """
    if isinstance(mode_or_args, str):
        # 写法 1：字符串别名
        if mode_or_args == "dry-run":
            args = ["--dry-run"]
        elif mode_or_args == "execute":
            args = ["--execute"]
        else:
            # 兜底：把字符串按空格切一下（防御性）
            args = mode_or_args.split()
    elif isinstance(mode_or_args, (list, tuple)):
        args = list(mode_or_args)
    elif mode_or_args is None:
        args = ["--dry-run"]
    else:
        raise TypeError(f"run() 参数类型不对：{type(mode_or_args).__name__}，预期 str / list[str]")
    return run_phase152_admission_scoring_pipeline(args)


if __name__ == "__main__":
    run_phase152_admission_scoring_pipeline()
