"""
Phase 151: Discovery Pipeline

使用 smr_pipeline_runner 统一框架
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from smr_pipeline_runner import create_pipeline


def extract_discovery_result(r):
    """
    从 build 结果中提取发现 pipeline 的关键数据
    
    Args:
        r: build_phase151_discovery_dashboard 的返回值
    
    Returns:
        包含发现关键指标的字典
    """
    d = r["phase151_discovery_dashboard"]
    return {
        "discovery_sources": d["discovery_sources"]["sources"],
        "candidates_discovered": d["discovery_queue"]["candidates_discovered"],
        "by_priority": d["discovery_queue"]["summary"]["by_priority"],
        "quality_gate": d["quality_gate"]["overall_status"],
        "guard": d["guard"]["overall_status"],
        "violations": d["guard"]["violations"],
        "research_only": True,
        "auto_add_to_watchlist_allowed": False,
        "trade_recommendation_created": 0,
        "paper_order_created": 0,
    }


run_phase151_discovery_pipeline = create_pipeline(
    phase_num=151,
    build_module="build_phase151_discovery_dashboard",
    result_extractor=extract_discovery_result,
    output_name="phase151_discovery_pipeline"
)

# Preserve the original short entry point while keeping the descriptive name.
def run(mode="dry-run"):
    return run_phase151_discovery_pipeline([f"--{mode}"])


if __name__ == "__main__":
    run_phase151_discovery_pipeline()
