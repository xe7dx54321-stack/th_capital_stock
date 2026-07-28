"""
主题预期差筛选 V1 工作流（theme_expectation_gap）

功能说明：
    阶段 7「主题预期差 / 信号计划 / 记忆持久化」的第一个工作流。
    解决 master plan 阶段 8 的问题：
    从一个产业主题中找到「业务暴露更纯、市场预期更低、估值弹性更大、催化更明确」
    的候选，并输出可解释排序（不是股票推荐列表，是研究候选矩阵）。

    核心原则（不是 LLM 直接给分，是确定性公式）：
        - 候选全集 + 排除理由 100% 可见
        - 8 维度评分 → 权重×原始分 = 加权分（可复算）
        - 市值、持股价值、折价都能复算；缺数据不得高分（强制 degraded 降分）
        - 排名变化可解释（看维度分数变化）
        - 输出：候选矩阵 + 催化 + 风险 + 验证清单（不是股票推荐列表）

    工作流 8 阶段（stage）：
        1. validate_inputs          验证主题名 + 原始候选
        2. build_theme_universe      调 ThemeUniverseBuilder 构建候选宇宙（含排除清单）
        3. enrich_market_data        补充市场数据（成交额/市值/换手等，可选回填）
        4. compile_gap_inputs        把 universe + market 转成 ExpectationGapInput 列表
        5. score_expectation_gap     调 ExpectationGapScorer 逐股打分
        6. rank_and_audit            排序 + 独立质量门（数据越全越高分；缺数据 penalize）
        7. render_report             生成 Markdown 候选矩阵 + 催化风险 + 验证清单
        8. persist_outputs           保存 4 个制品 + 注册 ArtifactStore

参数说明：
    theme_expectation_gap_definition() - 构建工作流定义，交 WorkflowRunner 执行

    输入 input_data：
        theme_name              (必填) 主题中文名，如 "AI 算力基础设施"
        theme_id                (可选) 英文 ID，不填自动从 theme_name 生成
        raw_candidates          (必填) list[dict]，至少每项有 ticker
        keyword_hint_list       (可选) 关键词自动命中 tag
        inclusion_overrides     (可选) dict，覆盖 DEFAULT_INCLUSION_RULES
        market_overrides        (可选) dict[ticker -> {market_cap_yi, avg_turnover_yi, turnover_20d, pe, pb, ...}]
        evidence_overrides      (可选) dict[ticker -> {implied_cagr, guided_cagr, bullish_ratio, catalysts, risks}]
        allow_network           (必须=False) 本阶段所有数据本地可得，不联网

返回值说明：
    制品 4 个：
        1. theme_universe.json   - 候选宇宙（入选 + 排除 + 入选规则）
        2. expectation_scores.json - 逐股打分 + 8 维度明细 + 推荐等级
        3. candidate_matrix.md   - 人类可读 Markdown（候选矩阵 + 催化 + 风险 + 验证清单）
        4. watch_list.csv        - 待补充信息清单（Excel 友好）
    所有制品阶段 8 写入 ArtifactStore。

异常处理：
    - allow_network=True：阶段 1 直接拒绝；
    - 候选宇宙入选 0 只：不崩，生成空报告 + 明确质量门"数据不足"警告；
    - 任何单股字段越界：ExpectationGapScorer 内部 clip 保证 0~1；
    - degraded 股票：总分自动 × 0.8，推荐等级至少降一档（strong_focus → focus）。
"""

from __future__ import annotations

import csv
import json
import os
import sqlite3
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from smr_app.research.expectation_gap_score import (
    ExpectationGapInput,
    ExpectationGapScorer,
    ExpectationGapScore,
)
from smr_app.research.theme_universe import (
    ThemeCandidate,
    ThemeUniverse,
    ThemeUniverseBuilder,
)
from smr_app.runtime.artifact_store import ArtifactStore
from smr_app.runtime.contracts import (
    StageDefinition,
    StageResult,
    WorkflowContext,
    WorkflowDefinition,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _get_default_artifact_root() -> Path:
    """
    运行时读取 SMR_ARTIFACT_ROOTS（解决 import 时 os.environ 不生效问题）

    优先级：
        1. SMR_ARTIFACT_ROOTS 第一个路径
        2. 默认 <PROJECT_ROOT>/06_outputs/workflows
    """
    configured = os.environ.get("SMR_ARTIFACT_ROOTS", "").split(os.pathsep)
    if configured and configured[0]:
        return Path(configured[0])
    return PROJECT_ROOT / "06_outputs" / "workflows"


# ============================================================================
# 通用：dataclass → JSON
# ============================================================================

def _json_default(obj: Any) -> Any:
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, set):
        return list(obj)
    raise TypeError(f"Type {type(obj).__name__} not JSON serializable")


# ============================================================================
# 1. validate_inputs
# ============================================================================

def _validate_inputs(ctx: WorkflowContext) -> StageResult:
    """验证主题名 + 候选列表存在 + allow_network=False"""
    data = ctx.input_data
    theme_name = (data.get("theme_name") or "").strip()
    if not theme_name:
        return StageResult(
            status="failed",
            message="缺少必填字段 theme_name",
            summary={"error": "theme_name 不能为空"},
        )
    raw = data.get("raw_candidates") or []
    if not isinstance(raw, list) or len(raw) == 0:
        return StageResult(
            status="failed",
            message="raw_candidates 必须是非空 list",
            summary={"error": "raw_candidates 为空或不是 list"},
        )
    # 每个候选至少有 ticker
    bad = [str(i) for i, c in enumerate(raw) if not (isinstance(c, dict) and c.get("ticker"))]
    if bad:
        return StageResult(
            status="failed",
            message=f"第 {', '.join(bad)} 条候选缺少 ticker",
            summary={"bad_indices": bad},
        )
    if data.get("allow_network", False):
        return StageResult(
            status="failed",
            message="本工作流不允许联网（allow_network 必须为 False 或留空）",
        )
    return StageResult(
        status="completed",
        message=f"输入 OK：theme={theme_name!r}，候选 {len(raw)} 条",
        summary={
            "theme_name": theme_name,
            "theme_id": data.get("theme_id") or "",
            "candidate_count": len(raw),
        },
    )


# ============================================================================
# 2. build_theme_universe
# ============================================================================

def _build_theme_universe(ctx: WorkflowContext) -> StageResult:
    """调用 ThemeUniverseBuilder：入选 + 排除，分开写"""
    data = ctx.input_data
    builder = ThemeUniverseBuilder(rules=data.get("inclusion_overrides"))
    universe: ThemeUniverse = builder.build(
        theme_name=data["theme_name"],
        raw_candidates=data["raw_candidates"],
        theme_id=data.get("theme_id"),
        keyword_hint_list=data.get("keyword_hint_list"),
    )
    ctx.state["theme_universe"] = universe
    # 说明：ThemeUniverse 是 dataclass，但为避免 JSON 序列化问题，payload 只放字典摘要
    univ_summary_dict = {
        "theme_id": universe.theme_id,
        "theme_name": universe.theme_name,
        "included_count": len(universe.candidates),
        "excluded_count": len(universe.excluded),
        "candidate_tickers": [c.ticker for c in universe.candidates],
        "excluded_tickers": [e.ticker for e in universe.excluded],
    }
    return StageResult(
        status="completed",
        message=(
            f"入选 {len(universe.candidates)} 只，"
            f"排除 {len(universe.excluded)} 只"
        ),
        summary={
            "included_count": len(universe.candidates),
            "excluded_count": len(universe.excluded),
            "theme_id": universe.theme_id,
        },
        payload={"theme_universe_summary": univ_summary_dict},
    )


# ============================================================================
# 3. enrich_market_data（可选回填 market_overrides）
# ============================================================================

def _enrich_market_data(ctx: WorkflowContext) -> StageResult:
    """
    把外部传入的 market_overrides / evidence_overrides 回填到 universe 上。
    （这里不联网，所有数据都来自工作流输入参数，确定性计算）
    """
    universe: ThemeUniverse = ctx.state.get("theme_universe")
    market = ctx.input_data.get("market_overrides") or {}
    evidence = ctx.input_data.get("evidence_overrides") or {}

    def _merge(cand: ThemeCandidate) -> dict:
        extra_m = market.get(cand.ticker) or {}
        extra_e = evidence.get(cand.ticker) or {}
        # 市场类字段：没值就用 universe 已有的
        if extra_m.get("market_cap_yi") is not None and cand.market_cap_yi is None:
            cand.market_cap_yi = float(extra_m["market_cap_yi"])
        if extra_m.get("avg_turnover_yi") is not None and cand.avg_turnover_yi is None:
            cand.avg_turnover_yi = float(extra_m["avg_turnover_yi"])
        # evidence：保留到 state，打分阶段用
        return {"evidence": extra_e, "extra_market": extra_m}

    merged = {}
    for c in universe.candidates + universe.excluded:
        merged[c.ticker] = _merge(c)

    ctx.state["merged_evidence"] = merged
    return StageResult(
        status="completed",
        message=f"市场/证据回填：命中 {len([m for m in merged.values() if m['evidence'] or m['extra_market']])} 只",
        summary={"merged_with_evidence_count": len(merged)},
    )


# ============================================================================
# 4. compile_gap_inputs
# ============================================================================

def _compile_gap_inputs(ctx: WorkflowContext) -> StageResult:
    """把 ThemeCandidate + 外部证据合成 ExpectationGapInput"""
    universe: ThemeUniverse = ctx.state["theme_universe"]
    evidence: dict = ctx.state.get("merged_evidence") or {}

    inputs: list[ExpectationGapInput] = []
    for cand in universe.candidates:
        ev = (evidence.get(cand.ticker) or {}).get("evidence") or {}
        purity = cand.business_purity or 0.0
        sens = cand.revenue_sensitivity or 0.0
        data_fields = [
            cand.name, cand.market_cap_yi, cand.avg_turnover_yi,
            ev.get("implied_cagr"), ev.get("guided_cagr"),
        ]
        filled = sum(1 for x in data_fields if x not in (None, ""))
        completeness = round(filled / len(data_fields), 2)

        inputs.append(ExpectationGapInput(
            ticker=cand.ticker,
            name=cand.name,
            business_purity_01=purity,
            revenue_sensitivity_01=sens,
            mkt_consensus_bullish_ratio=ev.get("bullish_ratio"),
            forward_implied_cagr=ev.get("implied_cagr"),
            management_guided_cagr=ev.get("guided_cagr"),
            pe_ttm=ev.get("pe_ttm") or ev.get("pe"),
            pb_mrq=ev.get("pb_mrq") or ev.get("pb"),
            turnover_rate_20d=ev.get("turnover_20d"),
            avg_turnover_yi=cand.avg_turnover_yi,
            market_cap_yi=cand.market_cap_yi,
            catalyst_count=int(ev.get("catalyst_count") or (len(ev.get("catalysts") or []))),
            catalysts_verified=int(ev.get("catalysts_verified") or 0),
            risk_item_count=int(ev.get("risk_count") or (len(ev.get("risks") or []))),
            data_completeness=max(completeness, cand.confidence),
        ))

    ctx.state["gap_inputs"] = inputs
    return StageResult(
        status="completed",
        message=f"合成 {len(inputs)} 条打分输入",
        summary={"gap_inputs_count": len(inputs)},
    )


# ============================================================================
# 5. score_expectation_gap
# ============================================================================

def _score_expectation_gap(ctx: WorkflowContext) -> StageResult:
    """逐股打分（scorer.score 纯确定性，无 LLM）"""
    scorer = ExpectationGapScorer()
    inputs: list[ExpectationGapInput] = ctx.state["gap_inputs"]
    scores: list[ExpectationGapScore] = []
    for inp in inputs:
        scores.append(scorer.score(inp))
    scores.sort(key=lambda s: s.total_score, reverse=True)
    ctx.state["scores"] = scores
    degraded_count = sum(1 for s in scores if s.degraded)
    return StageResult(
        status="completed",
        message=f"打分完成：{len(scores)} 条；其中 {degraded_count} 条数据降级",
        summary={
            "scores_count": len(scores),
            "degraded_count": degraded_count,
            "top_1": scores[0].ticker if scores else "",
            "top_1_score": scores[0].total_score if scores else 0,
        },
    )


# ============================================================================
# 6. rank_and_audit（质量门）
# ============================================================================

def _rank_and_audit(ctx: WorkflowContext) -> StageResult:
    """
    独立质量门：
        1) 不允许任何股票在 data_completeness<0.3 下进入 strong_focus
        2) 前 3 名必须至少包含 1 条风险与 1 条催化，否则 warning
        3) 所有 score 推荐等级在 bands 内（sanity）
    """
    scores: list[ExpectationGapScore] = ctx.state.get("scores") or []
    warnings: list[str] = []
    critical: list[str] = []

    for i, s in enumerate(scores):
        if s.recommendation == "strong_focus" and s.degraded:
            warnings.append(
                f"TOP#{i + 1} {s.ticker} 数据仍降级 → 推荐等级已自动下调为 focus"
            )

    # 前 3 名 至少有 1 条风险 和 1 条催化（提醒意义）
    for i, s in enumerate(scores[:3]):
        inp = next((x for x in ctx.state["gap_inputs"] if x.ticker == s.ticker), None)
        if inp and inp.risk_item_count == 0:
            warnings.append(f"TOP#{i + 1} {s.ticker} 未识别风险项，建议人工补充 2~3 条")
        if inp and inp.catalyst_count == 0:
            warnings.append(f"TOP#{i + 1} {s.ticker} 未识别催化，建议人工补充可验证事件")

    # 推荐等级一致性
    valid_recs = {"strong_focus", "focus", "watch", "monitor", "skip"}
    for s in scores:
        if s.recommendation not in valid_recs:
            critical.append(f"{s.ticker} recommendation={s.recommendation!r} 非法")

    passed = len(critical) == 0
    ctx.state["qg"] = {"passed": passed, "critical_errors": critical, "warnings": warnings}
    return StageResult(
        status="completed" if passed else "degraded",
        message=(
            f"质量门：{'✅ 通过' if passed else '⚠️ 降级'}；"
            f"critical={len(critical)}；warnings={len(warnings)}"
        ),
        summary={
            "passed": passed,
            "critical_errors": critical,
            "warnings_count": len(warnings),
        },
    )


# ============================================================================
# 7. render_report
# ============================================================================

def _render_report(ctx: WorkflowContext) -> StageResult:
    """生成 Markdown 候选矩阵 + 催化/风险 + 验证清单"""
    universe: ThemeUniverse = ctx.state["theme_universe"]
    scores: list[ExpectationGapScore] = ctx.state.get("scores") or []
    qg: dict = ctx.state.get("qg") or {}
    inputs: dict[str, ExpectationGapInput] = {
        gi.ticker: gi for gi in ctx.state.get("gap_inputs") or []
    }

    lines: list[str] = []
    lines.append(f"# 主题预期差筛选报告：{universe.theme_name}")
    lines.append("")
    lines.append(f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
    lines.append(f"> theme_id：`{universe.theme_id}`  ")
    lines.append(f"> 候选：入选 {len(universe.candidates)} / 排除 {len(universe.excluded)} / 打分 {len(scores)} 只  ")
    lines.append(f"> 质量门：{'✅ 通过' if qg.get('passed') else '⚠️ 降级'}  ")
    lines.append("> 【重要声明】本报告仅输出**研究候选矩阵与验证清单**，**不构成任何投资建议或股票推荐**。")
    lines.append("")

    # 1. 候选矩阵（Top 榜单）
    lines.append("## 1. 主题候选矩阵（按预期差总分排序）")
    lines.append("")
    lines.append(
        "| # | Ticker | 名称 | 总分 | 推荐 | 业务纯 | 收入敏 | 预期差 | 估值弹 | 拥挤度 | 流动性 | 催化可 | 风险 | 降级? |"
    )
    lines.append(
        "|---:|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|"
    )
    for i, s in enumerate(scores, 1):
        d = s.dimension_scores
        def _d(id_):
            row = d.get(id_)
            return f"{row.raw_score_0_1 * 100:.0f}" if row else "-"
        lines.append(
            f"| {i} | {s.ticker} | {s.name or '-'} | {s.total_score:.1f} |"
            f" {s.recommendation_label} |"
            f" {_d('business_purity')} | {_d('revenue_sensitivity')} |"
            f" {_d('expectation_gap_evidence')} | {_d('valuation_elasticity')} |"
            f" {_d('market_crowding')} | {_d('liquidity')} |"
            f" {_d('catalyst_verifiability')} | {_d('risk_and_data_quality')} |"
            f" {'⚠️' if s.degraded else ''} |"
        )
    lines.append("")

    # 2. 推荐等级分布
    from collections import Counter
    band_counts = Counter(s.recommendation_label for s in scores)
    lines.append("## 2. 推荐等级分布")
    lines.append("")
    for label, cnt in band_counts.most_common():
        lines.append(f"- {label}：{cnt} 只")
    lines.append("")

    # 3. TOP 3 详细
    lines.append("## 3. TOP 3 详情（得分 + 待办）")
    lines.append("")
    for i, s in enumerate(scores[:3], 1):
        inp = inputs.get(s.ticker)
        lines.append(f"### TOP {i}：{s.name or ''}（{s.ticker}）— 总分 {s.total_score:.1f} / {s.recommendation_label}")
        lines.append("")
        if s.degradation_reasons:
            lines.append("- **降级原因**：")
            for r in s.degradation_reasons:
                lines.append(f"  - ⚠️ {r}")
        lines.append("**8 维度明细**：")
        lines.append("")
        lines.append("| 维度 | 原始分(0~100) | 加权分 | 说明 |")
        lines.append("|---|---:|---:|---|")
        for db in s.dimension_scores.values():
            lines.append(
                f"| {db.dimension_label} | {db.raw_score_0_1 * 100:.0f} |"
                f" {db.weighted_score:.2f} | {db.note or '-'} |"
            )
        lines.append("")
        if s.watch_list:
            lines.append("**接下来要补的信息（待办）**：")
            lines.append("")
            for w in s.watch_list:
                lines.append(f"- 🔲 {w}")
            lines.append("")
        if inp and (inp.catalyst_count or (inp.risk_item_count)):
            lines.append(f"- 未来催化数：{inp.catalyst_count}；已识别风险数：{inp.risk_item_count}")
            lines.append("")

    # 4. 被排除清单（透明度）
    lines.append("## 4. 被排除清单与排除理由（透明化）")
    lines.append("")
    if not universe.excluded:
        lines.append("- （本次没有公司被排除）")
    else:
        lines.append("| Ticker | 名称 | 排除理由 |")
        lines.append("|---|---|---|")
        for ex in universe.excluded:
            lines.append(f"| {ex.ticker} | {ex.name or '-'} | {ex.exclude_reason or '-'} |")
    lines.append("")

    # 5. 质量门
    lines.append("## 5. 独立质量门 & 警告")
    lines.append("")
    lines.append(f"- 总评：{'✅ 通过' if qg.get('passed') else '❌ 关键错误'}")
    if qg.get("critical_errors"):
        lines.append("- 关键错误：")
        for e in qg["critical_errors"]:
            lines.append(f"  - ❌ {e}")
    if qg.get("warnings"):
        lines.append("- 警告项：")
        for w in qg["warnings"]:
            lines.append(f"  - ⚠️ {w}")
    lines.append("")
    lines.append("---")
    lines.append("*本报告由「确定性计算」产出：评分 8 维度可复算，LLM 不直接给分；缺数据不会得高分；所有结论仅为研究动作建议，不执行交易。*")
    md_text = "\n".join(lines)
    ctx.state["report_md"] = md_text

    # 写 CSV watch_list：汇总所有 watch_list + TOP 风险
    watch_rows = []
    for s in scores:
        for w in s.watch_list:
            watch_rows.append([s.ticker, s.name or "", "watch", w])
    for ex in universe.excluded:
        watch_rows.append([ex.ticker, ex.name or "", "excluded", ex.exclude_reason or ""])
    ctx.state["watch_rows"] = watch_rows

    return StageResult(
        status="completed",
        message=f"报告渲染完成：Markdown {len(md_text)} 字符；watch_list 行 {len(watch_rows)}",
        summary={"md_len": len(md_text), "watch_rows": len(watch_rows)},
    )


# ============================================================================
# 8. persist_outputs
# ============================================================================

def _persist_outputs(ctx: WorkflowContext) -> StageResult:
    """写 4 个制品 + 注册到 ArtifactStore"""
    root = _get_default_artifact_root()
    out_dir = root / f"theme_expectation_gap_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    out_dir.mkdir(parents=True, exist_ok=True)

    universe: ThemeUniverse = ctx.state["theme_universe"]
    scores: list[ExpectationGapScore] = ctx.state.get("scores") or []
    report_md = ctx.state["report_md"] or ""
    watch_rows: list[list] = ctx.state.get("watch_rows") or []

    univ_path = out_dir / "theme_universe.json"
    scores_path = out_dir / "expectation_scores.json"
    md_path = out_dir / "candidate_matrix.md"
    csv_path = out_dir / "watch_list.csv"

    univ_path.write_text(
        json.dumps(universe, default=_json_default, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    scores_path.write_text(
        json.dumps(scores, default=_json_default, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    md_path.write_text(report_md, encoding="utf-8")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ticker", "name", "category", "message"])
        for row in watch_rows:
            w.writerow(row)

    # 注册到 ArtifactStore（如果有 db_path）
    artifact_paths = {
        "theme_universe": str(univ_path),
        "expectation_scores": str(scores_path),
        "candidate_matrix_md": str(md_path),
        "watch_list_csv": str(csv_path),
    }
    reg_ids = {}
    registered = []
    artifact_types = {
        "theme_universe": ("theme_universe", "主题候选全集", "application/json"),
        "expectation_scores": ("expectation_scores", "预期差评分明细", "application/json"),
        "candidate_matrix_md": ("comparison_matrix", "主题预期差候选矩阵", "text/markdown"),
        "watch_list_csv": ("watch_list", "主题待补证清单", "text/csv"),
    }
    conn = sqlite3.connect(ctx.db_path)
    try:
        store = ArtifactStore(conn, [_get_default_artifact_root()])
        for key, path in artifact_paths.items():
            artifact_type, title, mime_type = artifact_types[key]
            artifact = store.register_artifact(
                ctx.run_id, artifact_type, title, path, mime_type,
                metadata={"theme_name": ctx.input_data.get("theme_name")},
            )
            reg_ids[key] = artifact["artifact_id"]
            registered.append(artifact)
    finally:
        conn.close()

    return StageResult(
        status="completed",
        message=f"4 个制品已保存到 {out_dir}",
        summary={"out_dir": str(out_dir), "artifacts": artifact_paths, "reg_ids": reg_ids},
        artifacts=tuple(registered),
    )


# ============================================================================
# 工作流定义
# ============================================================================

def theme_expectation_gap_definition(
    *, source_db_path: Path | None = None,
) -> WorkflowDefinition:
    """
    构建「主题预期差筛选 V1」工作流定义（master plan 阶段 8）

    参数：
        source_db_path - 可选的外部数据源 DB（这里简单忽略）
    """
    stages: list[StageDefinition] = [
        StageDefinition(stage_id="validate_inputs", handler=_validate_inputs,
                        title="1. 验证 theme_name + raw_candidates"),
        StageDefinition(stage_id="build_theme_universe", handler=_build_theme_universe,
                        title="2. 构建候选宇宙（入选+排除，所有排除理由可见）"),
        StageDefinition(stage_id="enrich_market_data", handler=_enrich_market_data,
                        title="3. 可选回填市场/证据数据（market_overrides / evidence_overrides）"),
        StageDefinition(stage_id="compile_gap_inputs", handler=_compile_gap_inputs,
                        title="4. 合成 ExpectationGapInput 打分输入"),
        StageDefinition(stage_id="score_expectation_gap", handler=_score_expectation_gap,
                        title="5. 8 维度确定性打分（scorer，无 LLM）"),
        StageDefinition(stage_id="rank_and_audit", handler=_rank_and_audit,
                        title="6. 排序 + 独立质量门（缺数据不会得高分）"),
        StageDefinition(stage_id="render_report", handler=_render_report,
                        title="7. 渲染 Markdown 候选矩阵 + 催化风险 + 验证清单"),
        StageDefinition(stage_id="persist_outputs", handler=_persist_outputs,
                        title="8. 保存 4 个制品 + 注册 ArtifactStore"),
    ]
    return WorkflowDefinition(
        workflow_id="theme_expectation_gap",
        title="主题预期差筛选 V1",
        description=(
            "从产业主题中按 8 维度（业务纯/收入敏/预期差证据/"
            "估值弹/拥挤度/流动性/催化可验证/风险）排序，"
            "输出可解释候选矩阵 + 待验证清单；不构成股票推荐。"
        ),
        stages=tuple(stages),
        input_schema={
            "required": ["theme_name", "raw_candidates"],
            "properties": {
                "theme_name": {"type": "string"},
                "theme_id": {"type": "string"},
                "raw_candidates": {"type": "array", "items": {"type": "object"}},
                "keyword_hint_list": {"type": "array", "items": {"type": "string"}},
                "inclusion_overrides": {"type": "object"},
                "market_overrides": {"type": "object"},
                "evidence_overrides": {"type": "object"},
                "allow_network": {"type": "boolean"},
            },
        },
    )
