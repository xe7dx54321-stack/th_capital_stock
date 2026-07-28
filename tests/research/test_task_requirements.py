"""
DataRequirementPlanner 测试

功能说明：
    测试任务数据需求计划器。根据任务类型和实体，生成需要获取的数据列表。
    核心目标：估值任务只取估值相关数据，不会跑完整 V3 十五章。

参数说明：
    无直接参数，通过调用 plan_requirements 验证行为

返回值说明：
    所有测试应通过

异常处理：
    测试失败会抛出 AssertionError
"""

import pytest


def test_planner_generates_requirements_for_stock_deep_dive():
    """个股深研应生成全量数据需求"""
    from smr_app.research.task_requirements import DataRequirementPlanner

    planner = DataRequirementPlanner()
    reqs = planner.plan_requirements(
        task_type="stock_deep_dive",
        entities=[{"ticker": "688041.SH", "role": "target"}],
    )

    assert len(reqs) > 0
    data_types = [r.data_type for r in reqs]
    # 个股深研需要市场、财务、新闻、估值数据
    assert "market_cap" in data_types or "market_data" in data_types
    assert "financial_statements" in data_types or "financial_data" in data_types
    assert "news" in data_types or "latest_news" in data_types


def test_planner_generates_minimal_requirements_for_valuation():
    """估值任务应只取估值相关数据，不获取全部十五章"""
    from smr_app.research.task_requirements import DataRequirementPlanner

    planner = DataRequirementPlanner()
    reqs = planner.plan_requirements(
        task_type="operating_driver_valuation",
        entities=[{"ticker": "688041.SH", "role": "target"}],
    )

    data_types = [r.data_type for r in reqs]
    # 估值任务需要财务和市场数据
    assert "financial_statements" in data_types or "financial_data" in data_types
    assert "market_cap" in data_types or "market_data" in data_types
    # 估值任务不需要新闻扫描
    assert "news" not in data_types and "latest_news" not in data_types, \
        "估值任务不应获取新闻数据"


def test_planner_generates_requirements_for_claim_correction():
    """纠错任务只取被纠正字段相关的数据"""
    from smr_app.research.task_requirements import DataRequirementPlanner

    planner = DataRequirementPlanner()
    reqs = planner.plan_requirements(
        task_type="claim_correction",
        entities=[{"ticker": "002396.SZ", "role": "target"}],
        correction_target={"field": "market_cap", "claimed_value": 260},
    )

    assert len(reqs) > 0
    # 纠错任务应包含市值数据
    data_types = [r.data_type for r in reqs]
    assert "market_cap" in data_types, "纠错任务应获取市值数据"


def test_planner_generates_requirements_for_pair_comparison():
    """双标的比较应为两个标的生成同口径数据需求"""
    from smr_app.research.task_requirements import DataRequirementPlanner

    planner = DataRequirementPlanner()
    reqs = planner.plan_requirements(
        task_type="pair_switch_decision",
        entities=[
            {"ticker": "300274.SZ", "role": "sell"},
            {"ticker": "688041.SH", "role": "buy"},
        ],
    )

    # 两个标的都应该有数据需求
    entities_in_reqs = set(r.entity_key for r in reqs)
    assert "300274.SZ" in entities_in_reqs
    assert "688041.SH" in entities_in_reqs

    # 两个标的的数据类型应该一致（同口径）
    reqs_a = [r.data_type for r in reqs if r.entity_key == "300274.SZ"]
    reqs_b = [r.data_type for r in reqs if r.entity_key == "688041.SH"]
    assert set(reqs_a) == set(reqs_b), "双标的比较应为同口径数据需求"


def test_planner_requirement_has_priority_and_authority():
    """每个需求应包含优先级和最低权威等级"""
    from smr_app.research.task_requirements import DataRequirementPlanner

    planner = DataRequirementPlanner()
    reqs = planner.plan_requirements(
        task_type="operating_driver_valuation",
        entities=[{"ticker": "688041.SH", "role": "target"}],
    )

    for req in reqs:
        assert hasattr(req, "priority"), "需求应包含优先级"
        assert hasattr(req, "min_authority_tier"), "需求应包含最低权威等级"
        assert req.priority in ("critical", "important", "nice_to_have")
        assert isinstance(req.min_authority_tier, int)
        assert 1 <= req.min_authority_tier <= 4


def test_planner_unknown_task_returns_empty():
    """未知任务类型应返回空需求列表"""
    from smr_app.research.task_requirements import DataRequirementPlanner

    planner = DataRequirementPlanner()
    reqs = planner.plan_requirements(
        task_type="unknown_task",
        entities=[{"ticker": "688041.SH"}],
    )

    assert reqs == []
