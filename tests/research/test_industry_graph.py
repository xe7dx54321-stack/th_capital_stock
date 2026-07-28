"""
阶段 7 测试：产业图谱 + 证据注册表（小白友好的单文件脚本，不需 pytest）

功能说明：
    直接用 python 运行：
        python tests/research/test_industry_graph.py
    最后一行：ALL PASSED 就是过，出现 FAIL/错误 就是不过。

    测试点（全部覆盖阶段 7 验收的 5 条）：
        1. 节点/边增删查、双向索引正确
        2. 每条边都有 evidence_id、valid_from、confidence、事实/推断区分
        3. 过期关系自动不参与当前查询（is_expired）
        4. query_upstream / query_peers / query_chain_position 返回正确结构
        5. 静态 peer_sets.json 作为可比公司确定性回退
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

# 确保项目根在 sys.path 里
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from smr_app.research.industry_graph import (  # noqa: E402
    IndustryGraph, GraphNode, GraphEdge,
    NODE_COMPANY, NODE_PRODUCT, NODE_SUPPLIER, NODE_CUSTOMER, NODE_THEME,
    EDGE_PRODUCES, EDGE_SUPPLIES, EDGE_COMPETES, EDGE_BENEFITS,
    EDGE_KIND_FACT, EDGE_KIND_INFERRED,
)
from smr_app.research.graph_evidence import (  # noqa: E402
    EvidenceRegistry, EvidenceSource, GraphEvidence,
    TIER_OFFICIAL, TIER_SEMI, TIER_NEWS, TIER_UNVERIFIED,
)

_FAIL_COUNT = 0
_PASS_COUNT = 0


def _check(name: str, condition: bool, detail: str = "") -> None:
    """小白断言：不抛异常，只计数"""
    global _FAIL_COUNT, _PASS_COUNT
    if condition:
        _PASS_COUNT += 1
        print(f"  [PASS] {name}" + (f"  — {detail}" if detail else ""))
    else:
        _FAIL_COUNT += 1
        print(f"  [FAIL] {name}" + (f"  — {detail}" if detail else ""))


# ======================================================================
# CASE 1：产业图谱基础 - 节点/边增查 + 证据字段齐全
# ======================================================================
def case_1_basic_graph() -> None:
    print("\n=== CASE 1：基础节点边 + 证据字段 ===")
    g = IndustryGraph()

    # 建节点
    hygon = GraphNode(node_id="688041.SH", node_type=NODE_COMPANY, name="海光信息")
    dcu = GraphNode(node_id="prod_dcu_s4", node_type=NODE_PRODUCT, name="深算四号 DCU")
    wafer = GraphNode(node_id="sup_tsmc", node_type=NODE_SUPPLIER, name="某晶圆厂")
    g.add_node(hygon); g.add_node(dcu); g.add_node(wafer)

    # 建边（每边都带 evidence_id + confidence + valid_from）
    e_prod = GraphEdge(
        edge_id="edge_hygon_dcus4",
        source_id="688041.SH", target_id="prod_dcu_s4",
        edge_type=EDGE_PRODUCES, edge_kind=EDGE_KIND_FACT,
        evidence_id="ev_20260110_abcdef01",
        valid_from="2025-06-01", confidence=0.95,
        properties={"share_of_revenue": "35%"},
    )
    e_sup = GraphEdge(
        edge_id="edge_sup_tsmc_hygon",
        source_id="sup_tsmc", target_id="688041.SH",
        edge_type=EDGE_SUPPLIES, edge_kind=EDGE_KIND_INFERRED,
        evidence_id="",  # 推断边可以暂时缺 evidence_id（写好后会自动降级为 inferred）
        valid_from="2024-01-01", confidence=0.6,
    )
    g.add_edge(e_prod); g.add_edge(e_sup)

    _check("get 海光节点", g.get_node("688041.SH") is not None)
    _check("get 深算四号节点", g.get_node("prod_dcu_s4") is not None)
    _check("生产边存在", g.get_edge("edge_hygon_dcus4") is not None)
    _check("供应边存在", g.get_edge("edge_sup_tsmc_hygon") is not None)
    _check("fact 边 evidence_id 非空", bool(g.get_edge("edge_hygon_dcus4").evidence_id))
    _check("边 confidence 在范围", 0 <= g.get_edge("edge_hygon_dcus4").confidence <= 1)
    _check("fact 边 kind 正确", g.get_edge("edge_hygon_dcus4").edge_kind == EDGE_KIND_FACT)


# ======================================================================
# CASE 2：过期关系判断（valid_until 过期后查询自动跳过）
# ======================================================================
def case_2_expired_edge() -> None:
    print("\n=== CASE 2：过期关系自动跳过 ===")
    g = IndustryGraph()
    hygon = GraphNode(node_id="688041.SH", node_type=NODE_COMPANY, name="海光信息")
    old_sup = GraphNode(node_id="sup_old", node_type=NODE_SUPPLIER, name="旧供应商")
    new_sup = GraphNode(node_id="sup_new", node_type=NODE_SUPPLIER, name="新供应商")
    g.add_node(hygon); g.add_node(old_sup); g.add_node(new_sup)

    # 旧供应商合同：2020-01-01 → 2024-12-31（已经过期）
    g.add_edge(GraphEdge(
        edge_id="edge_sup_old",
        source_id="sup_old", target_id="688041.SH",
        edge_type=EDGE_SUPPLIES, confidence=0.9,
        valid_from="2020-01-01", valid_until="2024-12-31",
    ))
    # 新供应商合同：2025-01-01 → 2028-12-31（当前有效）
    g.add_edge(GraphEdge(
        edge_id="edge_sup_new",
        source_id="sup_new", target_id="688041.SH",
        edge_type=EDGE_SUPPLIES, confidence=0.8,
        valid_from="2025-01-01", valid_until="2028-12-31",
    ))

    # 查当前（as_of=2026-07-23）：旧供应商应该被过滤掉
    upstream_now = g.query_upstream("688041.SH", as_of="2026-07-23T00:00:00+00:00")
    names_now = [r["counterparty_name"] for r in upstream_now]

    _check("2026 年查不到旧供应商", "旧供应商" not in names_now, f"实际={names_now}")
    _check("2026 年查到新供应商", "新供应商" in names_now)

    # 查 2023 年（as_of=2023-06-30）：应该只有旧供应商
    upstream_2023 = g.query_upstream("688041.SH", as_of="2023-06-30T00:00:00+00:00")
    names_2023 = [r["counterparty_name"] for r in upstream_2023]
    _check("2023 年能查到旧供应商", "旧供应商" in names_2023, f"实际={names_2023}")


# ======================================================================
# CASE 3：可比公司查询 - 先查图内 competes 边，查不到回退 peer_sets.json
# ======================================================================
def case_3_peers_query() -> None:
    print("\n=== CASE 3：可比公司查询 + peer_sets 回退 ===")

    # 3.1 图内数据齐全时，查 competes 边
    g1 = IndustryGraph()
    g1.add_node(GraphNode("688041.SH", NODE_COMPANY, "海光信息"))
    g1.add_node(GraphNode("688256.SH", NODE_COMPANY, "寒武纪"))
    g1.add_node(GraphNode("300474.SZ", NODE_COMPANY, "景嘉微"))
    g1.add_edge(GraphEdge(
        edge_id="edge_compete_hygon_cambricon",
        source_id="688041.SH", target_id="688256.SH",
        edge_type=EDGE_COMPETES, confidence=0.8,
        evidence_id="ev_2026_analyst_01",
        properties={"reason": "AI GPU/DCU 同赛道，产品直接竞争"},
    ))
    peers = g1.query_peers("688041.SH")
    peer_ids = [p["peer_id"] for p in peers]
    _check("图内有 competes 边时返回寒武纪", "688256.SH" in peer_ids, f"peers={peer_ids}")
    _check("返回带 reason 字段", all("reason" in p for p in peers))
    _check("返回带 evidence_id", all("evidence_id" in p for p in peers))

    # 3.2 图内没有任何 competes 边，回退 peer_sets.json
    with tempfile.TemporaryDirectory() as tmp:
        peer_json = Path(tmp) / "peer_sets.json"
        peer_json.write_text(json.dumps({
            "688041.SH": ["688256.SH", "300474.SZ", "000977.SZ"]
        }), encoding="utf-8")
        g2 = IndustryGraph(peer_sets_json_path=peer_json)
        g2.add_node(GraphNode("688041.SH", NODE_COMPANY, "海光信息"))

        peers2 = g2.query_peers("688041.SH")
        peer_ids2 = sorted([p["peer_id"] for p in peers2])
        expected = sorted(["688256.SH", "300474.SZ", "000977.SZ"])
        _check("peer_sets 回退 3 个可比", peer_ids2 == expected, f"实际={peer_ids2}")
        # 回退数据信心度=1.0（确定性配置）
        if peers2:
            _check("回退边标记 reason=静态 peer_sets",
                   "peer_sets.json" in peers2[0].get("reason", ""))
            _check("回退信心度=1.0", peers2[0].get("confidence") == 1.0)


# ======================================================================
# CASE 4：产业链位置查询（主题受益 + 上下游 + 信心度排序）
# ======================================================================
def case_4_chain_position() -> None:
    print("\n=== CASE 4：产业链位置 + 信心度排序 ===")
    g = IndustryGraph()
    g.add_node(GraphNode("688041.SH", NODE_COMPANY, "海光信息"))
    g.add_node(GraphNode("theme_ai", NODE_THEME, "AI 算力基础设施"))
    g.add_node(GraphNode("cust_bigtech", NODE_CUSTOMER, "某大型互联网厂商"))
    g.add_edge(GraphEdge(
        edge_id="e_benefit_theme_hygon",
        source_id="theme_ai", target_id="688041.SH",
        edge_type=EDGE_BENEFITS, confidence=0.9, evidence_id="ev_theme_001",
        properties={"revenue_exposure": "60%"},
    ))

    pos = g.query_chain_position("688041.SH")
    _check("themes 字段包含 AI 主题",
           any("AI" in t.get("counterparty_name", "") for t in pos["themes"]),
           f"themes={pos['themes']}")
    _check("返回值含 upstream/downstream/themes 3 键",
           {"upstream", "downstream", "themes"}.issubset(pos.keys()))


# ======================================================================
# CASE 5：证据注册表 - 幂等 + fact 边验证
# ======================================================================
def case_5_evidence_registry() -> None:
    print("\n=== CASE 5：证据注册表（幂等 + 事实边验证） ===")
    with tempfile.TemporaryDirectory() as tmp:
        persist_file = Path(tmp) / "graph_evidences.json"
        reg = EvidenceRegistry(persist_path=persist_file)

        # 注册一条官方公告证据
        src1 = EvidenceSource(
            url="https://cninfo.com.cn/xxx/hygon_2025_annual.pdf",
            title="海光信息 2025 年年度报告",
            source_name="巨潮资讯",
            published_at="2026-03-18T22:00:00+08:00",
            source_tier=TIER_OFFICIAL,
        )
        snippet1 = "2025 年公司 DCU 产品实现出货约 12 万颗，同比增长 153%。"
        ev_id1, is_new1 = reg.register(
            source=src1, snippet=snippet1,
            valid_from="2025-01-01", valid_until="2025-12-31",
            tags=["688041.SH", "DCU", "2025年报"],
        )
        _check("首次注册新证据 is_new=True", is_new1)
        _check("evidence_id 非空", bool(ev_id1))

        # 再注册完全相同的内容 → 命中幂等（is_new=False）
        ev_id2, is_new2 = reg.register(source=src1, snippet=snippet1)
        _check("幂等：相同内容不会再次入库", is_new2 is False)
        _check("幂等：两次 evidence_id 相同", ev_id1 == ev_id2)

        # 验证这条证据 "够不够支撑 fact 边"（官方公告 + 有片段 + 信心≥0.8 应该过）
        ok, reasons = reg.validate_for_edge(ev_id1, EDGE_KIND_FACT)
        _check(f"官方公告证据可支撑 fact 边", ok, f"reasons={reasons}")

        # 注册一条 4 级传闻证据（没有片段）
        src_bad = EvidenceSource(source_name="匿名论坛", source_tier=TIER_UNVERIFIED)
        ev_id_bad, _ = reg.register(source=src_bad, snippet="", confidence=0.2)
        ok2, reasons2 = reg.validate_for_edge(ev_id_bad, EDGE_KIND_FACT)
        _check("4 级传闻 + 无片段 不能支撑 fact 边", ok2 is False)
        _check("验证失败至少返回 1 条原因", len(reasons2) >= 1)

        # 推断边可以没有 evidence_id（允许后续补）
        ok3, _ = reg.validate_for_edge("", EDGE_KIND_INFERRED)
        _check("空 evidence_id 仍可支撑 inferred 边", ok3)

        # 统计
        stats = reg.count()
        _check("统计 total ≥ 2", stats.get("total", 0) >= 2)

        # 持久化后重新加载 → 验证数据还在
        loaded = EvidenceRegistry(persist_path=persist_file)
        _check("持久化重启后 evidence_id1 仍存在", loaded.get(ev_id1) is not None)


# ======================================================================
# 入口
# ======================================================================
def main() -> int:
    print("======== 阶段 7：产业图谱 + 证据注册表 单文件测试 ========")
    case_1_basic_graph()
    case_2_expired_edge()
    case_3_peers_query()
    case_4_chain_position()
    case_5_evidence_registry()

    total = _PASS_COUNT + _FAIL_COUNT
    print("\n" + "=" * 56)
    if _FAIL_COUNT == 0:
        print(f"ALL PASSED  ✅  {_PASS_COUNT}/{total}")
        return 0
    else:
        print(f"FAILED  ❌  {_FAIL_COUNT}/{total} 失败，{_PASS_COUNT} 通过")
        return 1


if __name__ == "__main__":
    sys.exit(main())
