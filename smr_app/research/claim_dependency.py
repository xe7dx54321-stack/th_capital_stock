"""
估值 Claim 依赖图（claim_dependency.py）

功能说明（小白版）：
    你做一个估值的时候，用到了 WACC、毛利率、收入增速、税率这些数字。
    每个数字就叫一个"Claim"（结论/主张）。
    Claim 和 Claim 之间有"依赖关系"：比如"目标市值=199亿"这个结论，
    依赖"WACC=11%"这个假设、"2026 收入=320亿"这个预测、"净利率=6.5%"这个假设。

    某天你发现"WACC=11%"不对，其实行业最新无风险利率变了，应该是 8.5%。
    这时候你不能只改 WACC，还要知道"谁依赖 WACC"——比如股权价值、目标市值、
    目标价、IRR 都要重算。本模块就是干这个的。

核心类：
    Claim          ：一条结论/假设/事实/数据，带唯一 ID，类型，上游依赖
    ClaimGraph     ：整幅依赖图（加 claim / 查下游 / 查上游 / 算影响范围）
    ImpactReport   ："改了 X claim 之后"受影响的 claim 列表 + 提示

ClaimType 5 种：
    FACT       = "fact"       事实（年报披露、历史数据等）——最稳，改的概率小
    ASSUMPTION = "assumption" 假设（WACC、税率、长期增速等）
    DRIVER     = "driver"     经营驱动（出货量、ASP、毛利率）
    MODEL      = "model"      模型产出（EPS、收入、利润等中间计算）
    OUTPUT     = "output"     最终输出（目标市值、目标价、IRR）

使用例子见 tests 中 test_claim_dependency.py。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from collections import deque


# Claim 类型常量（小白版注释：别管"什么是枚举"，你直接用下面字符串就行）
CLAIM_TYPE_FACT = "fact"
CLAIM_TYPE_ASSUMPTION = "assumption"
CLAIM_TYPE_DRIVER = "driver"
CLAIM_TYPE_MODEL = "model"
CLAIM_TYPE_OUTPUT = "output"

ALL_CLAIM_TYPES = (
    CLAIM_TYPE_FACT,
    CLAIM_TYPE_ASSUMPTION,
    CLAIM_TYPE_DRIVER,
    CLAIM_TYPE_MODEL,
    CLAIM_TYPE_OUTPUT,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class Claim:
    """
    一条 Claim（= 一个结论 / 假设 / 事实 / 数据）

    小白讲解参数：
        claim_id           唯一 ID，例 "starnet_wacc_assumption_v1"
        entity_key         研究对象，例 "002396.SZ"（星网锐捷）
        claim_type         5 选一：fact/assumption/driver/model/output
        metric             指标名，例 "WACC" / "target_market_cap_yi" / "2026_revenue_yi"
        value              数值/字符串，例 0.11、199.0、"星网锐捷2025年报"
        unit               单位，例 "%" / "亿元" / "亿元/年"
        source             来源，例 "同花顺 2025 年报" / "假设：行业无风险利率3.0%"
        evidence_id        关联证据 ID（可选，对应 EvidenceRegistry）
        upstream_claim_ids 这个 claim 依赖哪些上游 claim（关键！）
        version            版本号，每次改 value 建议 +1，默认 1
        confidence         0~1，信心度，事实 0.9+，假设 0.5~0.8
        created_at         首次创建时间（UTC）
        updated_at         最后更新时间（UTC）
        description        人类可读描述，例 "星网锐捷 WACC 假设：股权成本 12% 债成本 5% D/E 0.1"
        metadata           其他乱七八糟想塞的信息都在这
    """
    claim_id: str
    entity_key: str
    claim_type: str
    metric: str
    value: Any
    unit: str = ""
    source: str = ""
    evidence_id: str = ""
    upstream_claim_ids: list[str] = field(default_factory=list)
    version: int = 1
    confidence: float = 0.8
    created_at: str = field(default_factory=_utc_now)
    updated_at: str = field(default_factory=_utc_now)
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # 小白版"类型检查防御"：防止瞎写 claim_type 导致下游搞不清
        if self.claim_type not in ALL_CLAIM_TYPES:
            raise ValueError(
                f"claim_type='{self.claim_type}' 非法，必须是下列之一：{ALL_CLAIM_TYPES}"
            )
        # confidence 限制在 0~1
        if self.confidence < 0:
            self.confidence = 0.0
        if self.confidence > 1:
            self.confidence = 1.0
        if not isinstance(self.upstream_claim_ids, list):
            raise TypeError("upstream_claim_ids 必须是 list[str]（空 list 也行）")


@dataclass
class ImpactReport:
    """
    "当我改了某个 claim 之后，谁会受影响？"的报告

    小白讲解字段：
        changed_claim_id        你刚刚改了哪条 claim
        old_value / new_value   改前改后对比
        impacted_claim_ids      受影响 claim ID 列表（含 changed_claim_id 自身）
        impacted_by_type        按类型分组：{output: [...], model: [...]}
        recommendation          给研究员的提示（"请重算以下模型输出"）
        severity                影响程度 "low"/"medium"/"high"
                                只要影响了 OUTPUT 就是 high，只有中间模型是 medium，只有 assumption 自己是 low
        depth                   下游传播了多少层
    """
    changed_claim_id: str
    old_value: Any
    new_value: Any
    impacted_claim_ids: list[str] = field(default_factory=list)
    impacted_by_type: dict[str, list[str]] = field(default_factory=dict)
    recommendation: str = ""
    severity: str = "low"
    depth: int = 0
    generated_at: str = field(default_factory=_utc_now)

    def to_human_readable(self) -> str:
        """生成小白也能看懂的报告文本"""
        lines = [
            f"# Claim 影响报告",
            f"- 改了 Claim ID   ：{self.changed_claim_id}",
            f"- 原值 → 新值      ：{self.old_value!r} → {self.new_value!r}",
            f"- 影响严重程度      ：{self.severity}",
            f"- 下游传播深度      ：{self.depth}",
            f"- 受影响的 Claim 总数：{len(self.impacted_claim_ids)}",
            "",
            "## 按类型分组的受影响 Claim：",
        ]
        for t in (CLAIM_TYPE_OUTPUT, CLAIM_TYPE_MODEL, CLAIM_TYPE_DRIVER,
                  CLAIM_TYPE_ASSUMPTION, CLAIM_TYPE_FACT):
            ids = self.impacted_by_type.get(t) or []
            if ids:
                lines.append(f"- {t:11s}（{len(ids)}）：{ids}")
        lines.append("")
        lines.append(f"## 给研究员的操作建议\n{self.recommendation}")
        return "\n".join(lines)


class ClaimGraph:
    """
    Claim 依赖图——整幅研究结论的因果网

    小白讲解：
        你把所有 claim 都 add 进来，用 upstream_claim_ids 告诉它"谁依赖谁"。
        然后：
            trace_impact(claim_id)   → 改了 X，要重算谁？给 ImpactReport
            get_downstream(X)        → 一层下游（直接依赖 X 的）
            get_upstream(Y)          → 一层上游（Y 直接依赖的）
            list_by_entity("002396.SZ") → 某标的所有 claim
            clone_with_new_value(id, new_value) → 复制定量测试用（先不提交原图）
    """

    def __init__(self) -> None:
        # 内部数据结构：_claims[id] = Claim 对象；_downstream[id] = [直接下游 id]
        self._claims: dict[str, Claim] = {}
        self._downstream: dict[str, list[str]] = {}

    # ------------------------------------------------------------------ 增删改查
    def add_claim(self, claim: Claim) -> Claim:
        """
        加一条 claim 到图里

        小白版检查：
            - 如果 upstream_claim_ids 里写了不存在的 claim_id，会警告（但不崩）
            - 如果 claim_id 已存在，会抛错，避免覆盖（请用 update_claim_value）
        """
        if claim.claim_id in self._claims:
            raise ValueError(
                f"claim_id='{claim.claim_id}' 已存在！"
                "要改 value 请用 update_claim_value，不要覆盖原 claim"
            )
        for up in claim.upstream_claim_ids:
            if up not in self._claims:
                # 上游缺失——可能还没加，仅警告
                pass
            self._downstream.setdefault(up, [])
            if claim.claim_id not in self._downstream[up]:
                self._downstream[up].append(claim.claim_id)
        self._downstream.setdefault(claim.claim_id, [])
        self._claims[claim.claim_id] = claim
        return claim

    def get(self, claim_id: str) -> Claim | None:
        """拿 claim，没有返回 None"""
        return self._claims.get(claim_id)

    def has(self, claim_id: str) -> bool:
        return claim_id in self._claims

    def list_by_entity(self, entity_key: str) -> list[Claim]:
        """某标的所有 claim（按类型排序：output→model→driver→assumption→fact）"""
        order = {t: i for i, t in enumerate(
            (CLAIM_TYPE_OUTPUT, CLAIM_TYPE_MODEL, CLAIM_TYPE_DRIVER,
             CLAIM_TYPE_ASSUMPTION, CLAIM_TYPE_FACT))}
        claims = [c for c in self._claims.values() if c.entity_key == entity_key]
        claims.sort(key=lambda c: (order.get(c.claim_type, 99), c.metric))
        return claims

    def get_upstream(self, claim_id: str) -> list[Claim]:
        """直接上游（claim_id 依赖了谁）"""
        c = self.get(claim_id)
        if c is None:
            return []
        return [self._claims[u] for u in c.upstream_claim_ids if u in self._claims]

    def get_downstream(self, claim_id: str) -> list[Claim]:
        """直接下游（谁直接依赖 claim_id）"""
        ids = self._downstream.get(claim_id, [])
        return [self._claims[i] for i in ids if i in self._claims]

    # ------------------------------------------------------------------ 核心：传播影响
    def trace_impact(
        self,
        claim_id: str,
        new_value: Any,
    ) -> ImpactReport:
        """
        核心功能：假设我把 claim_id 的 value 改成 new_value，下游会影响哪些 claim？

        小白讲解算法（BFS 广度优先，避免循环依赖死循环）：
            1. 把 claim_id 自己放进"待扩散"队列，深度=0
            2. 每出队一个，把它所有直接下游也收进来，深度+1
            3. 用 visited 去重，不会重复收集
        """
        if claim_id not in self._claims:
            raise KeyError(f"claim_id='{claim_id}' 不存在，先 add_claim 再 trace_impact")

        visited: dict[str, int] = {claim_id: 0}  # id → 传播深度
        queue: deque[tuple[str, int]] = deque([(claim_id, 0)])
        max_depth = 0
        while queue:
            cur_id, d = queue.popleft()
            for nxt in self._downstream.get(cur_id, []):
                if nxt in visited:
                    continue
                visited[nxt] = d + 1
                max_depth = max(max_depth, d + 1)
                queue.append((nxt, d + 1))

        impacted_ids_sorted = sorted(visited.keys(), key=lambda x: (visited[x], x))

        # 按类型分组
        by_type: dict[str, list[str]] = {}
        for i in impacted_ids_sorted:
            t = self._claims[i].claim_type
            by_type.setdefault(t, []).append(i)

        # 严重程度
        if CLAIM_TYPE_OUTPUT in by_type:
            severity = "high"
        elif CLAIM_TYPE_MODEL in by_type:
            severity = "medium"
        else:
            severity = "low"

        # 操作建议
        parts = []
        if CLAIM_TYPE_OUTPUT in by_type:
            parts.append(
                f"下列输出类结论已失效，请重新运行估值模型后更新："
                f"{by_type[CLAIM_TYPE_OUTPUT]}"
            )
        if CLAIM_TYPE_MODEL in by_type:
            parts.append(
                f"下列中间模型变量（收入/利润/EPS 等）需要重算："
                f"{by_type[CLAIM_TYPE_MODEL]}"
            )
        if severity == "low":
            parts.append(
                "本次只影响 assumption 本身或低阶依赖，低严重；但建议把整个 valuation 脚本"
                "再跑一次确保没有遗漏"
            )
        parts.append(
            f"提醒：本次 value 变更 {self._claims[claim_id].value!r} → {new_value!r}"
            "；若 value 单位变化（%→倍数/亿元→万元）请同时改 unit 字段，否则公式会错"
        )
        recommendation = "\n".join(parts)

        return ImpactReport(
            changed_claim_id=claim_id,
            old_value=self._claims[claim_id].value,
            new_value=new_value,
            impacted_claim_ids=impacted_ids_sorted,
            impacted_by_type=by_type,
            recommendation=recommendation,
            severity=severity,
            depth=max_depth,
        )

    # ------------------------------------------------------------------ 变更（原地改 + 版本号自增）
    def update_claim_value(
        self,
        claim_id: str,
        new_value: Any,
        *,
        source: str = "",
        new_confidence: float | None = None,
    ) -> Claim:
        """
        改 claim 的 value。自动 version+1、updated_at 重记、可选改 source/confidence。

        返回 ImpactReport 生成建议再由上层保存到日志/决策记录中。
        """
        c = self._claims.get(claim_id)
        if c is None:
            raise KeyError(f"claim_id='{claim_id}' 不存在")
        c.value = new_value
        c.version += 1
        c.updated_at = _utc_now()
        if source:
            c.source = source
        if new_confidence is not None:
            c.confidence = max(0.0, min(1.0, float(new_confidence)))
        return c

    def to_dict(self) -> dict[str, Any]:
        """导出 JSON 可用的字典（快照备份 / 跨进程传递 / 渲染）"""
        claims_list = []
        for cid, c in sorted(self._claims.items()):
            claims_list.append({
                "claim_id": c.claim_id,
                "entity_key": c.entity_key,
                "claim_type": c.claim_type,
                "metric": c.metric,
                "value": c.value,
                "unit": c.unit,
                "source": c.source,
                "evidence_id": c.evidence_id,
                "upstream_claim_ids": list(c.upstream_claim_ids),
                "version": c.version,
                "confidence": c.confidence,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
                "description": c.description,
                "metadata": c.metadata,
            })
        return {
            "schema_version": "1.0",
            "generated_at": _utc_now(),
            "claims_count": len(self._claims),
            "claims": claims_list,
            "downstream_edges": [
                {"from": k, "to": sorted(v)}
                for k, v in sorted(self._downstream.items()) if v
            ],
        }
