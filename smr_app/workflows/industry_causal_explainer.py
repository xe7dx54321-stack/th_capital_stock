"""
产业因果解释工作流 V1（industry_causal_explainer）

功能说明：
    阶段 9「产业因果解释 V1」的核心工作流编排层。
    严格按 master plan 阶段 9 的 8 步固定分析框架 + 金标准（"DCI 需求明确但 A 股长期没有催化"）。

    解决的问题（小白版）：
        "需求明明在那里，为什么相关股票一直不涨？"
        我们不是"凭感觉找原因"，而是按 8 步逐一拆：
        S1 需求真不真？S2 在产业链哪一层？S3 A 股有没有纯映射？
        S4 是不是被其他主题抢了注意力？S5 订单怎么到利润？S6 要多久？
        S7 什么催化会涨？S8 什么情况证明我分析错了？
        另外必须同时列"替代解释"和"证伪条件"，防止确认偏误。

    工作流 11 阶段（stage）：
        1. validate_input          验证核心字段（主题/问题/实体/原始事实/假设）
        2. assemble_nodes          填充 S1~S8 8 个因果节点（可以接 EvidenceRegistry）
        3. assemble_edges          填充 S1→S2 / S2→S3 ... 7 条因果边
        4. assemble_alternatives   添加替代解释（至少 1 个，防确认偏误）
        5. check_single_news_bias  禁止"单条新闻解释长期行情"强制质量门
        6. evaluate_chain          评估整体质量（节点完整度 / fact: inferred / 致命缺口）
        7. render_markdown         产出 Markdown 报告（给人读）
        8. render_json             产出 JSON causal_chain_artifact（给程序用）
        9. persist_outputs         保存 2 种制品 + ArtifactStore 注册
       10. summary                 输出最终结果摘要

参数说明：
    industry_causal_explainer_definition(*) → WorkflowDefinition（可交给 Runner）

    input_data 字段：
        theme               (必填) 字符串，例 "DCI"
        question            (必填) 核心问题，例 "为什么 DCI 需求明确但 A 股没行情？"
        entity_key          (可选) 例 "300394.SZ/688xxx.SH 组合"，研究的代表性公司
        causal_nodes_input  (必填) dict，键 "1"~"8" → dict{conclusion, detail, confidence, evidences[]}
        causal_edges_input  (必填) list[{from_step,to_step,edge_kind,explanation,...}]
        alternatives_input  (必填) list[{title, plausibility, how_to_falsify, ...}]
        allow_network       (必须=False) 所有研究原始事实应前置，不在工作流内联网

返回值说明：
    制品：
        causal_chain_artifact.json  - 结构化 causal chain（节点/边/替代/评估，可复算）
        industry_causal_explainer.md - 人可读 Markdown 报告
    state.summary 含：节点完成数 / 整体信心度 / 是否 ready / 缺口数

异常处理：
    - allow_network!=False：阶段 1 直接抛 ValueError 拒绝
    - 缺 S1/S3/S5/S7 关键节点：evaluate 里标 fatal_gap，但工作流仍能保存（不崩）
    - 缺替代解释：evaluate 里标 fatal_gap + 不满足阶段 9 验收条件（仍生成制品，标记 degraded）
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from smr_app.runtime.artifact_store import ArtifactStore
from smr_app.runtime.contracts import (
    StageDefinition,
    StageResult,
    WorkflowContext,
    WorkflowDefinition,
)
from smr_app.research.causal_chain import (
    CausalChain,
    CausalNode,
    CausalEdge,
    EvidenceSlim,
    AlternativeExplanation,
    CausalRenderer,
    ALL_STEPS,
    STEP_LABELS,
    EDGE_FACT,
    EDGE_INFERRED,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _get_default_artifact_root() -> Path:
    configured = os.environ.get("SMR_ARTIFACT_ROOTS", "").split(os.pathsep)
    if configured and configured[0]:
        return Path(configured[0])
    return PROJECT_ROOT / "06_outputs" / "workflows"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# =============================================================================
# 1. validate_input
# =============================================================================

def _validate_input(ctx: WorkflowContext) -> StageResult:
    """
    验证工作流输入

    小白讲解：这里是"门卫"，检查必填字段都有，且 allow_network=False。
    """
    inp = ctx.input_data
    theme = inp.get("theme")
    question = inp.get("question")
    if not theme or not isinstance(theme, str) or not theme.strip():
        raise ValueError("theme 必填（例：'DCI'）")
    if not question or not isinstance(question, str) or not question.strip():
        raise ValueError("question 必填（例：'为什么 DCI 需求明确但没行情？'）")
    allow_network = inp.get("allow_network", False)
    if allow_network is not False:
        raise ValueError("industry_causal_explainer 只支持 allow_network=False（离线研究）")
    nodes = inp.get("causal_nodes_input") or {}
    edges = inp.get("causal_edges_input") or []
    alts = inp.get("alternatives_input") or []
    if not isinstance(nodes, dict):
        raise ValueError("causal_nodes_input 必须是 dict（键 '1'..'8'）")
    if not isinstance(edges, list):
        raise ValueError("causal_edges_input 必须是列表")
    if not isinstance(alts, list):
        raise ValueError("alternatives_input 必须是列表")

    ctx.state.update({
        "theme": theme,
        "question": question,
        "entity_key": inp.get("entity_key", ""),
        "nodes_input": nodes,
        "edges_input": edges,
        "alts_input": alts,
    })
    return StageResult.completed(
        "输入验证通过",
        {
            "theme": theme,
            "question_len": len(question),
            "node_keys_provided": sorted(nodes.keys()),
            "edges_count": len(edges),
            "alternatives_count": len(alts),
        },
    )


# =============================================================================
# 2. assemble_nodes
# =============================================================================

def _assemble_nodes(ctx: WorkflowContext) -> StageResult:
    """
    组装 S1~S8 八个因果节点

    小白讲解：把用户传入的 causal_nodes_input 字典转成 CausalNode 对象列表，
    每条证据变成 EvidenceSlim。
    """
    theme = ctx.state["theme"]
    question = ctx.state["question"]
    entity_key = ctx.state["entity_key"]
    chain = CausalChain(theme=theme, question=question, entity_key=entity_key)

    nodes_input = ctx.state["nodes_input"]
    for step_num in ALL_STEPS:
        raw = nodes_input.get(str(step_num)) or nodes_input.get(step_num) or {}
        ev_raw_list = raw.get("evidences") or []
        ev_list: list[EvidenceSlim] = []
        for ev in ev_raw_list:
            ev_list.append(EvidenceSlim(
                evidence_id=str(ev.get("evidence_id", "")),
                summary=str(ev.get("summary", "")),
                source_tier=int(ev.get("source_tier", 4)),
                fact=bool(ev.get("fact", False)),
            ))
        confidence = raw.get("confidence", 0.0)
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.0
        has_conclusion = bool(str(raw.get("conclusion", "")).strip())
        node = CausalNode(
            step=step_num,
            title=raw.get("title") or STEP_LABELS[step_num],
            conclusion=str(raw.get("conclusion", "")),
            detail=str(raw.get("detail", "")),
            evidences=ev_list,
            confidence=confidence,
            completed=has_conclusion,
            alternative_findings=[str(x) for x in (raw.get("alternative_findings") or [])],
        )
        chain.set_node(node)

    ctx.state["chain"] = chain
    return StageResult.completed(
        f"S1~S8 节点组装完成，已填 {len(chain.nodes)}/8",
        {"nodes_filled_count": len(chain.nodes), "steps": sorted(chain.nodes.keys())},
    )


# =============================================================================
# 3. assemble_edges
# =============================================================================

def _assemble_edges(ctx: WorkflowContext) -> StageResult:
    """
    组装 S1→S2 到 S7→S8 的 7 条因果边

    小白讲解：检查每条边是不是 step 连续，fact 边有没有 evidence_id。
    """
    chain: CausalChain = ctx.state["chain"]
    edges_input = ctx.state["edges_input"]
    for raw in edges_input:
        fs = raw.get("from_step")
        ts = raw.get("to_step")
        try:
            fs_int = int(fs); ts_int = int(ts)
        except (TypeError, ValueError):
            chain.warnings.append(f"边 {raw} 步号不是整数，已跳过")
            continue
        ekind = raw.get("edge_kind") or EDGE_INFERRED
        if ekind == EDGE_FACT and not str(raw.get("evidence_id", "")).strip():
            ekind = EDGE_INFERRED  # 降级
            chain.warnings.append(
                f"边 S{fs_int}→S{ts_int} 声明 fact 但无 evidence_id，已自动降级为 inferred"
            )
        chain.set_edge(CausalEdge(
            from_step=fs_int,
            to_step=ts_int,
            edge_kind=ekind,
            explanation=str(raw.get("explanation", "")),
            evidence_id=str(raw.get("evidence_id", "")),
            historical_precedent=str(raw.get("historical_precedent", "")),
        ))
    return StageResult.completed(
        f"组装了 {len(chain.edges)} 条因果边",
        {
            "edges_count": len(chain.edges),
            "fact_edges": sum(1 for e in chain.edges if e.edge_kind == EDGE_FACT),
            "inferred_edges": sum(1 for e in chain.edges if e.edge_kind == EDGE_INFERRED),
        },
    )


# =============================================================================
# 4. assemble_alternatives
# =============================================================================

def _assemble_alternatives(ctx: WorkflowContext) -> StageResult:
    """
    添加替代解释（防确认偏误）

    小白讲解：不能只看自己想相信的解释，必须列出"也可能是估值高了、也可能是需求不在 A 股、
    也可能是有解禁压力"等替代解释，并写明各自"如何证伪"。
    """
    chain: CausalChain = ctx.state["chain"]
    alts_input = ctx.state["alts_input"]
    for raw in alts_input:
        plaus = raw.get("plausibility", 0.3)
        try:
            plaus = float(plaus)
        except (TypeError, ValueError):
            plaus = 0.3
        if plaus < 0: plaus = 0.0
        if plaus > 1: plaus = 1.0
        chain.add_alternative(AlternativeExplanation(
            title=str(raw.get("title", "")),
            plausibility=plaus,
            how_to_falsify=str(raw.get("how_to_falsify", "")),
            current_evidence_against=str(raw.get("current_evidence_against", "")),
        ))
    return StageResult.completed(
        f"添加了 {len(chain.alternatives)} 个替代解释",
        {"alternatives_count": len(chain.alternatives)},
    )


# =============================================================================
# 5. check_single_news_bias
# =============================================================================

def _check_single_news_bias(ctx: WorkflowContext) -> StageResult:
    """
    单条新闻偏见检查

    小白讲解：阶段 9 验收明确写了"不用单条新闻解释长期行情"。
    如果 S1（需求真实）只有 1 条 4 级证据，就加警告。
    """
    chain: CausalChain = ctx.state["chain"]
    n1 = chain.nodes.get(1)
    warning = None
    if n1 is None:
        warning = "S1（需求真实）未填写——没有支撑的长期行情解释属于空口无凭"
    else:
        ev_count = len(n1.evidences)
        avg_tier = (
            sum(e.source_tier for e in n1.evidences) / ev_count
            if ev_count else 999
        )
        if ev_count == 1 and avg_tier >= 3:
            warning = (
                f"S1 只有 {ev_count} 条证据（权威等级 {avg_tier:.1f}），"
                "单条低等级新闻不能解释长期行情，请至少补 2~3 条独立 1~2 级证据"
            )
    if warning:
        chain.warnings.append(warning)
    return StageResult.completed(
        "单条新闻偏见检查完成",
        {"passed": warning is None, "warning": warning or ""},
    )


# =============================================================================
# 6. evaluate_chain
# =============================================================================

def _evaluate_chain(ctx: WorkflowContext) -> StageResult:
    """调用 chain.evaluate() 评估整体质量"""
    chain: CausalChain = ctx.state["chain"]
    evaluation = chain.evaluate()
    ctx.state["evaluation"] = evaluation
    return StageResult.completed(
        "因果链评估完成" + ("（已满足阶段 9 所有验收条件）" if evaluation["ready"] else "（仍有致命缺口）"),
        {
            "ready": evaluation["ready"],
            "completed_steps": f"{evaluation['completed_steps']}/8",
            "confidence_overall": evaluation["confidence_overall"],
            "fact_edges_count": evaluation["fact_edge_count"],
            "has_alternatives": evaluation["has_alternatives"],
            "has_falsification": evaluation["has_falsification"],
            "fatal_gaps_count": len(evaluation["fatal_gaps"]),
            "warnings_count": len(evaluation["warnings"]),
        },
    )


# =============================================================================
# 7. render_markdown & 8. render_json & 9. persist_outputs 合并写
# =============================================================================

def _render_and_persist_stage(artifact_root: Path):
    """构建渲染+保存阶段（闭包注入 artifact_root 路径）"""

    def handler(ctx: WorkflowContext) -> StageResult:
        chain: CausalChain = ctx.state["chain"]
        evaluation = ctx.state["evaluation"]

        run_dir: Path = artifact_root.resolve() / ctx.run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        md_path = run_dir / "industry_causal_explainer.md"
        md_path.write_text(
            CausalRenderer.to_markdown(chain), encoding="utf-8",
        )

        json_path = run_dir / "causal_chain_artifact.json"
        json_path.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "generated_at": _utc_now(),
                    "run_id": ctx.run_id,
                    "renderer": CausalRenderer.to_dict(chain),
                    "evaluation": evaluation,
                    "warnings": chain.warnings,
                },
                ensure_ascii=False, indent=2, default=str,
            ),
            encoding="utf-8",
        )

        registered = []
        try:
            conn = sqlite3.connect(ctx.db_path)
            try:
                store = ArtifactStore(conn, [artifact_root])
                md_art = store.register_artifact(
                    ctx.run_id,
                    "industry_causal_report",
                    f"产业因果解释报告 — {ctx.state['theme']}",
                    md_path, "text/markdown",
                    metadata={"theme": ctx.state["theme"], "ready": evaluation["ready"]},
                )
                j_art = store.register_artifact(
                    ctx.run_id,
                    "causal_chain",
                    f"结构化因果链 JSON — {ctx.state['theme']}",
                    json_path, "application/json",
                    metadata={"theme": ctx.state["theme"], "ready": evaluation["ready"]},
                )
                registered = [md_art, j_art]
            finally:
                conn.close()
        except sqlite3.Error:
            # DB 注册失败不影响制品已写入
            pass

        ctx.state.update({
            "markdown_path": str(md_path),
            "json_path": str(json_path),
            "registered_artifacts": registered,
            "output_dir": str(run_dir),
        })
        summary = {
            "ready": evaluation["ready"],
            "output_dir": str(run_dir),
            "markdown_path": str(md_path),
            "json_path": str(json_path),
            "registered_count": len(registered),
            "completed_steps": f"{evaluation['completed_steps']}/8",
            "confidence_overall": evaluation["confidence_overall"],
            "fatal_gaps_count": len(evaluation["fatal_gaps"]),
            "artifact_ids": [a.get("artifact_id", "") for a in registered],
        }
        return StageResult.completed("Markdown + JSON 制品已保存", summary, artifacts=tuple(registered))

    return handler


# =============================================================================
# 10. 最终总结
# =============================================================================

def _final_summary(ctx: WorkflowContext) -> StageResult:
    chain: CausalChain = ctx.state["chain"]
    eval_r = ctx.state["evaluation"]
    summary = {
        "theme": ctx.state["theme"],
        "question": ctx.state["question"],
        "ready": eval_r["ready"],
        "completed_steps": eval_r["completed_steps"],
        "total_steps": 8,
        "confidence_overall": eval_r["confidence_overall"],
        "fatal_gaps": list(eval_r["fatal_gaps"]),
        "warnings": list(chain.warnings),
        "output_dir": ctx.state.get("output_dir"),
        "registered_artifacts": len(ctx.state.get("registered_artifacts", [])),
    }
    ctx.state["summary"] = summary
    return StageResult.completed("因果解释工作流完成", summary)


# =============================================================================
# Workflow Definition
# =============================================================================

def industry_causal_explainer_definition(
    *,
    artifact_root: Path | None = None,
) -> WorkflowDefinition:
    """
    构建产业因果解释 V1 工作流定义

    小白调用示例（伪代码）：
        runner = WorkflowRunner(db_path=...)
        runner.run(industry_causal_explainer_definition(), input_data=...)
    """
    root = artifact_root or _get_default_artifact_root()

    stages = [
        StageDefinition("validate_input", _validate_input,
                        title="1. 验证必填字段 + allow_network=False"),
        StageDefinition("assemble_nodes", _assemble_nodes,
                        title="2. 组装 S1~S8 8 个因果节点（+证据）"),
        StageDefinition("assemble_edges", _assemble_edges,
                        title="3. 组装 S1→S2 / S2→S3 ... 7 条因果边"),
        StageDefinition("assemble_alternatives", _assemble_alternatives,
                        title="4. 添加≥1 个替代解释（防确认偏误）"),
        StageDefinition("check_single_news_bias", _check_single_news_bias,
                        title="5. 禁止单条新闻解释长期行情"),
        StageDefinition("evaluate_chain", _evaluate_chain,
                        title="6. 因果链质量评估（ready / fatal_gaps）"),
        StageDefinition("render_persist", _render_and_persist_stage(root),
                        title="7-9. 渲染 Markdown/JSON + ArtifactStore 注册"),
        StageDefinition("final_summary", _final_summary,
                        title="10. 最终总结"),
    ]

    return WorkflowDefinition(
        workflow_id="industry_causal_explainer",
        title="产业因果解释 V1（DCI 需求明确但没行情？8 步证据化拆解）",
        description=(
            "严格按阶段 9 的 8 步框架 + 替代解释 + 证伪条件，"
            "把长期没行情拆成可验证的因果节点，禁止单条新闻解释长期行情。"
        ),
        stages=tuple(stages),
    )
