"""
产业图谱（Industry Graph）- 动态产业关系知识库

功能说明：
    阶段 7「产业图谱与前瞻数据增强」的核心数据结构模块。
    解决：主题预期差和因果研究只靠静态 peer_sets.json 不够用的问题。
    把公司、产品、技术、客户、供应商、工厂、认证、订单、主题等
    作为节点，把"生产/供应/采购/持股/竞争/认证/替代/受益/约束/领先"
    作为边，建成一张动态的产业关系网。

    核心原则（master plan 阶段 7 验收）：
    1. 每条高判断关系必须带 evidence_id、valid_from、confidence
    2. 推断边（inferred）和正式事实边（fact）必须明确区分
    3. 过期关系（valid_until < 今天）不参与当前结论
    4. 查询可以回答：公司的产业链位置、关键上下游、为什么 A 是 B 的可比
    5. 静态 peer_sets.json 仍可作为"纯确定性回退"（graph 没数据时）

参数说明：
    GraphNode         - 图谱节点（id / 类型 / 名称 / 属性字典）
    GraphEdge         - 图谱边（源节点 → 目标节点 + 边类型 + 证据 + 有效期 + 信心）
    IndustryGraph     - 图谱实例：增/删/查节点、增边、查询上下游、找可比、回退 peer_sets

返回值说明：
    - IndustryGraph.query_upstream(公司) → 关键供应商/客户/约束
    - IndustryGraph.query_peers(公司)   → 可比公司 + 选择原因
    - IndustryGraph.is_expired(边)      → True/False（判断过期）
    - 所有查询永远返回 list/dict，从不抛异常（缺数据返回空）

异常处理：
    - 任意参数错 / 节点不存在 → 降级（返回空列表/None），不会让工作流崩
    - 证据 ID 缺失仅在非 fact 边允许（fact 边必须有 evidence）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional
import json


# ============================================================================
# 节点类型常量（小白：这 11 种就是图谱里所有的"点"）
# ============================================================================

NODE_COMPANY = "company"          # 公司（例：海光信息 688041.SH）
NODE_PRODUCT = "product"          # 产品（例：深算四号 DCU）
NODE_TECH = "tech"                # 技术（例：CoWoS 封装）
NODE_CUSTOMER = "customer"        # 客户（例：某AI大模型厂商）
NODE_SUPPLIER = "supplier"        # 供应商（例：某晶圆厂）
NODE_SYSTEM_INTEGRATOR = "si"     # 系统商（例：某服务器厂商）
NODE_END_DEMAND = "demand"        # 终端需求（例：AI训练算力）
NODE_FACTORY = "factory"          # 工厂（例：海光成都封测厂）
NODE_CERT = "cert"                # 认证（例：800G 相干认证）
NODE_ORDER = "order"              # 订单（例：某运营商批量订单）
NODE_THEME = "theme"              # 行业主题（例：AI 算力基础设施）

NODE_LABELS = {
    NODE_COMPANY: "公司",
    NODE_PRODUCT: "产品",
    NODE_TECH: "技术",
    NODE_CUSTOMER: "客户",
    NODE_SUPPLIER: "供应商",
    NODE_SYSTEM_INTEGRATOR: "系统商",
    NODE_END_DEMAND: "终端需求",
    NODE_FACTORY: "工厂",
    NODE_CERT: "认证",
    NODE_ORDER: "订单",
    NODE_THEME: "行业主题",
}

VALID_NODE_TYPES = frozenset(NODE_LABELS.keys())


# ============================================================================
# 边类型常量（小白：这 10 种就是图谱里所有的"连线"）
# ============================================================================

EDGE_PRODUCES = "produces"         # 生产：公司 → 产品（海光 → 深算四号）
EDGE_SUPPLIES = "supplies"         # 供应：供应商 → 公司（晶圆厂 → 海光）
EDGE_PURCHASES = "purchases"       # 采购：公司 → 供应商（反向 supplies）
EDGE_HOLDS = "holds"               # 持股：公司 → 公司（星网锐捷 → 锐捷网络）
EDGE_COMPETES = "competes"         # 竞争：公司 ↔ 公司（海光 ↔ 寒武纪）
EDGE_CERTIFIED = "certified"       # 认证：产品 ← 认证（深算四号 ← PCIe 认证）
EDGE_SUBSTITUTES = "substitutes"   # 替代：产品 ↔ 产品（DCU ↔ GPU）
EDGE_BENEFITS = "benefits"         # 受益：主题 → 公司（AI算力 → 海光）
EDGE_CONSTRAINS = "constrains"     # 约束：供应商/政策 → 公司（出口管制 → 海光）
EDGE_LEADS = "leads"               # 领先指标：订单/认证 → 收入（首批订单 → Q4 收入）

EDGE_LABELS = {
    EDGE_PRODUCES: "生产",
    EDGE_SUPPLIES: "供应",
    EDGE_PURCHASES: "采购",
    EDGE_HOLDS: "持股",
    EDGE_COMPETES: "竞争",
    EDGE_CERTIFIED: "认证通过",
    EDGE_SUBSTITUTES: "替代",
    EDGE_BENEFITS: "受益于",
    EDGE_CONSTRAINS: "受约束于",
    EDGE_LEADS: "是…的领先指标",
}

VALID_EDGE_TYPES = frozenset(EDGE_LABELS.keys())

# 边类型方向性：是否允许反向查找时自动生成反向边
EDGE_AUTO_REVERSE = {
    EDGE_SUPPLIES: EDGE_PURCHASES,   # 供应 ↔ 采购
    EDGE_PURCHASES: EDGE_SUPPLIES,
}


# ============================================================================
# 边的确定性分类：fact（硬事实） vs inferred（推断）
# ============================================================================

EDGE_KIND_FACT = "fact"          # 事实边：有公告/官网/权威源支撑
EDGE_KIND_INFERRED = "inferred"  # 推断边：分析师/研究员逻辑推导

VALID_EDGE_KINDS = frozenset({EDGE_KIND_FACT, EDGE_KIND_INFERRED})


# ============================================================================
# 数据结构
# ============================================================================

@dataclass
class GraphNode:
    """
    图谱节点

    小白讲解：
        图谱上的每一个"点"就是一个节点。
        例如"海光信息"是一个 company 节点，"深算四号"是一个 product 节点。
        properties 是附加信息（比如公司节点可以加市值、PE 等）。
    """
    node_id: str                 # 全局唯一 ID（例：688041.SH、产品_dcu_shengsuan4）
    node_type: str               # 节点类型（见上面 11 种 VALID_NODE_TYPES）
    name: str                    # 显示名（例："海光信息"）
    properties: dict = field(default_factory=dict)  # 自定义属性字典
    created_at: str = ""         # 创建时间 ISO（自动填）
    updated_at: str = ""         # 更新时间 ISO（自动填）

    def __post_init__(self):
        """创建后自动校验类型 + 补时间戳（小白：这是 dataclass 的初始化钩子）"""
        if self.node_type not in VALID_NODE_TYPES:
            # 不抛异常，降级为通用节点（保证工作流不崩）
            self.node_type = NODE_COMPANY
        now = _utc_now_iso()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now


@dataclass
class GraphEdge:
    """
    图谱边（节点之间的关系）

    小白讲解：
        图谱上"点和点之间的连线"就是边。
        例如边 (海光, produces, 深算四号) 表示"海光生产深算四号"。

        关键：
        - evidence_id：这条关系从哪儿来的（ArtifactStore 里的证据文件 ID），
          fact 边必须有，inferred 边可以没
        - valid_from / valid_until：有效期（例：某供应商合同 2025-01-01 生效
          2026-12-31 到期，到期后就不算了）
        - confidence：0~1 的信心度（fact=1.0，推断通常 0.5~0.8）
        - edge_kind：fact vs inferred
    """
    edge_id: str                 # 全局唯一 ID（例：edge_hygon_produces_dcus4）
    source_id: str               # 源节点 ID
    target_id: str               # 目标节点 ID
    edge_type: str               # 边类型（见上面 10 种 VALID_EDGE_TYPES）
    edge_kind: str = EDGE_KIND_INFERRED  # fact / inferred
    evidence_id: str = ""        # 证据 ID（fact 边必填）
    valid_from: str = ""         # 生效开始 ISO 日期（空=永久前）
    valid_until: str = ""        # 生效结束 ISO 日期（空=永久后）
    confidence: float = 0.6      # 信心度 0~1
    properties: dict = field(default_factory=dict)  # 附加属性（例：持股比例）
    created_at: str = ""         # 创建时间
    updated_at: str = ""         # 更新时间

    def __post_init__(self):
        """初始化校验 + 补时间"""
        if self.edge_type not in VALID_EDGE_TYPES:
            # 降级：不认识的边当受益处理（不崩）
            self.edge_type = EDGE_BENEFITS
        if self.edge_kind not in VALID_EDGE_KINDS:
            self.edge_kind = EDGE_KIND_INFERRED
        # fact 边必须有 evidence_id，缺失的话降级为 inferred
        if self.edge_kind == EDGE_KIND_FACT and not self.evidence_id:
            self.edge_kind = EDGE_KIND_INFERRED
        # 信心度夹在 0~1
        self.confidence = max(0.0, min(1.0, float(self.confidence)))
        now = _utc_now_iso()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now


class IndustryGraph:
    """
    产业图谱实例

    小白讲解：
        这就是一张完整的"产业关系网地图"。
        你可以往里面加节点（公司/产品）、加边（生产/供应/竞争），
        也可以从里面查"某公司的上游供应商是谁"、"和它竞争的有哪些公司"。
    """

    def __init__(self, peer_sets_json_path: Optional[str | Path] = None):
        """
        初始化图谱

        参数:
            peer_sets_json_path: 静态 peer_sets.json 的路径（回退方案）。
                当图谱里查不到可比公司时，从这个 JSON 里读确定性回退。
        """
        self._nodes: dict[str, GraphNode] = {}
        self._edges: dict[str, GraphEdge] = {}
        # 索引：source_id → [edges]  和  target_id → [edges]（加速查询）
        self._out_edges: dict[str, list[str]] = {}
        self._in_edges: dict[str, list[str]] = {}
        # 静态可比公司回退
        self._peer_sets_fallback: dict[str, list[str]] = {}
        if peer_sets_json_path:
            self._load_peer_sets_fallback(Path(peer_sets_json_path))

    # ------------------------------------------------------------------
    # 节点操作
    # ------------------------------------------------------------------

    def add_node(self, node: GraphNode) -> GraphNode:
        """
        添加/更新节点

        参数:
            node: GraphNode 实例

        返回:
            实际存入的 GraphNode（ID 冲突会合并属性）
        """
        existing = self._nodes.get(node.node_id)
        if existing is None:
            self._nodes[node.node_id] = node
            self._out_edges.setdefault(node.node_id, [])
            self._in_edges.setdefault(node.node_id, [])
        else:
            # 合并属性（新的覆盖旧的），更新时间戳
            merged_props = {**existing.properties, **node.properties}
            existing.properties = merged_props
            existing.name = node.name or existing.name
            existing.node_type = node.node_type or existing.node_type
            existing.updated_at = _utc_now_iso()
            self._nodes[node.node_id] = existing
        return self._nodes[node.node_id]

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """按 ID 查节点，不存在返回 None"""
        return self._nodes.get(node_id)

    def list_nodes_by_type(self, node_type: str) -> list[GraphNode]:
        """
        列出某一类型的所有节点（例：列出所有 company 节点）

        参数:
            node_type: 节点类型常量（如 NODE_COMPANY）

        返回:
            该类型的节点列表（空列表表示没有）
        """
        return [n for n in self._nodes.values() if n.node_type == node_type]

    # ------------------------------------------------------------------
    # 边操作
    # ------------------------------------------------------------------

    def add_edge(self, edge: GraphEdge) -> GraphEdge:
        """
        添加/更新边

        小白讲解：
            加边之前会检查源和目标节点是否存在，不存在就自动创建一个
            "占位节点"（保证图谱始终是自洽的，不会有"悬空边"）。
        """
        # 先确保两端节点存在（不存在就占位）
        for nid in (edge.source_id, edge.target_id):
            if nid not in self._nodes:
                self.add_node(GraphNode(
                    node_id=nid, node_type=NODE_COMPANY, name=nid,
                    properties={"__placeholder__": True},
                ))
        existing = self._edges.get(edge.edge_id)
        if existing is None:
            self._edges[edge.edge_id] = edge
            self._out_edges.setdefault(edge.source_id, []).append(edge.edge_id)
            self._in_edges.setdefault(edge.target_id, []).append(edge.edge_id)
        else:
            # 合并属性 + 更新时间
            merged_props = {**existing.properties, **edge.properties}
            existing.properties = merged_props
            existing.edge_type = edge.edge_type or existing.edge_type
            existing.edge_kind = edge.edge_kind or existing.edge_kind
            existing.evidence_id = edge.evidence_id or existing.evidence_id
            existing.valid_from = edge.valid_from or existing.valid_from
            existing.valid_until = edge.valid_until or existing.valid_until
            existing.confidence = edge.confidence
            existing.updated_at = _utc_now_iso()
            self._edges[edge.edge_id] = existing
        return self._edges[edge.edge_id]

    def get_edge(self, edge_id: str) -> Optional[GraphEdge]:
        return self._edges.get(edge_id)

    # ------------------------------------------------------------------
    # 有效期判断（核心：过期边不参与当前结论）
    # ------------------------------------------------------------------

    def is_expired(self, edge: GraphEdge, as_of: Optional[str] = None) -> bool:
        """
        判断一条边是否已过期

        小白讲解：
            valid_until < as_of 就过期；valid_from > as_of 还没生效也算过期。
            不传 as_of 就用当前 UTC 时间。

        参数:
            edge: 要检查的边
            as_of: 基准 ISO 时间（空=现在）

        返回:
            True=过期/未生效（不应该用于当前结论）
        """
        now = as_of or _utc_now_iso()
        if edge.valid_until and now[:10] > edge.valid_until[:10]:
            return True
        if edge.valid_from and now[:10] < edge.valid_from[:10]:
            return True
        return False

    def _active_edges(self, edge_ids: list[str], as_of: Optional[str] = None) -> list[GraphEdge]:
        """从 ID 列表中过滤出当前有效（没过期）的边"""
        result = []
        for eid in edge_ids:
            edge = self._edges.get(eid)
            if edge is None:
                continue
            if self.is_expired(edge, as_of):
                continue
            result.append(edge)
        return result

    # ------------------------------------------------------------------
    # 图谱查询（工作流真正会用到的）
    # ------------------------------------------------------------------

    def query_upstream(self, company_id: str, as_of: Optional[str] = None) -> list[dict]:
        """
        查询一家公司的上游（供应商/约束/技术/工厂…）

        小白讲解：
            输入"海光"，返回：它的晶圆供应商是谁？受什么出口管制约束？
            工厂在哪里？每条结果都带关系类型和信心度。

        参数:
            company_id: 公司节点 ID（如 688041.SH）
            as_of: 基准时间（空=现在）

        返回:
            列表，每个元素是 {relation, target, target_type, confidence, evidence_id}
        """
        out_ids = self._out_edges.get(company_id, [])
        in_ids = self._in_edges.get(company_id, [])
        active_out = self._active_edges(out_ids, as_of)
        active_in = self._active_edges(in_ids, as_of)

        results: list[dict] = []
        # 出边：公司 → X（例：公司采购自 供应商）
        for edge in active_out:
            target = self._nodes.get(edge.target_id)
            if target is None:
                continue
            results.append(self._format_query_result(
                edge=edge,
                counterparty_name=target.name,
                counterparty_id=target.node_id,
                counterparty_type=target.node_type,
            ))
        # 入边：X → 公司（例：供应商 供应给 公司）
        for edge in active_in:
            source = self._nodes.get(edge.source_id)
            if source is None:
                continue
            results.append(self._format_query_result(
                edge=edge,
                counterparty_name=source.name,
                counterparty_id=source.node_id,
                counterparty_type=source.node_type,
                reverse=True,
            ))
        # 按信心度降序排
        results.sort(key=lambda r: r.get("confidence", 0), reverse=True)
        return results

    def query_peers(
        self,
        company_id: str,
        min_confidence: float = 0.4,
        as_of: Optional[str] = None,
    ) -> list[dict]:
        """
        查询一家公司的可比公司（竞争/同产品/同主题）

        小白讲解：
            优先从图谱里找 competes 边；找不到就从静态 peer_sets.json 回退。
            返回时附带"选择原因"（小白能看懂为什么把 A 和 B 放在一起比）。

        参数:
            company_id: 公司节点 ID
            min_confidence: 只返回 ≥ 该信心度的结果（默认 0.4）
            as_of: 基准时间

        返回:
            列表，每个元素是 {peer_id, peer_name, reason, confidence, evidence_id}
        """
        peers: list[dict] = []
        seen: set[str] = set()

        # 图内查询：competes 边（双向都查）
        out_ids = self._out_edges.get(company_id, [])
        in_ids = self._in_edges.get(company_id, [])
        for edge in self._active_edges(out_ids, as_of) + self._active_edges(in_ids, as_of):
            if edge.edge_type != EDGE_COMPETES:
                continue
            if edge.confidence < min_confidence:
                continue
            # 找出另一端的公司 ID
            other_id = edge.target_id if edge.source_id == company_id else edge.source_id
            if other_id == company_id or other_id in seen:
                continue
            other = self._nodes.get(other_id)
            if other is None:
                continue
            seen.add(other_id)
            peers.append({
                "peer_id": other_id,
                "peer_name": other.name,
                "reason": f"图谱竞争边（{edge.edge_id}）：{edge.properties.get('reason', '同赛道业务重叠')}",
                "confidence": edge.confidence,
                "evidence_id": edge.evidence_id or "",
                "edge_kind": edge.edge_kind,
            })

        # 如果图谱没结果，用静态 peer_sets.json 回退
        if not peers:
            fallback_list = self._peer_sets_fallback.get(company_id, [])
            for peer_id in fallback_list:
                if peer_id == company_id or peer_id in seen:
                    continue
                seen.add(peer_id)
                peers.append({
                    "peer_id": peer_id,
                    "peer_name": peer_id,
                    "reason": "静态 peer_sets.json 确定性回退（图谱暂无竞争边数据）",
                    "confidence": 1.0,  # 静态数据视为硬配置
                    "evidence_id": "peer_sets.json",
                    "edge_kind": EDGE_KIND_FACT,
                })

        peers.sort(key=lambda r: r.get("confidence", 0), reverse=True)
        return peers

    def query_chain_position(self, company_id: str, as_of: Optional[str] = None) -> dict:
        """
        回答：这家公司在产业链什么位置？关键上下游是谁？

        返回:
            {"upstream": [...], "downstream": [...], "themes": [...]}
            每个子结构和 query_upstream 返回格式一致
        """
        all_rels = self.query_upstream(company_id, as_of)
        upstream = []
        downstream = []
        themes = []
        for rel in all_rels:
            rel_type = rel.get("relation_code", "")
            counterparty_t = rel.get("counterparty_type", "")
            if rel_type in (EDGE_SUPPLIES, EDGE_PURCHASES) and counterparty_t in (NODE_SUPPLIER, NODE_TECH, NODE_FACTORY):
                upstream.append(rel)
            elif counterparty_t == NODE_CUSTOMER or counterparty_t == NODE_SYSTEM_INTEGRATOR:
                downstream.append(rel)
            elif counterparty_t == NODE_THEME:
                themes.append(rel)
        return {
            "company_id": company_id,
            "upstream": upstream,
            "downstream": downstream,
            "themes": themes,
            "as_of": as_of or _utc_now_iso(),
        }

    # ------------------------------------------------------------------
    # 导入 / 导出（方便持久化到 JSON）
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """把整个图谱转成可 JSON 序列化的字典"""
        return {
            "schema_version": "1.0",
            "generated_at": _utc_now_iso(),
            "nodes": [
                {
                    "node_id": n.node_id,
                    "node_type": n.node_type,
                    "name": n.name,
                    "properties": n.properties,
                    "created_at": n.created_at,
                    "updated_at": n.updated_at,
                }
                for n in self._nodes.values()
            ],
            "edges": [
                {
                    "edge_id": e.edge_id,
                    "source_id": e.source_id,
                    "target_id": e.target_id,
                    "edge_type": e.edge_type,
                    "edge_kind": e.edge_kind,
                    "evidence_id": e.evidence_id,
                    "valid_from": e.valid_from,
                    "valid_until": e.valid_until,
                    "confidence": e.confidence,
                    "properties": e.properties,
                    "created_at": e.created_at,
                    "updated_at": e.updated_at,
                }
                for e in self._edges.values()
            ],
            "peer_sets_fallback": self._peer_sets_fallback,
        }

    def load_dict(self, data: dict) -> "IndustryGraph":
        """从字典里恢复图谱数据（to_dict 的逆操作）"""
        for nd in data.get("nodes", []):
            self.add_node(GraphNode(
                node_id=nd.get("node_id", ""),
                node_type=nd.get("node_type", NODE_COMPANY),
                name=nd.get("name", nd.get("node_id", "")),
                properties=nd.get("properties", {}),
                created_at=nd.get("created_at", ""),
                updated_at=nd.get("updated_at", ""),
            ))
        for ed in data.get("edges", []):
            self.add_edge(GraphEdge(
                edge_id=ed.get("edge_id", ""),
                source_id=ed.get("source_id", ""),
                target_id=ed.get("target_id", ""),
                edge_type=ed.get("edge_type", EDGE_BENEFITS),
                edge_kind=ed.get("edge_kind", EDGE_KIND_INFERRED),
                evidence_id=ed.get("evidence_id", ""),
                valid_from=ed.get("valid_from", ""),
                valid_until=ed.get("valid_until", ""),
                confidence=float(ed.get("confidence", 0.6)),
                properties=ed.get("properties", {}),
                created_at=ed.get("created_at", ""),
                updated_at=ed.get("updated_at", ""),
            ))
        if data.get("peer_sets_fallback"):
            self._peer_sets_fallback = dict(data["peer_sets_fallback"])
        return self

    # ------------------------------------------------------------------
    # 内部辅助
    # ------------------------------------------------------------------

    def _load_peer_sets_fallback(self, path: Path) -> None:
        """从 peer_sets.json 加载静态可比公司（作为确定性回退）"""
        try:
            if not path.is_file():
                return
            raw = json.loads(path.read_text(encoding="utf-8"))
            # 兼容两种结构：{"code_A": ["code_B", ...]} 或 {"peer_sets": {...}}
            if isinstance(raw, dict) and "peer_sets" in raw:
                raw = raw["peer_sets"]
            if isinstance(raw, dict):
                for key, peers in raw.items():
                    if isinstance(peers, list):
                        self._peer_sets_fallback[str(key)] = [str(p) for p in peers]
        except (json.JSONDecodeError, OSError):
            # 解析失败不抛，保持空回退表
            self._peer_sets_fallback = {}

    @staticmethod
    def _format_query_result(
        *,
        edge: GraphEdge,
        counterparty_name: str,
        counterparty_id: str,
        counterparty_type: str,
        reverse: bool = False,
    ) -> dict:
        """把一条边格式化成统一的查询返回结构"""
        rel_code = edge.edge_type
        if reverse and edge.edge_type in EDGE_AUTO_REVERSE:
            rel_code = EDGE_AUTO_REVERSE[edge.edge_type]
        return {
            "relation_code": rel_code,
            "relation_label": EDGE_LABELS.get(edge.edge_type, edge.edge_type),
            "counterparty_id": counterparty_id,
            "counterparty_name": counterparty_name,
            "counterparty_type": counterparty_type,
            "counterparty_type_label": NODE_LABELS.get(counterparty_type, counterparty_type),
            "confidence": edge.confidence,
            "evidence_id": edge.evidence_id or "",
            "edge_kind": edge.edge_kind,
            "edge_id": edge.edge_id,
            "valid_from": edge.valid_from,
            "valid_until": edge.valid_until,
            "properties": dict(edge.properties),
        }


# ============================================================================
# 工具函数
# ============================================================================

def _utc_now_iso() -> str:
    """返回当前 UTC 时间的 ISO 字符串（精确到秒，不带微秒）"""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
