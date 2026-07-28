"""
产业因果链（Causal Chain）- 把"为什么需求存在但没行情"拆成证据化的 8 步

功能说明：
    阶段 9「产业因果解释 V1」的核心数据结构模块。

    解决的问题：小白经常问："DCI 需求明明存在，为什么 A 股相关公司一直没有行情？"
    本模块把这种"感觉"拆解为 8 个必须分别证明的因果节点，
    每条因果边标注清楚：是硬事实（evidence_id 支撑的 fact）还是逻辑推断（inferred）。

    固定 8 步分析框架（严格来自 master plan 阶段 9）：
        1 终端需求是否真实？（不能拿媒体稿件当事实）
        2 需求位于产业链哪个节点？（上游资本开支 vs 下游出货量 vs 终端采购）
        3 A 股是否有纯正可投资映射？（标的收入占比 / 业务纯度）
        4 市场注意力是否被其他叙事占用？（AI vs 消费 vs 政策主题）
        5 订单如何传导到收入和利润？（订单→排产→出货→开票→确认收入→利润）
        6 传导需要多长时间？（几个季度？历史案例耗时多久）
        7 什么催化会改变市场定价？（催化剂清单 + 观察指标）
        8 什么证据会证伪当前解释？（反例清单 + 失效条件）

    同时必须列出：替代解释（Alternative Explanations）和证伪条件（Falsification），
    避免"确认偏误"——只看支持自己观点的证据。

参数说明：
    CausalNode      - 8 步框架中的一个节点（编号/标题/结论摘要/证据列表/信心度）
    CausalEdge      - 从节点 A 到节点 B 的因果边（标注 fact vs inferred，evidence_id）
    CausalChain     - 整条因果链 = 8 个 CausalNode + 边 + 替代解释 + 证伪条件
    CausalRenderer  - 产出结构化 causal_chain_artifact（JSON + Markdown）

返回值说明：
    CausalChain.evaluate() → {"ready": True/False, "fatal_gaps": [...],
                               "confirmed_count": n, "inferred_count": m}
    CausalRenderer.to_markdown() → 人能看懂的因果报告
    永远不抛异常（输入非法返回"框架未完成 + 缺口列表"）

异常处理：
    节点缺失 / 边缺失 / 证据格式错 → 不崩，记录到 fatal_gaps / warnings
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
import json


# ============================================================================
# 8 步框架常量（严格按 master plan 阶段 9 顺序）
# ============================================================================

STEP_DEMAND_REAL = 1          # 1. 终端需求是否真实？
STEP_CHAIN_LOCATION = 2       # 2. 产业链位置
STEP_A_SHARE_MAPPING = 3      # 3. A 股可投资映射
STEP_NARRATIVE_COMPETE = 4    # 4. 市场叙事竞争
STEP_TRANSMISSION = 5         # 5. 订单→利润传导
STEP_TRANSMISSION_TIME = 6    # 6. 传导耗时
STEP_CATALYST = 7             # 7. 定价催化
STEP_FALSIFICATION = 8        # 8. 证伪条件

STEP_LABELS = {
    STEP_DEMAND_REAL: "终端需求是否真实",
    STEP_CHAIN_LOCATION: "需求位于产业链哪个节点",
    STEP_A_SHARE_MAPPING: "A 股是否有纯正可投资映射",
    STEP_NARRATIVE_COMPETE: "市场注意力是否被其他叙事占用",
    STEP_TRANSMISSION: "订单如何传导到收入和利润",
    STEP_TRANSMISSION_TIME: "传导需要多长时间",
    STEP_CATALYST: "什么催化会改变市场定价",
    STEP_FALSIFICATION: "什么证据会证伪当前解释",
}

ALL_STEPS = (STEP_DEMAND_REAL, STEP_CHAIN_LOCATION, STEP_A_SHARE_MAPPING,
             STEP_NARRATIVE_COMPETE, STEP_TRANSMISSION, STEP_TRANSMISSION_TIME,
             STEP_CATALYST, STEP_FALSIFICATION)


# ============================================================================
# 边的事实/推断分类
# ============================================================================

EDGE_FACT = "fact"
EDGE_INFERRED = "inferred"


# ============================================================================
# 数据结构
# ============================================================================

@dataclass
class EvidenceSlim:
    """
    轻量证据引用（与 graph_evidence.py 的 EvidenceRegistry 呼应）

    小白讲解：
        每条结论下面要列"谁说的"。
        evidence_id 要能在 ArtifactStore / EvidenceRegistry 里查到原件。
    """
    evidence_id: str = ""      # 对应 EvidenceRegistry 的 ID
    summary: str = ""          # 一句话摘要（例：DCI 联盟 2026 Q1 招标金额同比+50%）
    source_tier: int = 4       # 1~4 权威等级（越小越权威）
    fact: bool = False         # True=硬事实支撑，False=推断

    def __post_init__(self):
        if self.source_tier < 1:
            self.source_tier = 1
        if self.source_tier > 4:
            self.source_tier = 4


@dataclass
class CausalNode:
    """
    因果链中的一个节点（对应 8 步框架中的 1 步）

    小白讲解：
        step=1 就是"需求是否真实"这一步的完整分析：
        结论（conclusion 例如"需求真实，已有 Q1 招标数据+运营商集采公告"），
        证据列表（evidences 至少 1 条最好是 1~2 级权威源），
        confidence 0~1 自己对这一步结论的信心（没证据=0，有3条公告=0.9）。
    """
    step: int                          # 1~8
    title: str = ""                    # 通常取 STEP_LABELS[step]
    conclusion: str = ""               # 结论摘要（一句话，小白能看懂）
    detail: str = ""                   # 详细文字分析
    evidences: list[EvidenceSlim] = field(default_factory=list)
    confidence: float = 0.0            # 0~1
    completed: bool = False            # 是否已完成（有结论且≥1条证据或明确"无结论"）
    alternative_findings: list[str] = field(default_factory=list)  # 本节点内的反面证据

    def __post_init__(self):
        if self.step not in ALL_STEPS:
            self.step = STEP_DEMAND_REAL
        if not self.title:
            self.title = STEP_LABELS.get(self.step, f"步骤 {self.step}")
        if self.confidence < 0:
            self.confidence = 0.0
        if self.confidence > 1:
            self.confidence = 1.0


@dataclass
class CausalEdge:
    """
    因果链中的一条边（从 step_i → step_{i+1}，例如 需求真实 → 映射到 A 股）

    小白讲解：
        边代表"因为节点 A 成立，所以节点 B 才有可能成立"这种因果。
        必须标注这是事实边（有公告支撑）还是纯推断边（拍脑袋）。
        例如"DCI 联盟招标了 50% 增长 → 供应商下季度收入会增长"，如果有公司在手
        订单公告就是 fact 边；如果只是"按历史经验招标→收入大约 1 个季度"，就是 inferred 边。
    """
    from_step: int                     # 起点（1~7）
    to_step: int                       # 终点（2~8，= from_step+1）
    edge_kind: str = EDGE_INFERRED     # fact / inferred
    explanation: str = ""              # 为什么这条边成立？（一句话解释）
    evidence_id: str = ""              # fact 边必填（支撑传导机制的证据）
    historical_precedent: str = ""     # 历史案例（例：2024 光模块招标→Q3 收入确认）

    def __post_init__(self):
        if self.edge_kind not in (EDGE_FACT, EDGE_INFERRED):
            self.edge_kind = EDGE_INFERRED
        # fact 边强制要求 evidence_id
        if self.edge_kind == EDGE_FACT and not self.evidence_id:
            # 降级为 inferred（不抛异常）
            self.edge_kind = EDGE_INFERRED


@dataclass
class AlternativeExplanation:
    """
    替代解释（防止确认偏误）

    小白讲解：
        "为什么没行情"不能只看"传导需要时间"这一种解释。
        还要列出：是不是"行业内耗价格战导致利润端不兑现？"、
        "是不是大股东减持压制股价？"、"是不是估值已经反映了预期？"…
        每一种替代解释要讲清楚：会看什么指标来排除它？
    """
    title: str = ""                        # 简短标题（例：估值已反映）
    plausibility: float = 0.3              # 可信度 0~1（自己评估）
    how_to_falsify: str = ""               # 怎么证伪（例：查当前 PE band vs 历史 90 分位）
    current_evidence_against: str = ""     # 当前是否有证据排除（例：PE 仅 35x，在 5 年均值下方）


class CausalChain:
    """
    完整的产业因果链（8 个节点 + 7 条边 + 替代解释 + 证伪条件）

    用法（小白步骤）：
        1. chain = CausalChain(theme="DCI", question="为什么 DCI 需求没行情？")
        2. 用 set_node() 把 1~8 每一步的结论和证据填进去
        3. 用 set_edge() 把 7 条边的传导机制填进去
        4. 用 add_alternative() 加替代解释
        5. 调 evaluate() 看整体是否完成、有哪些致命缺口
        6. 调 renderer.to_markdown() 输出报告
    """

    def __init__(self, *, theme: str = "", question: str = "", entity_key: str = ""):
        self.theme = theme
        self.question = question
        self.entity_key = entity_key
        self.nodes: dict[int, CausalNode] = {}
        self.edges: list[CausalEdge] = []
        self.alternatives: list[AlternativeExplanation] = []
        self.warnings: list[str] = []
        self.created_at = _utc_now_iso()

    # ------------------------------------------------------------------
    # 核心写入 API（都是写进去再校验，不抛异常）
    # ------------------------------------------------------------------

    def set_node(self, node: CausalNode) -> None:
        """写入/覆盖某一步节点"""
        if node.step not in ALL_STEPS:
            self.warnings.append(f"set_node 收到非法 step={node.step}，已忽略")
            return
        self.nodes[node.step] = node

    def set_edge(self, edge: CausalEdge) -> None:
        """写入一条边（自动校验步号连续）"""
        if edge.to_step != edge.from_step + 1:
            self.warnings.append(
                f"边 {edge.from_step}→{edge.to_step} 步号不连续，已接受但会标记风险"
            )
        # 不允许重复边
        for i, existing in enumerate(self.edges):
            if existing.from_step == edge.from_step and existing.to_step == edge.to_step:
                self.edges[i] = edge
                return
        self.edges.append(edge)

    def add_alternative(self, alt: AlternativeExplanation) -> None:
        """添加一个替代解释"""
        self.alternatives.append(alt)

    # ------------------------------------------------------------------
    # 核心校验：evaluate() - 回答"这条因果链质量怎么样？"
    # ------------------------------------------------------------------

    def evaluate(self) -> dict:
        """
        评估整条因果链的完整性和质量

        返回（小白能看懂的 dict）：
            - ready:            True/False（是否已经能支撑工作流输出）
            - completed_steps:  已完成节点数（0~8）
            - fact_edge_count:  7 条边中 fact 边的数量（理想 ≥3）
            - inferred_edge_count: 7 条边中 inferred 边数量
            - has_alternatives: 是否有≥1 个替代解释（必须 True，防确认偏误）
            - has_falsification:步骤 8 是否明确列了证伪条件
            - fatal_gaps:       致命缺口列表（空=无缺口）
            - confidence_overall: 整体信心度（0~1，8 步加权平均）
            - warnings:         警告列表
        """
        fatal_gaps: list[str] = []

        # 检查 1：8 个节点都得存在
        missing_steps = [s for s in ALL_STEPS if s not in self.nodes]
        if missing_steps:
            labels = "、".join(f"S{s}({STEP_LABELS[s]})" for s in missing_steps)
            fatal_gaps.append(f"缺少因果节点：{labels}")

        # 检查 2：8 个节点 confidence 之和要高（步骤 1/3/5/7 必须≥0.5）
        hard_steps = (STEP_DEMAND_REAL, STEP_A_SHARE_MAPPING, STEP_TRANSMISSION, STEP_CATALYST)
        for s in hard_steps:
            if s in self.nodes and self.nodes[s].confidence < 0.3:
                fatal_gaps.append(
                    f"关键节点 S{s}({STEP_LABELS[s]}) 信心度={self.nodes[s].confidence:.2f} 过低（<0.3）"
                )

        # 检查 3：必须有≥1 条替代解释
        if len(self.alternatives) < 1:
            fatal_gaps.append("至少需要 1 个替代解释（防确认偏误），当前 0 个")

        # 检查 4：步骤 8 证伪条件必须非空
        if STEP_FALSIFICATION in self.nodes and not self.nodes[STEP_FALSIFICATION].conclusion.strip():
            fatal_gaps.append("S8（证伪条件）结论为空——必须明确：什么情况出现就判定这条因果链错了")

        # 统计
        completed = sum(1 for s, n in self.nodes.items() if n.completed)
        fact_edges = sum(1 for e in self.edges if e.edge_kind == EDGE_FACT)
        inferred_edges = len(self.edges) - fact_edges
        confidence_values = [n.confidence for n in self.nodes.values()]
        overall = sum(confidence_values) / 8.0 if confidence_values else 0.0
        has_alt = len(self.alternatives) >= 1
        has_fals = STEP_FALSIFICATION in self.nodes and bool(self.nodes[STEP_FALSIFICATION].conclusion.strip())

        # 节点 1-8 每步至少 1 条边，7 条边
        expected_edges = 7
        if len(self.edges) < expected_edges:
            self.warnings.append(
                f"仅注册了 {len(self.edges)}/{expected_edges} 条因果边，部分节点之间的传导机制为空"
            )

        ready = len(fatal_gaps) == 0 and completed >= 6
        return {
            "theme": self.theme,
            "question": self.question,
            "ready": ready,
            "completed_steps": completed,
            "total_steps": 8,
            "fact_edge_count": fact_edges,
            "inferred_edge_count": inferred_edges,
            "has_alternatives": has_alt,
            "has_falsification": has_fals,
            "confidence_overall": round(overall, 3),
            "fatal_gaps": fatal_gaps,
            "warnings": list(self.warnings),
        }


class CausalRenderer:
    """把 CausalChain 渲染成 Markdown 报告 / JSON 制品"""

    @staticmethod
    def to_markdown(chain: CausalChain) -> str:
        """
        渲染成人类能看懂的 Markdown 报告

        结构：
            # 产业因果解释报告
            - 主题 / 问题
            - 8 步因果节点（每步：结论/信心度/证据）
            - 7 条因果边（fact vs inferred 分色）
            - 替代解释（重要！防确认偏误）
            - 证伪条件
            - 质量评估
        """
        eval_result = chain.evaluate()
        lines: list[str] = []
        title_parts = []
        if chain.theme:
            title_parts.append(chain.theme)
        if chain.entity_key:
            title_parts.append(chain.entity_key)
        title = " / ".join(title_parts) if title_parts else "产业因果解释"
        lines.append(f"# 产业因果解释 — {title}")
        lines.append(f"\n生成时间：{_utc_now_iso()}\n")
        if chain.question:
            lines.append(f"**核心问题：** {chain.question}\n")
        lines.append("---")

        # 8 步节点
        lines.append("## 8 步因果框架\n")
        for s in ALL_STEPS:
            n = chain.nodes.get(s)
            if n is None:
                lines.append(f"### S{s}. {STEP_LABELS[s]}")
                lines.append("_节点未填写_\n")
                continue
            status_icon = "✅" if n.completed else "⚠️"
            lines.append(f"### S{s}. {n.title} {status_icon}（信心度 {n.confidence:.0%}）\n")
            lines.append(f"**结论：** {n.conclusion or '（无）'}\n")
            if n.detail.strip():
                lines.append(f"{n.detail.strip()}\n")
            if n.evidences:
                lines.append("**证据：**\n")
                for i, ev in enumerate(n.evidences, 1):
                    tag = "[FACT]" if ev.fact else "[INFERRED]"
                    lines.append(
                        f"  {i}. {tag} T{ev.source_tier} `{ev.evidence_id}` — {ev.summary or '（无摘要）'}"
                    )
                lines.append("")
            if n.alternative_findings:
                lines.append("**反面/不确定证据：**")
                for f in n.alternative_findings:
                    lines.append(f"- {f}")
                lines.append("")

        # 边
        lines.append("## 因果传导机制\n")
        lines.append("| 边 | 类型 | 说明 | 证据 | 历史案例 |")
        lines.append("|---|---|---|---|---|")
        edges_sorted = sorted(chain.edges, key=lambda e: e.from_step)
        if edges_sorted:
            for e in edges_sorted:
                kind_cn = "事实" if e.edge_kind == EDGE_FACT else "推断"
                exp = e.explanation or "—"
                ev = f"`{e.evidence_id}`" if e.evidence_id else "—"
                precedent = e.historical_precedent or "—"
                lines.append(f"| S{e.from_step}→S{e.to_step} | {kind_cn} | {exp} | {ev} | {precedent} |")
        else:
            lines.append("| _（7 条边均未填写）_ | | | | |")
        lines.append("")

        # 替代解释
        lines.append("## 替代解释（排除确认偏误）\n")
        if chain.alternatives:
            lines.append("| # | 解释 | 可信度 | 如何证伪 | 当前排除证据 |")
            lines.append("|---|---|---|---|---|")
            for i, alt in enumerate(chain.alternatives, 1):
                falsify = alt.how_to_falsify or "—"
                against = alt.current_evidence_against or "—"
                lines.append(
                    f"| {i} | {alt.title or '（无标题）'} | {alt.plausibility:.0%} | {falsify} | {against} |"
                )
        else:
            lines.append("_（未提供替代解释，需警惕确认偏误）_")
        lines.append("")

        # 证伪条件
        lines.append("## 证伪条件（什么时候判定我错了？）\n")
        f8 = chain.nodes.get(STEP_FALSIFICATION)
        if f8 and f8.conclusion.strip():
            lines.append(f8.conclusion)
            if f8.detail.strip():
                lines.append(f"\n{f8.detail.strip()}")
        else:
            lines.append("_（S8 证伪条件未填写——强烈建议补上，避免自欺欺人）_")
        lines.append("")

        # 质量评估
        lines.append("## 质量评估\n")
        lines.append("| 指标 | 值 |")
        lines.append("|---|---|")
        ok_icon = "✅" if eval_result["ready"] else "❌"
        lines.append(f"| 整体可使用 {ok_icon} | {'是' if eval_result['ready'] else '否'} |")
        lines.append(f"| 完成节点 | {eval_result['completed_steps']}/8 |")
        lines.append(f"| 信心度（加权平均） | {eval_result['confidence_overall']:.0%} |")
        lines.append(f"| 因果边 - 事实/推断 | {eval_result['fact_edge_count']} / {eval_result['inferred_edge_count']} |")
        lines.append(f"| 有替代解释（防确认偏误）| {'是' if eval_result['has_alternatives'] else '否'} |")
        lines.append(f"| 有证伪条件 | {'是' if eval_result['has_falsification'] else '否'} |")
        if eval_result["fatal_gaps"]:
            lines.append("")
            lines.append("### 致命缺口\n")
            for g in eval_result["fatal_gaps"]:
                lines.append(f"- ❌ {g}")
        if eval_result["warnings"]:
            lines.append("")
            lines.append("### 警告\n")
            for w in eval_result["warnings"]:
                lines.append(f"- ⚠️ {w}")
        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def to_dict(chain: CausalChain) -> dict:
        """渲染成可序列化的 JSON 制品（用于工作流输出 artifact）"""
        nodes_d = {}
        for s, n in chain.nodes.items():
            nodes_d[str(s)] = {
                "step": s, "title": n.title, "conclusion": n.conclusion,
                "detail": n.detail, "confidence": n.confidence, "completed": n.completed,
                "evidences": [
                    {
                        "evidence_id": e.evidence_id, "summary": e.summary,
                        "source_tier": e.source_tier, "fact": e.fact,
                    }
                    for e in n.evidences
                ],
                "alternative_findings": list(n.alternative_findings),
            }
        edges_d = [
            {
                "from_step": e.from_step, "to_step": e.to_step,
                "edge_kind": e.edge_kind, "explanation": e.explanation,
                "evidence_id": e.evidence_id, "historical_precedent": e.historical_precedent,
            }
            for e in chain.edges
        ]
        alts_d = [
            {
                "title": a.title, "plausibility": a.plausibility,
                "how_to_falsify": a.how_to_falsify,
                "current_evidence_against": a.current_evidence_against,
            }
            for a in chain.alternatives
        ]
        return {
            "schema_version": "1.0",
            "theme": chain.theme,
            "question": chain.question,
            "entity_key": chain.entity_key,
            "created_at": chain.created_at,
            "nodes": nodes_d,
            "edges": edges_d,
            "alternatives": alts_d,
            "warnings": list(chain.warnings),
            "evaluate": chain.evaluate(),
        }


# ============================================================================
# 工具
# ============================================================================

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
