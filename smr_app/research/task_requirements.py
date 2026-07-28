"""
DataRequirementPlanner - 任务数据需求计划器

功能说明：
    根据任务类型和实体，生成需要获取的数据列表。
    核心目标：估值任务只取估值相关数据，不会跑完整 V3 十五章。

    每种任务类型有自己的数据需求模板：
    - stock_deep_dive: 全量数据（市场+财务+新闻+估值）
    - operating_driver_valuation: 只取财务+市场+估值（不取新闻）
    - pair_switch_decision: 两个标的同口径数据
    - theme_expectation_gap: 主题+市场+财务
    - claim_correction: 只取被纠正字段相关数据

参数说明：
    plan_requirements(task_type, entities, **kwargs) - 生成数据需求计划

返回值说明：
    返回 DataRequirement 列表，每个包含：
    - entity_key: 实体标识
    - data_type: 数据类型
    - priority: 优先级（critical/important/nice_to_have）
    - min_authority_tier: 最低权威等级
    - as_of: 要求的数据时点

异常处理：
    未知任务类型返回空列表（不抛异常）
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DataRequirement:
    """
    单条数据需求

    小白讲解：
        这就像购物清单上的一条——"买鸡蛋（critical），要新鲜的（authority_tier<=2）"。
    """
    entity_key: str
    data_type: str
    priority: str  # critical / important / nice_to_have
    min_authority_tier: int  # 1-4，越小越权威
    as_of: Optional[str] = None  # 要求的数据时点
    period: Optional[str] = None  # 报告期（如 "2025Q4"）


# === 任务数据需求模板 ===
# 小白讲解：这是每种任务的"购物清单"模板。
# 比如估值任务只需要财务和市场数据，不需要新闻。
# 格式：(data_type, priority, min_authority_tier)
_TASK_TEMPLATES = {
    "stock_deep_dive": [
        ("market_data", "critical", 2),
        ("market_cap", "critical", 2),
        ("financial_statements", "critical", 1),
        ("financial_data", "critical", 1),
        ("valuation_metrics", "important", 2),
        ("news", "important", 3),
        ("industry_chain", "nice_to_have", 3),
    ],
    "operating_driver_valuation": [
        ("financial_statements", "critical", 1),
        ("financial_data", "critical", 1),
        ("market_cap", "critical", 2),
        ("market_data", "critical", 2),
        ("valuation_metrics", "important", 2),
    ],
    "pair_switch_decision": [
        ("market_cap", "critical", 2),
        ("market_data", "critical", 2),
        ("financial_statements", "critical", 1),
        ("financial_data", "critical", 1),
        ("valuation_metrics", "important", 2),
    ],
    "theme_expectation_gap": [
        ("thematic_universe", "critical", 3),
        ("market_cap", "critical", 2),
        ("market_data", "critical", 2),
        ("financial_data", "important", 2),
    ],
    "industry_causal_explainer": [
        ("industry_chain", "critical", 3),
        ("news", "important", 3),
        ("market_data", "nice_to_have", 3),
    ],
    "company_signal_plan": [
        ("signal_data", "critical", 2),
        ("market_data", "important", 2),
        ("news", "nice_to_have", 3),
    ],
    "claim_correction": [
        # 纠错任务的需求在运行时根据 correction_target 动态生成
    ],
    "daily_brief": [
        ("market_indices", "critical", 2),
        ("top_gainers", "critical", 2),
        ("top_losers", "critical", 2),
        ("volume_surge", "important", 2),
        ("news", "important", 3),
    ],
    "portfolio_review": [
        ("portfolio_snapshot", "critical", 1),
        ("decisions", "critical", 1),
        ("market_data", "important", 2),
    ],
    "thesis_update": [
        ("memory", "critical", 1),
        ("news", "important", 3),
        ("market_data", "important", 2),
    ],
}


class DataRequirementPlanner:
    """
    任务数据需求计划器

    小白讲解：
        这是"购物清单生成器"。你告诉它要做什么菜（task_type），
        它就列出需要买的食材（数据需求）。
        估值任务和深研任务的购物清单不一样——
        估值任务不需要买新闻，深研任务什么都买。
    """

    def plan_requirements(
        self,
        task_type: str,
        entities: list,
        correction_target: Optional[dict] = None,
        **kwargs,
    ) -> list:
        """
        生成数据需求计划

        参数:
            task_type: 任务类型（如 "stock_deep_dive"）
            entities: 实体列表 [{"ticker": "688041.SH", "role": "target"}]
            correction_target: 纠错目标（仅 claim_correction 任务使用）
            **kwargs: 其他参数

        返回:
            DataRequirement 列表
        """
        # 未知任务类型返回空列表
        template = _TASK_TEMPLATES.get(task_type)
        if template is None:
            return []

        # 纠错任务：根据被纠正字段动态生成需求
        if task_type == "claim_correction" and correction_target:
            return self._plan_correction_requirements(entities, correction_target)

        # 普通任务：为每个实体生成模板中的数据需求
        requirements = []
        for entity in entities:
            ticker = entity.get("ticker") or entity.get("entity_key", "")
            if not ticker:
                continue

            for data_type, priority, min_tier in template:
                requirements.append(DataRequirement(
                    entity_key=ticker,
                    data_type=data_type,
                    priority=priority,
                    min_authority_tier=min_tier,
                ))

        return requirements

    def _plan_correction_requirements(
        self,
        entities: list,
        correction_target: dict,
    ) -> list:
        """
        为纠错任务生成数据需求

        小白讲解：
            用户说"市值是260亿不是199亿"，
            系统只需要重新获取市值数据来验证，
            不需要跑完整研究流程。
        """
        field = correction_target.get("field", "")
        ticker = entities[0].get("ticker", "") if entities else ""

        # 字段到数据类型的映射
        field_to_data_type = {
            "market_cap": "market_cap",
            "revenue": "financial_data",
            "net_income": "financial_data",
            "eps": "financial_data",
            "pe": "valuation_metrics",
            "pb": "valuation_metrics",
        }

        data_type = field_to_data_type.get(field, "market_cap")
        min_tier = 1 if data_type in ("financial_data", "financial_statements") else 2

        return [
            DataRequirement(
                entity_key=ticker,
                data_type=data_type,
                priority="critical",
                min_authority_tier=min_tier,
            ),
            # 同时获取财务数据以重算依赖项
            DataRequirement(
                entity_key=ticker,
                data_type="financial_data",
                priority="important",
                min_authority_tier=1,
            ),
        ]
