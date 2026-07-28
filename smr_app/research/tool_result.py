"""
ToolResult - 金融工具统一返回字段契约

功能说明：
    所有金融工具（行情、财务、估值、新闻等）返回的数据都必须使用这个统一结构。
    核心目标：不管用哪个工具取数据，返回格式都是一致的，
    这样上游代码不需要为每个工具写特殊处理。

    14 个必填字段：
    - entity_key: 实体标识（如 "688041.SH"）
    - data_type: 数据类型（如 "market_cap", "financial_statements"）
    - as_of: 数据时点（如 "2026-07-22"）
    - available_through: 获取途径（如 "local_db", "api", "cache"）
    - fetched_at: 获取时间戳（ISO 8601）
    - source_ids: 数据源 ID 列表
    - authority_tier: 权威等级（1=交易所/官方公告, 2=持牌数据商, 3=聚合站, 4=推断）
    - evidence_ids: 关联的证据 ID 列表
    - unit: 单位（如 "亿元", "倍"）
    - currency: 币种（如 "CNY", "USD"）
    - period: 报告期（如 "2025Q4", None 表示非报告期数据）
    - freshness_status: 新鲜度状态（fresh/stale/cache_miss/provider_failure）
    - conflicts: 冲突列表（多数据源返回不同值时记录）
    - allowed_usage: 允许用途列表（如 ["valuation", "comparison"]）
    - payload: 实际数据载荷

参数说明：
    ToolResult(...) - 构造一个工具结果
    to_json() - 序列化为 JSON 字符串
    from_json(json_str) - 从 JSON 字符串恢复

返回值说明：
    is_stale() - 是否过期
    has_conflicts() - 是否有冲突

异常处理：
    非法权威等级、非法新鲜度状态会抛出 ValueError
"""

# === 合法的新鲜度状态 ===
# 小白讲解：数据的新鲜度有四种状态：
# - fresh: 数据是最新的，在有效期内
# - stale: 数据已过期，但仍有参考价值
# - cache_miss: 缓存中没有这个数据，需要从源头获取
# - provider_failure: 数据源不可用或返回错误
VALID_FRESHNESS_STATUS = frozenset({
    "fresh",
    "stale",
    "cache_miss",
    "provider_failure",
})

# === 合法的权威等级 ===
# 小白讲解：数据的可靠性分四级：
# - 1: 交易所/官方公告（最可靠）
# - 2: 持牌数据商（如 Wind、东方财富）
# - 3: 聚合站（如新浪财经、雪球）
# - 4: 推断（从其他数据推导，最不可靠）
VALID_AUTHORITY_TIERS = frozenset({1, 2, 3, 4})


class ToolResult:
    """
    金融工具统一返回字段契约

    小白讲解：
        这就像快递包裹的标准格式——不管里面装的是行情数据还是财务数据，
        外面的包装都一样：收件人（entity_key）、物品类型（data_type）、
        发货时间（fetched_at）、来源（source_ids）、可靠性评级（authority_tier）。
        这样收件人不需要为每种物品写不同的拆包方法。
    """

    __slots__ = (
        "entity_key", "data_type", "as_of", "available_through",
        "fetched_at", "source_ids", "authority_tier", "evidence_ids",
        "unit", "currency", "period", "freshness_status",
        "conflicts", "allowed_usage", "payload",
    )

    def __init__(
        self,
        entity_key: str,
        data_type: str,
        as_of: str,
        available_through: str,
        fetched_at: str,
        source_ids: list,
        authority_tier: int,
        evidence_ids: list,
        unit: str,
        currency: str,
        period,
        freshness_status: str,
        conflicts: list,
        allowed_usage: list,
        payload: dict,
    ):
        # === 验证必填字段 ===
        if not entity_key:
            raise ValueError("entity_key 不能为空")
        if not data_type:
            raise ValueError("data_type 不能为空")
        if authority_tier not in VALID_AUTHORITY_TIERS:
            raise ValueError(
                f"authority_tier 必须在 {sorted(VALID_AUTHORITY_TIERS)} 之间，"
                f"收到 {authority_tier}"
            )
        if freshness_status not in VALID_FRESHNESS_STATUS:
            raise ValueError(
                f"freshness_status 必须是 {sorted(VALID_FRESHNESS_STATUS)} 之一，"
                f"收到 {freshness_status}"
            )

        self.entity_key = entity_key
        self.data_type = data_type
        self.as_of = as_of
        self.available_through = available_through
        self.fetched_at = fetched_at
        self.source_ids = list(source_ids) if source_ids else []
        self.authority_tier = authority_tier
        self.evidence_ids = list(evidence_ids) if evidence_ids else []
        self.unit = unit
        self.currency = currency
        self.period = period
        self.freshness_status = freshness_status
        self.conflicts = list(conflicts) if conflicts else []
        self.allowed_usage = list(allowed_usage) if allowed_usage else []
        self.payload = payload if payload else {}

    def is_stale(self) -> bool:
        """是否过期"""
        return self.freshness_status == "stale"

    def has_conflicts(self) -> bool:
        """是否有数据冲突"""
        return len(self.conflicts) > 0

    def to_json(self) -> str:
        """序列化为 JSON 字符串"""
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "entity_key": self.entity_key,
            "data_type": self.data_type,
            "as_of": self.as_of,
            "available_through": self.available_through,
            "fetched_at": self.fetched_at,
            "source_ids": self.source_ids,
            "authority_tier": self.authority_tier,
            "evidence_ids": self.evidence_ids,
            "unit": self.unit,
            "currency": self.currency,
            "period": self.period,
            "freshness_status": self.freshness_status,
            "conflicts": self.conflicts,
            "allowed_usage": self.allowed_usage,
            "payload": self.payload,
        }

    @classmethod
    def from_json(cls, json_str: str) -> "ToolResult":
        """从 JSON 字符串恢复"""
        import json
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> "ToolResult":
        """从字典恢复"""
        return cls(
            entity_key=data["entity_key"],
            data_type=data["data_type"],
            as_of=data["as_of"],
            available_through=data["available_through"],
            fetched_at=data["fetched_at"],
            source_ids=data.get("source_ids", []),
            authority_tier=data["authority_tier"],
            evidence_ids=data.get("evidence_ids", []),
            unit=data.get("unit", ""),
            currency=data.get("currency", ""),
            period=data.get("period"),
            freshness_status=data["freshness_status"],
            conflicts=data.get("conflicts", []),
            allowed_usage=data.get("allowed_usage", []),
            payload=data.get("payload", {}),
        )

    def __repr__(self) -> str:
        return (
            f"ToolResult(entity={self.entity_key}, type={self.data_type}, "
            f"as_of={self.as_of}, tier={self.authority_tier}, "
            f"fresh={self.freshness_status})"
        )
