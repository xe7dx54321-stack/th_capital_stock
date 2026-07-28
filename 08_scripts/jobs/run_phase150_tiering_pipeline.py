"""
Phase 150: Watchlist Tiering Pipeline

使用 smr_pipeline_runner 统一框架
原文件已备份为 .bak
"""
import sys
from pathlib import Path

# 设置路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from smr_pipeline_runner import create_pipeline


def extract_tiering_result(r):
    """
    从 build 结果中提取关键数据
    
    Args:
        r: build_phase150_tiering_dashboard 的返回值
    
    Returns:
        包含分层关键指标的字典
    """
    d = r["phase150_tiering_dashboard"]
    tc = d["tier_assignments"]["tier_counts"]
    return {
        "tiers": {"core": tc["core"], "watch": tc["watch"], "candidate": tc["candidate"]},
        "total_tracked": d["tier_assignments"]["total"],
        "max_capacity": d["capacity_model"]["model"]["max_total"],
        "utilization_pct": d["capacity_model"]["model"]["utilization_pct"],
        "quality_gate": d["quality_gate"]["overall_status"],
        "guard": d["guard"]["overall_status"],
        "violations": d["guard"]["violations"],
        "research_only": True,
        "auto_add_to_watchlist_allowed": False,
        "auto_promote_to_core_allowed": False,
        "trade_recommendation_created": 0,
        "paper_order_created": 0,
    }


# 创建 pipeline
run_phase150_tiering_pipeline = create_pipeline(
    phase_num=150,
    build_module="build_phase150_tiering_dashboard",
    result_extractor=extract_tiering_result,
    output_name="phase150_tiering_pipeline"
)

# Preserve the original short entry point while keeping the descriptive name.
def run(mode="dry-run"):
    return run_phase150_tiering_pipeline([f"--{mode}"])


if __name__ == "__main__":
    run_phase150_tiering_pipeline()
