"""
ToolResult 统一返回字段契约测试

功能说明：
    测试所有金融工具返回的统一数据结构。
    核心目标：不管用哪个工具取数据，返回格式都是一致的，
    这样上游代码不需要为每个工具写特殊处理。

参数说明：
    无直接参数，通过构造和验证 ToolResult 对象测试

返回值说明：
    所有测试应通过，如果失败说明契约实现有问题

异常处理：
    测试失败会抛出 AssertionError
"""

import pytest
from datetime import date


def test_tool_result_creates_with_all_required_fields():
    """测试 ToolResult 包含全部 14 个必填字段"""
    from smr_app.research.tool_result import ToolResult

    result = ToolResult(
        entity_key="688041.SH",
        data_type="market_cap",
        as_of="2026-07-22",
        available_through="local_db",
        fetched_at="2026-07-22T10:00:00Z",
        source_ids=["tencent_quote"],
        authority_tier=1,
        evidence_ids=["ev_001"],
        unit="亿元",
        currency="CNY",
        period=None,
        freshness_status="fresh",
        conflicts=[],
        allowed_usage=["valuation", "comparison"],
        payload={"value": 2600},
    )

    assert result.entity_key == "688041.SH"
    assert result.data_type == "market_cap"
    assert result.as_of == "2026-07-22"
    assert result.available_through == "local_db"
    assert result.fetched_at == "2026-07-22T10:00:00Z"
    assert result.source_ids == ["tencent_quote"]
    assert result.authority_tier == 1
    assert result.evidence_ids == ["ev_001"]
    assert result.unit == "亿元"
    assert result.currency == "CNY"
    assert result.period is None
    assert result.freshness_status == "fresh"
    assert result.conflicts == []
    assert result.allowed_usage == ["valuation", "comparison"]
    assert result.payload == {"value": 2600}


def test_tool_result_serializes_to_json():
    """测试 ToolResult 可序列化为 JSON 并往返"""
    import json
    from smr_app.research.tool_result import ToolResult

    result = ToolResult(
        entity_key="688041.SH",
        data_type="market_cap",
        as_of="2026-07-22",
        available_through="local_db",
        fetched_at="2026-07-22T10:00:00Z",
        source_ids=["tencent_quote"],
        authority_tier=1,
        evidence_ids=["ev_001"],
        unit="亿元",
        currency="CNY",
        period=None,
        freshness_status="fresh",
        conflicts=[],
        allowed_usage=["valuation"],
        payload={"value": 2600},
    )

    json_str = result.to_json()
    assert isinstance(json_str, str)

    restored = ToolResult.from_json(json_str)
    assert restored.entity_key == "688041.SH"
    assert restored.payload == {"value": 2600}


def test_tool_result_validates_authority_tier():
    """测试权威等级必须在 1-4 之间"""
    from smr_app.research.tool_result import ToolResult

    with pytest.raises((ValueError, TypeError)):
        ToolResult(
            entity_key="688041.SH",
            data_type="market_cap",
            as_of="2026-07-22",
            available_through="local_db",
            fetched_at="2026-07-22T10:00:00Z",
            source_ids=["source"],
            authority_tier=0,  # 非法
            evidence_ids=[],
            unit="亿元",
            currency="CNY",
            period=None,
            freshness_status="fresh",
            conflicts=[],
            allowed_usage=[],
            payload={},
        )


def test_tool_result_validates_freshness_status():
    """测试新鲜度状态只接受预定义值"""
    from smr_app.research.tool_result import ToolResult

    with pytest.raises((ValueError, TypeError)):
        ToolResult(
            entity_key="688041.SH",
            data_type="market_cap",
            as_of="2026-07-22",
            available_through="local_db",
            fetched_at="2026-07-22T10:00:00Z",
            source_ids=["source"],
            authority_tier=1,
            evidence_ids=[],
            unit="亿元",
            currency="CNY",
            period=None,
            freshness_status="unknown_status",  # 非法
            conflicts=[],
            allowed_usage=[],
            payload={},
        )


def test_tool_result_marks_stale_data():
    """测试过期数据被标记为 stale"""
    from smr_app.research.tool_result import ToolResult

    result = ToolResult(
        entity_key="688041.SH",
        data_type="market_cap",
        as_of="2025-01-01",  # 很旧的数据
        available_through="local_db",
        fetched_at="2025-01-01T10:00:00Z",
        source_ids=["source"],
        authority_tier=1,
        evidence_ids=[],
        unit="亿元",
        currency="CNY",
        period=None,
        freshness_status="stale",
        conflicts=[],
        allowed_usage=[],
        payload={"value": 2000},
    )

    assert result.freshness_status == "stale"
    assert result.is_stale() is True


def test_tool_result_detects_conflicts():
    """测试冲突检测"""
    from smr_app.research.tool_result import ToolResult

    result = ToolResult(
        entity_key="688041.SH",
        data_type="market_cap",
        as_of="2026-07-22",
        available_through="local_db",
        fetched_at="2026-07-22T10:00:00Z",
        source_ids=["source_a", "source_b"],
        authority_tier=1,
        evidence_ids=[],
        unit="亿元",
        currency="CNY",
        period=None,
        freshness_status="fresh",
        conflicts=[{"field": "value", "source_a": 2600, "source_b": 2550}],
        allowed_usage=[],
        payload={"value": 2600},
    )

    assert result.has_conflicts() is True
