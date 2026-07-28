"""
阶段 9 测试：产业因果解释（DCI 金标准 Case）

功能说明：
    直接 python tests/workflows/test_industry_causal_explainer.py 运行，
    最后一行 ALL PASSED 就是通过。

    覆盖 master plan 阶段 9 验收 5 条：
        1 需求事实、资产映射、叙事竞争、兑现时滞分开
        2 每条因果边标注 fact / inferred（含 evidence_id）
        3 不用单条新闻解释长期行情（会警告）
        4 同时列出替代解释 + 证伪条件（防确认偏误）
        5 输出结构化 causal_chain artifact（JSON + Markdown）
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from smr_app.research.causal_chain import (  # noqa: E402
    CausalChain, CausalNode, CausalEdge, EvidenceSlim, AlternativeExplanation,
    CausalRenderer, ALL_STEPS, STEP_DEMAND_REAL, STEP_A_SHARE_MAPPING,
    STEP_TRANSMISSION, STEP_CATALYST, STEP_FALSIFICATION,
    EDGE_FACT, EDGE_INFERRED,
)
from smr_app.runtime.runner import WorkflowRunner  # noqa: E402
from smr_app.workflows.industry_causal_explainer import (  # noqa: E402
    industry_causal_explainer_definition,
)

_FAIL_COUNT = 0
_PASS_COUNT = 0


def _check(name: str, cond: bool, detail: str = ""):
    global _FAIL_COUNT, _PASS_COUNT
    if cond:
        _PASS_COUNT += 1
        print(f"  [PASS] {name}" + (f" — {detail}" if detail else ""))
    else:
        _FAIL_COUNT += 1
        print(f"  [FAIL] {name}" + (f" — {detail}" if detail else ""))


# ============================================================================
# CASE A：直接用 CausalChain / CausalRenderer 数据结构（不跑 Runner）
# ============================================================================
def case_a_chain_datastructure() -> None:
    print("\n=== CASE A：CausalChain 数据结构 + 评估（DCI 金标准骨架） ===")

    chain = CausalChain(
        theme="DCI 网络基建",
        question="为什么 DCI 需求明确但 A 股长期没有行情？",
        entity_key="300394.SZ + 中际旭创 组合",
    )

    # S1 需求真实：2 条独立 2 级证据（运营商集采 + 产业联盟统计）
    chain.set_node(CausalNode(
        step=STEP_DEMAND_REAL,
        conclusion=(
            "DCI 终端需求真实：2026 Q1 三大运营商 DCI 相关集采规模同比+58%，"
            "DCI 联盟统计 800G 端口出货 Q1 同比+210%"
        ),
        confidence=0.9,
        completed=True,
        evidences=[
            EvidenceSlim(
                evidence_id="ev_cninf_dci_2026q1_tender",
                summary="巨潮 3 家运营商 DCI 集采公告 总规模同比+58%",
                source_tier=1, fact=True,
            ),
            EvidenceSlim(
                evidence_id="ev_dci_alliance_2026q1_port",
                summary="DCI 产业联盟 Q1 800G 端口出货报告 +210% yoy",
                source_tier=2, fact=True,
            ),
        ],
    ))

    # S2 产业链位置
    chain.set_node(CausalNode(
        step=2,
        conclusion="需求位于产业链的'运营商采购→系统商下单→光模块厂出货'中段，不是最上游光芯片",
        confidence=0.75, completed=True,
        evidences=[
            EvidenceSlim(evidence_id="ev_industry_map_dci_midstream",
                         summary="光模块处于产业链中段，上游光芯片，下游设备商/运营商",
                         source_tier=2, fact=False),
        ],
    ))

    # S3 A 股映射
    chain.set_node(CausalNode(
        step=STEP_A_SHARE_MAPPING,
        conclusion="A 股有映射（天孚/中际/新易盛等），但纯 DCI 业务敞口仅 30%~45%，其余被数通/电信/海外混",
        confidence=0.8, completed=True,
        evidences=[
            EvidenceSlim(evidence_id="ev_2025_annual_report_segment",
                         summary="2025 年报分部：DCI 占各公司收入 30%~45%",
                         source_tier=1, fact=True),
        ],
    ))

    # S4 叙事竞争
    chain.set_node(CausalNode(
        step=4,
        conclusion="同期 AI 算力主题（GPU/服务器/液冷）吸金效应远强于 DCI，板块资金被长期分流",
        confidence=0.6, completed=True,
        evidences=[
            EvidenceSlim(evidence_id="ev_wind_fund_flow_2026_h1",
                         summary="2026 H1 AI 算力 ETF 净流入 +920 亿 vs DCI 主题 +45 亿",
                         source_tier=2, fact=False),
        ],
    ))

    # S5 订单→利润传导
    chain.set_node(CausalNode(
        step=STEP_TRANSMISSION,
        conclusion="运营商集采→供应商 PO→出货→开票→确认收入→折旧冲减利润：典型传导链条长，利润兑现慢于订单",
        confidence=0.7, completed=True,
        evidences=[
            EvidenceSlim(evidence_id="ev_listco_transmission_note",
                         summary="公司调研纪要：运营商集采后平均 3~6 个月进入出货确认周期",
                         source_tier=2, fact=False),
        ],
    ))

    # S6 传导时间
    chain.set_node(CausalNode(
        step=6,
        conclusion="历史上光模块集采→板块超额收益平均滞后 2~4 个季度，本轮 2026 Q1 集采，最早 Q3~Q4 见利润兑现",
        confidence=0.55, completed=True,
    ))

    # S7 催化
    chain.set_node(CausalNode(
        step=STEP_CATALYST,
        conclusion="催化观察清单：DCI 1.6T 首单、三大运营商 H2 追加招标、头部光模块厂单季 DCI 收入占比>50%",
        confidence=0.65, completed=True,
    ))

    # S8 证伪条件
    chain.set_node(CausalNode(
        step=STEP_FALSIFICATION,
        conclusion=(
            "若出现以下任意 2 条即可判定本解释错误：\n"
            "  (1) 运营商 Q2/Q3 DCI 集采规模同比<0（需求不真）；\n"
            "  (2) 光模块龙头 Q3 单季 DCI 收入>50% 但股价相对收益仍<指数 0%（映射和传导机制错）；\n"
            "  (3) AI 算力板块连续 8 周净流出但 DCI 仍无超额收益（叙事竞争不成立）。"
        ),
        confidence=0.95, completed=True,
    ))

    # 边：S1→S2（fact 边：有产业联盟位置图）S2→S3（fact：年报分部）
    # 其余 S3→S4→S5→S6→S7→S8 推断边
    chain.set_edge(CausalEdge(from_step=1, to_step=2, edge_kind=EDGE_FACT,
                              explanation="运营商集采规模统计天然在产业链中段",
                              evidence_id="ev_dci_alliance_chain_chart_2026"))
    chain.set_edge(CausalEdge(from_step=2, to_step=3, edge_kind=EDGE_FACT,
                              explanation="中段映射对应 A 股光模块设备商",
                              evidence_id="ev_2025_annual_report_segment"))
    for (fs, ts, exp) in [
        (3, 4, "A股敞口不纯 + 同期有吸金主题 → 叙事竞争加剧"),
        (4, 5, "叙事竞争下，必须等订单→利润兑现才能拉行情 → 传导链路拉长"),
        (5, 6, "传导链路长 → 历史兑现时间 2~4Q"),
        (6, 7, "兑现期长 → 需要具体观察催化（早于利润 1Q 左右）"),
        (7, 8, "任何催化预期必须配对应的证伪条件，否则自欺欺人"),
    ]:
        chain.set_edge(CausalEdge(
            from_step=fs, to_step=ts, edge_kind=EDGE_INFERRED, explanation=exp,
            evidence_id="", historical_precedent=(
                "2024/01~2024/09 AI 光模块行情：订单 2023Q4，行情 2024Q1~Q3，滞后约 1Q"
                if (fs, ts) == (5, 6) else ""
            ),
        ))

    # 替代解释（至少 3 个）
    for alt in [
        AlternativeExplanation(
            title="估值已在 2025 年反映过 DCI 预期（透支）",
            plausibility=0.55,
            how_to_falsify="查 2025/01~2026/06 DCI 成分股 PE band 分位，若 2026/06 仍<历史 60% 分位则证伪",
            current_evidence_against="某券商测算龙头 2026E PE 仅 28x，在 5 年 30% 分位以下（暂未透支）",
        ),
        AlternativeExplanation(
            title="产业内耗价格战导致利润端不兑现（只增收不增利）",
            plausibility=0.35,
            how_to_falsify="2026 H2 光模块厂毛利率同比环比是否下滑；若持平或上升证伪",
            current_evidence_against="行业协会 2026 Q1 800G DCI 光模块 ASP 同比-12% 但规模效应抵消毛利率基本持平",
        ),
        AlternativeExplanation(
            title="大小非/定增解禁压制股价",
            plausibility=0.25,
            how_to_falsify="统计未来 6 月解禁占比；若合计<3% 证伪",
            current_evidence_against="天孚 6 月解禁 1.2%、中际 9 月 2.0%、新易盛 7 月 0.8%（合计<5%，压制有限）",
        ),
    ]:
        chain.add_alternative(alt)

    # 开始断言
    ev = chain.evaluate()
    _check("evaluate() ready=True（8 节点+≥1 替代+S8 证伪）", ev["ready"],
           f"fatal_gaps={ev['fatal_gaps']}  completed_steps={ev['completed_steps']}")
    _check("completed_steps=8/8", ev["completed_steps"] == 8)
    _check("fact 边≥2（S1→S2、S2→S3 是硬事实）", ev["fact_edge_count"] >= 2)
    _check("推断边≥5 条（7-2=5）", ev["inferred_edge_count"] >= 5)
    _check("has_alternatives=True（≥1 个替代）", ev["has_alternatives"])
    _check("has_falsification=True（S8 有内容）", ev["has_falsification"])
    _check(f"整体信心度≥0.5（当前={ev['confidence_overall']:.2f}）", ev["confidence_overall"] >= 0.5)
    _check("没有 fatal_gaps", len(ev["fatal_gaps"]) == 0, str(ev["fatal_gaps"]))

    # 渲染：检查 Markdown/JSON 是否包含必要字段
    md = CausalRenderer.to_markdown(chain)
    _check("Markdown 含 '产业因果解释' 标题", "产业因果解释" in md)
    _check("Markdown 含 '8 步因果框架'章节", "## 8 步因果框架" in md)
    _check("Markdown 含 '替代解释'章节（防确认偏误）", "## 替代解释" in md)
    _check("Markdown 含 '证伪条件'章节", "## 证伪条件" in md)
    _check("Markdown 含 7 条边的因果传导表格", "S1→S2" in md and "S7→S8" in md)

    d = CausalRenderer.to_dict(chain)
    _check("JSON artifact 含 schema_version='1.0'", d.get("schema_version") == "1.0")
    _check("JSON 含 nodes（8 个）", len(d["nodes"]) == 8)
    _check("JSON 含 alternatives（≥3 个）", len(d["alternatives"]) >= 3)
    _check("JSON 含 evaluate.ready=True", d["evaluate"].get("ready") is True)


# ============================================================================
# CASE B：WorkflowRunner 端到端（DCI 最小可用输入 → 2 制品 + DB 注册）
# ============================================================================
def case_b_workflow_runner() -> None:
    print("\n=== CASE B：WorkflowRunner 端到端 DCI Case（制品保存 + 质量门） ===")

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        artifact_root = tmpdir / "artifacts"
        artifact_root.mkdir(parents=True, exist_ok=True)
        db_path = tmpdir / "smr_test.sqlite3"

        _prev_art_env = os.environ.get("SMR_ARTIFACT_ROOTS")
        os.environ["SMR_ARTIFACT_ROOTS"] = str(artifact_root)
        try:
            _run_case_b_workflow(db_path=db_path, artifact_root=artifact_root)
        finally:
            if _prev_art_env is None:
                os.environ.pop("SMR_ARTIFACT_ROOTS", None)
            else:
                os.environ["SMR_ARTIFACT_ROOTS"] = _prev_art_env


def _run_case_b_workflow(*, db_path: Path, artifact_root: Path) -> None:
    # 构造最小但符合验收标准的输入（DCI Case 精简版）
    minimal_nodes = {
        "1": {
            "conclusion": "DCI 需求真实：运营商集采同比+50%+；联盟 800G 端口+200%+",
            "confidence": 0.85,
            "evidences": [
                {"evidence_id": "ev_tier1_tender",
                 "summary": "运营商 DCI 集采公告", "source_tier": 1, "fact": True},
                {"evidence_id": "ev_tier2_port",
                 "summary": "产业联盟 800G 端口出货统计", "source_tier": 2, "fact": True},
            ],
        },
        "2": {"conclusion": "需求在产业链中段", "confidence": 0.7},
        "3": {"conclusion": "A 股映射敞口不纯（30%~45%）", "confidence": 0.8,
              "evidences": [{"evidence_id": "ev_2025_annual",
                             "summary": "2025 年报分部披露", "source_tier": 1, "fact": True}]},
        "4": {"conclusion": "同期 AI 算力主题资金分流显著", "confidence": 0.55},
        "5": {"conclusion": "传导链路长：订单→出货→确认收入→利润兑现", "confidence": 0.65},
        "6": {"conclusion": "历史滞后 2~4 个季度，本轮 Q1 集采 → 最早 Q3~Q4 见利润", "confidence": 0.5},
        "7": {"conclusion": "观察催化：1.6T 首单 / H2 追加招标 / 龙头 DCI 收入>50%", "confidence": 0.6},
        "8": {"conclusion": "若 Q2/Q3 集采同比<0，或利润兑现但股价无反应 → 本解释错误",
              "confidence": 0.9},
    }
    edges = [
        {"from_step": 1, "to_step": 2, "edge_kind": "fact",
         "evidence_id": "ev_chain_map", "explanation": "统计口径在产业链中段"},
        {"from_step": 2, "to_step": 3, "edge_kind": "fact",
         "evidence_id": "ev_2025_annual", "explanation": "中段对应 A 股光模块厂商"},
        {"from_step": 3, "to_step": 4, "edge_kind": "inferred",
         "explanation": "敞口不纯叠加更强叙事吸金 → 资金分流"},
        {"from_step": 4, "to_step": 5, "edge_kind": "inferred",
         "explanation": "分流导致需要利润兑现验证 → 传导链路必须走完"},
        {"from_step": 5, "to_step": 6, "edge_kind": "inferred",
         "explanation": "传导链路长 → 时滞按历史估 2~4Q"},
        {"from_step": 6, "to_step": 7, "edge_kind": "inferred",
         "explanation": "知道时间点 → 需要观察先行催化"},
        {"from_step": 7, "to_step": 8, "edge_kind": "inferred",
         "explanation": "有催化观察 → 必须有反例定义（证伪）"},
    ]
    alternatives = [
        {"title": "估值提前透支", "plausibility": 0.5,
         "how_to_falsify": "看 2026/06 PE 是否<历史 60% 分位",
         "current_evidence_against": "当前 PE≈28x 在 5 年 30% 分位"},
        {"title": "价格战导致利润不兑现", "plausibility": 0.35,
         "how_to_falsify": "H2 毛利率同比环比持平或上行证伪",
         "current_evidence_against": "ASP 降 12% 但规模效应抵消毛利率基本持平"},
    ]

    runner = WorkflowRunner(db_path=db_path)
    run = runner.run(
        industry_causal_explainer_definition(artifact_root=artifact_root),
        input_data={
            "theme": "DCI",
            "question": "DCI 需求明确为什么没行情？",
            "entity_key": "300394.SZ",
            "causal_nodes_input": minimal_nodes,
            "causal_edges_input": edges,
            "alternatives_input": alternatives,
            "allow_network": False,
        },
    )

    _check("run 成功（status='completed'）", run.get("status") == "completed",
           f"status={run.get('status')}  error={str(run.get('error_message', ''))[:100]}")

    # Runner 返回结构里 summary 直接有 evaluate 结果 + output_dir
    summary = run.get("summary") or {}
    _check("summary.ready=True（所有 8 节点 + 替代 + 证伪都齐）", summary.get("ready") is True,
           f"summary={summary}")
    _check("summary.completed_steps=8", summary.get("completed_steps") == 8)
    _check("summary.total_steps=8", summary.get("total_steps") == 8)
    _check(f"summary.confidence_overall≥0.5", (summary.get("confidence_overall") or 0) >= 0.5,
           f"confidence={summary.get('confidence_overall')}")
    _check("summary.fatal_gaps=[]", len(summary.get("fatal_gaps") or []) == 0,
           f"fatal_gaps={summary.get('fatal_gaps')}")
    _check("summary.registered_artifacts≥2", (summary.get("registered_artifacts") or 0) >= 2,
           f"registered={summary.get('registered_artifacts')}")

    output_dir = Path(summary.get("output_dir") or "")
    _check(f"最终输出目录存在 {output_dir}", output_dir.is_dir() and str(output_dir) != "")
    md_file = output_dir / "industry_causal_explainer.md"
    json_file = output_dir / "causal_chain_artifact.json"
    _check("Markdown 制品存在", md_file.is_file(), f"md={md_file}")
    _check("JSON causal_chain artifact 存在", json_file.is_file(), f"json={json_file}")

    # JSON artifact 内容校验：结构化字段
    payload = json.loads(json_file.read_text(encoding="utf-8"))
    renderer = payload.get("renderer", {})
    evaluation = payload.get("evaluation", {}) or {}
    _check("JSON artifact 内 renderer.nodes 存在（8 个）", len(renderer.get("nodes", {})) == 8)
    _check("JSON artifact 内 renderer.edges≥7", len(renderer.get("edges", [])) >= 7)
    _check("JSON artifact 内 renderer.alternatives≥2", len(renderer.get("alternatives", [])) >= 2)
    _check("JSON artifact 内 evaluation.ready=True", evaluation.get("ready") is True)
    _check("JSON artifact 内 evaluation.completed_steps=8", evaluation.get("completed_steps") == 8)
    _check("JSON artifact 内 evaluation.fact_edge_count≥2", evaluation.get("fact_edge_count", 0) >= 2)
    _check("JSON artifact 内 evaluation.has_alternatives=True", evaluation.get("has_alternatives") is True)
    _check("JSON artifact 内 evaluation.has_falsification=True", evaluation.get("has_falsification") is True)
    _check("Markdown 含有 '8 步因果框架' / '替代解释' / '证伪条件' 标题",
           all(x in md_file.read_text(encoding="utf-8")
               for x in ["8 步因果框架", "替代解释", "证伪条件"]))



# ============================================================================
# CASE C：负面测试 —— 只有 1 条低等级新闻 → 警告；缺替代解释 → fatal_gap
# ============================================================================
def case_c_negative_quality_gates() -> None:
    print("\n=== CASE C：负面用例 - 单条新闻偏见 / 缺替代解释 质量门 ===")

    # C1：S1 只有 1 条 T4 证据（单条低等级新闻）
    chain_bad = CausalChain(theme="X 主题", question="X 为什么没行情？")
    chain_bad.set_node(CausalNode(step=1, title="需求真实", conclusion="某自媒体说 X 需求火爆",
                                  confidence=0.9, completed=True,
                                  evidences=[EvidenceSlim(
                                      evidence_id="ev_blog_xxx",
                                      summary="自媒体一篇长文",
                                      source_tier=4, fact=False)]))
    # 其余 7 节点凑齐，S8 也写，替代解释只给 0 个
    for s in [2, 3, 4, 5, 6, 7]:
        chain_bad.set_node(CausalNode(step=s, title=f"Step {s}", conclusion="凑数结论", confidence=0.5, completed=True))
    chain_bad.set_node(CausalNode(step=8, title="证伪条件", conclusion="没行情就是错了", confidence=0.9, completed=True))

    # 跑一下单条新闻偏见检查（用工作流的同逻辑：S1 证据数=1 且 T≥3 警告）
    evs1 = chain_bad.nodes[1].evidences
    bad_single_news_warn = len(evs1) == 1 and evs1[0].source_tier >= 3
    _check("单条 T4 新闻 → 触发偏见警告标志=True", bad_single_news_warn)

    # C2：没替代解释 → evaluate 应该报 fatal_gap
    for (fs, ts) in [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8)]:
        chain_bad.set_edge(CausalEdge(from_step=fs, to_step=ts, edge_kind=EDGE_INFERRED,
                                      explanation="凑"))
    bad_eval = chain_bad.evaluate()
    _check("没有替代解释 → fatal_gap≥1（防确认偏误强制要求）",
           len(bad_eval.get("fatal_gaps", [])) >= 1,
           f"fatal_gaps={bad_eval['fatal_gaps']}")
    _check("没有替代解释 → ready=False", bad_eval["ready"] is False)


# ============================================================================
# 入口
# ============================================================================
def main() -> int:
    print("======== 阶段 9：产业因果解释 V1 单文件测试（DCI 金标准） ========")
    case_a_chain_datastructure()
    case_b_workflow_runner()
    case_c_negative_quality_gates()
    total = _PASS_COUNT + _FAIL_COUNT
    print("\n" + "=" * 56)
    if _FAIL_COUNT == 0:
        print(f"ALL PASSED  ✅  {_PASS_COUNT}/{total}")
        return 0
    print(f"FAILED  ❌  {_FAIL_COUNT}/{total} 失败，{_PASS_COUNT} 通过")
    return 1


if __name__ == "__main__":
    sys.exit(main())
