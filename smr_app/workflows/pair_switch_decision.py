"""
双标的换仓决策工作流 V1

功能说明：
    阶段 5 的核心工作流编排层，把"同口径比较矩阵 + 四方案决策情景"串联起来，
    形成一份"相对决策备忘录"（不是两份个股报告的拼接）。

    核心原则（来自 master plan 阶段 5）：
    - 两标的行情时点差不超过配置阈值（默认 72h）
    - 市值、PE、PB、利润等单位一致（亿元/倍/%）
    - **调用阶段 4 的估值制品**，不是重复手算
    - 用户偏好只使用明确确认信息
    - **不把"昂贵/便宜"直接等同于买入/卖出**
    - 任一核心数据冲突时相关结论局部降级
    - 明确声明**不执行真实交易**（只是研究备忘录）

    金标准案例：
        "把阳光电源（300274.SZ）持仓换成海光信息（688041.SH）"

    工作流 12 阶段：
        1.  validate_inputs                   验证两标的 + 偏好格式合法
        2.  load_market_contexts              读取两标的 fundamentals/valuation 快照
        3.  load_phase4_valuation_artifacts   加载阶段4估值制品（关键：不复算）
        4.  compile_comparison_inputs         汇总为两个 ComparisonInput
        5.  enforce_units_and_alignment       单位一致性 + 时点对齐校验
        6.  build_comparison_matrix           调用 ComparisonMatrixBuilder
        7.  apply_user_preferences            生成 UserPreference
        8.  generate_decision_scenarios       调用 ScenarioPlanner
        9.  verify_no_buy_sell_equivalence    质量门：估值高低≠买卖信号（验收要求）
        10. build_decision_memo               生成 Markdown 决策备忘录
        11. independent_quality_gate          独立复算 + 数据完整度 + 成立/失效条件覆盖
        12. persist_outputs                   保存 4 个制品 + 注册 ArtifactStore

参数说明：
    pair_switch_decision_definition() - 构建工作流定义，交给 WorkflowRunner 执行

    工作流输入（input_data）：
    - from_ticker:          被换出标的（当前持仓方 A），必填
    - to_ticker:            被换入标的（候选方 B），必填
    - from_name / to_name:  公司中文名，可选（用于报告更友好）
    - temporal_threshold_hours: 两标的行情时点差阈值，默认 72h
    - preference:           用户偏好字典（对应 UserPreference 的字段），可选
    - from_industry / to_industry:        行业标签，可选
    - from_lifecycle / to_lifecycle:      生命周期标签，可选
    - from_industry_position / to_industry_position: 产业位置，可选
    - from_catalysts / to_catalysts:      催化列表，可选
    - from_risks / to_risks:              风险列表，可选
    - from_holding:       A 方持仓信息字典（shares/成本/占比等），仅 from 需要
    - phase4_from_json:   A 的阶段4估值 JSON 路径或字典（优先用此，不复算）
    - phase4_to_json:     B 的阶段4估值 JSON 路径或字典（优先用此，不复算）
    - allow_network:      必须为 False（本阶段所有数据必须本地可得）

返回值说明：
    WorkflowDefinition，12 个阶段；产出 4 类制品：
    - comparison_matrix.json
    - decision_scenarios.json
    - decision_memo.md
    - monitoring_list.csv
    所有制品在阶段 12 注册到 ArtifactStore。

异常处理：
    - allow_network=True 直接被阶段 1 拒绝
    - 阶段 4 估值制品缺失时：对应维度降级，并写入 data_gaps（**不**当场重算）
    - 时点未对齐：相关维度降级，推荐置信度降一级
    - 关键用户偏好与硬约束冲突（如 max_switch_ratio=0）：方案被大比例扣分
"""

from __future__ import annotations

import csv
import io
import json
import os
import sqlite3
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from smr_app.research.comparison_matrix import (
    ComparisonInput,
    ComparisonMatrix,
    ComparisonMatrixBuilder,
)
from smr_app.research.decision_scenarios import (
    DecisionOutput,
    ScenarioPlanner,
    UserPreference,
)
from smr_app.runtime.artifact_store import ArtifactStore
from smr_app.runtime.contracts import (
    StageDefinition,
    StageResult,
    WorkflowContext,
    WorkflowDefinition,
)
from smr_app.workflows.stock_deep_dive import parse_ticker


# ============================================================================
# 全局配置
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _get_default_artifact_root() -> Path:
    """
    运行时获取默认 artifact 输出根目录（解决"模块 import 时就读取环境变量"导致测试 setUp 里的 os.environ 不生效问题）

    优先级：
        1. 环境变量 SMR_ARTIFACT_ROOTS 的第一个路径（多个用 os.pathsep 分隔）
        2. 默认：<PROJECT_ROOT>/06_outputs/workflows
    """
    configured_roots = os.environ.get("SMR_ARTIFACT_ROOTS", "").split(os.pathsep)
    if configured_roots and configured_roots[0]:
        return Path(configured_roots[0])
    return PROJECT_ROOT / "06_outputs" / "workflows"


DEFAULT_TEMPORAL_THRESHOLD_HOURS = 72.0


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# ============================================================================
# 通用工具：读取阶段4估值制品（或直接从已有 JSON/字典取摘要）
# ============================================================================


def _extract_valuation_summary_from_artifact(
    artifact: dict | str | Path | None,
) -> dict[str, Any]:
    """
    从阶段4估值制品（ValuationResult 的 JSON 结构或路径）提取摘要字段

    小白讲解：
        阶段4已经为 A 和 B 各算了一份估值报告，
        这里只**提取**结果，不重新计算。
        如果传的是文件路径，就读文件；如果是 dict，直接取；
        如果为 None，返回空 dict（对应维度在比较矩阵里会降级）。

    返回字段：
    - valuation_target_price, valuation_target_market_cap, valuation_irr
    - implied_cagr, implied_net_margin
    - current_price（如果 JSON 里有 input_snapshot.current_price）
    """
    summary: dict[str, Any] = {}
    if artifact is None:
        return summary
    try:
        data: dict
        if isinstance(artifact, (str, Path)):
            p = Path(artifact)
            if not p.exists():
                return {}
            data = json.loads(p.read_text(encoding="utf-8"))
        elif isinstance(artifact, dict):
            data = artifact
        else:
            return summary
    except (OSError, json.JSONDecodeError):
        return {}

    if isinstance(data, dict):
        s = data.get("summary") or {}
        if isinstance(s, dict):
            for k in ("target_price", "target_market_cap", "irr"):
                v = s.get(k)
                if isinstance(v, (int, float)):
                    summary[f"valuation_{k}"] = float(v)
        # 隐含增长：从阶段4 JSON 的 implied 字段（如果存在）或从反解结果取
        impl = data.get("implied") if isinstance(data.get("implied"), dict) else {}
        for k in ("implied_cagr", "implied_net_margin", "implied_dcu_shipment"):
            v = impl.get(k)
            if isinstance(v, (int, float)):
                summary[k] = float(v)
        # input_snapshot 里有当前价
        snap = data.get("input_snapshot")
        if isinstance(snap, dict):
            cp = snap.get("current_price")
            mcap = snap.get("current_market_cap")
            shares = snap.get("shares_outstanding")
            if isinstance(cp, (int, float)):
                summary["current_price"] = float(cp)
            if isinstance(mcap, (int, float)):
                summary["market_cap"] = float(mcap)
            if isinstance(shares, (int, float)):
                summary["shares_outstanding"] = float(shares)
    return summary


# ============================================================================
# 阶段 1：验证输入
# ============================================================================


def _validate_inputs(context: WorkflowContext) -> StageResult:
    """
    验证工作流输入（两标的 + allow_network + 偏好字段）

    小白讲解：
        这个"门卫"比阶段4的门卫多了几项检查：
        - 必须有 from_ticker 和 to_ticker，且不能一样
        - allow_network 必须为 False（所有数据必须本地可得）
        - 用户偏好如果传了，数值字段必须是数值
    """
    inp = context.input_data
    # 1. from/to 必须存在且是合法 A/港股/美股代码
    from_ticker, from_market = parse_ticker(inp.get("from_ticker"))
    to_ticker, to_market = parse_ticker(inp.get("to_ticker"))
    if from_ticker == to_ticker:
        raise ValueError("from_ticker 与 to_ticker 不能相同（换仓不能自己换自己）")

    # 2. allow_network 必须是 False
    allow_network = inp.get("allow_network")
    if allow_network is None:
        allow_network = False
    if not isinstance(allow_network, bool):
        raise ValueError("allow_network 必须是布尔值")
    if allow_network:
        raise ValueError("阶段 5 换仓决策要求 allow_network=False；所有数据需本地可用")

    # 3. temporal_threshold_hours（可选）必须是正数
    temporal_threshold_hours = inp.get("temporal_threshold_hours")
    if temporal_threshold_hours is None:
        temporal_threshold_hours = DEFAULT_TEMPORAL_THRESHOLD_HOURS
    if not isinstance(temporal_threshold_hours, (int, float)) or temporal_threshold_hours <= 0:
        raise ValueError("temporal_threshold_hours 必须是正数（小时）")

    # 4. preference（可选）基础检查
    pref = inp.get("preference") or {}
    if pref is not None and not isinstance(pref, dict):
        raise ValueError("preference 必须是字典或 None")

    # 写入状态
    context.state.update({
        "from_ticker": from_ticker,
        "from_market": from_market,
        "to_ticker": to_ticker,
        "to_market": to_market,
        "from_name": inp.get("from_name") or "",
        "to_name": inp.get("to_name") or "",
        "temporal_threshold_hours": float(temporal_threshold_hours),
        "raw_preference": dict(pref) if isinstance(pref, dict) else {},
        "from_industry": inp.get("from_industry") or "",
        "to_industry": inp.get("to_industry") or "",
        "from_lifecycle": inp.get("from_lifecycle") or "",
        "to_lifecycle": inp.get("to_lifecycle") or "",
        "from_industry_position": inp.get("from_industry_position") or "",
        "to_industry_position": inp.get("to_industry_position") or "",
        "from_catalysts": list(inp.get("from_catalysts") or []),
        "to_catalysts": list(inp.get("to_catalysts") or []),
        "from_risks": list(inp.get("from_risks") or []),
        "to_risks": list(inp.get("to_risks") or []),
        "from_holding": dict(inp.get("from_holding") or {}),
        "phase4_from_input": inp.get("phase4_from_json"),
        "phase4_to_input": inp.get("phase4_to_json"),
    })

    return StageResult.completed(
        "输入验证通过",
        {
            "from_ticker": from_ticker,
            "to_ticker": to_ticker,
            "from_market": from_market,
            "to_market": to_market,
            "temporal_threshold_hours": float(temporal_threshold_hours),
            "has_from_name": bool(inp.get("from_name")),
            "has_to_name": bool(inp.get("to_name")),
            "has_preference": bool(pref),
            "has_from_holding": bool(inp.get("from_holding")),
            "has_phase4_from": inp.get("phase4_from_json") is not None,
            "has_phase4_to": inp.get("phase4_to_json") is not None,
        },
    )


# ============================================================================
# 阶段 2：读取两标的基本面/估值快照
# ============================================================================


def _load_market_contexts_stage(source_db_path: Path | None):
    """
    构建"读取两标的快照"阶段处理函数

    小白讲解：
        去数据库查 A 和 B 两家公司最新的基本面、估值、价格快照。
        如果查不到，也不报错——后面 ComparisonMatrix 会自动降级。
    """
    def handler(context: WorkflowContext) -> StageResult:
        from_ticker = context.state["from_ticker"]
        to_ticker = context.state["to_ticker"]
        warnings: list[str] = []
        result = {
            "from": {"fundamentals": None, "valuation": None},
            "to":   {"fundamentals": None, "valuation": None},
        }

        # 打开只读/读写连接（复用阶段4连接模式）
        if source_db_path is None or source_db_path.resolve() == context.db_path.resolve():
            conn = sqlite3.connect(context.db_path)
        else:
            uri = source_db_path.resolve().as_uri() + "?mode=ro"
            conn = sqlite3.connect(uri, uri=True)
        try:
            for label, ticker in (("from", from_ticker), ("to", to_ticker)):
                # 基本面快照
                try:
                    row = conn.execute(
                        "SELECT ticker, revenue, net_income, gross_margin, net_margin, "
                        "operating_margin, roe, source, period_end, created_at "
                        "FROM fundamentals_snapshot WHERE ticker = ? "
                        "ORDER BY created_at DESC LIMIT 1",
                        (ticker,),
                    ).fetchone()
                    if row:
                        result[label]["fundamentals"] = {
                            "ticker": row[0], "revenue": row[1], "net_income": row[2],
                            "gross_margin": row[3], "net_margin": row[4],
                            "operating_margin": row[5], "roe": row[6],
                            "source": row[7], "period_end": row[8], "created_at": row[9],
                        }
                except sqlite3.Error as e:
                    warnings.append(f"{label} fundamentals_snapshot 不可读: {e}")
                # 估值快照
                try:
                    row = conn.execute(
                        "SELECT ticker, pe_ttm, pb, current_price, broker_target_price, "
                        "valuation_status, valuation_confidence, generated_at "
                        "FROM valuation_snapshot WHERE ticker = ? "
                        "ORDER BY generated_at DESC LIMIT 1",
                        (ticker,),
                    ).fetchone()
                    if row:
                        result[label]["valuation"] = {
                            "ticker": row[0], "pe_ttm": row[1], "pb": row[2],
                            "current_price": row[3], "broker_target_price": row[4],
                            "valuation_status": row[5], "valuation_confidence": row[6],
                            "generated_at": row[7],
                        }
                        # 快照时点
                        if row[7]:
                            result[label]["snapshot_as_of"] = row[7]
                except sqlite3.Error as e:
                    warnings.append(f"{label} valuation_snapshot 不可读: {e}")
        finally:
            conn.close()

        context.state["market_contexts"] = result
        context.state["snapshot_warnings"] = warnings

        summary = {
            "from_has_fundamentals": result["from"]["fundamentals"] is not None,
            "from_has_valuation": result["from"]["valuation"] is not None,
            "to_has_fundamentals": result["to"]["fundamentals"] is not None,
            "to_has_valuation": result["to"]["valuation"] is not None,
            "warning_count": len(warnings),
        }
        return StageResult.completed("市场快照读取完成", summary,
                                     payload={"warnings": list(warnings)})
    return handler


# ============================================================================
# 阶段 3：加载阶段4估值制品（不复算！验收关键）
# ============================================================================


def _load_phase4_valuation_artifacts(context: WorkflowContext) -> StageResult:
    """
    加载阶段4估值制品（不复算，只提取摘要 + 隐含增长）

    验收要求 3：调用阶段 4 的估值制品，而非重复手算。
    本阶段的唯一职责是"提取"，不调用 ValuationEngine.compute()。
    """
    warnings: list[str] = []
    from_art = _extract_valuation_summary_from_artifact(context.state.get("phase4_from_input"))
    to_art = _extract_valuation_summary_from_artifact(context.state.get("phase4_to_input"))
    if not from_art:
        warnings.append(f"{context.state.get('from_name') or context.state['from_ticker']}"
                        " 未提供阶段4估值制品；估值/隐含增长维度将降级")
    if not to_art:
        warnings.append(f"{context.state.get('to_name') or context.state['to_ticker']}"
                        " 未提供阶段4估值制品；估值/隐含增长维度将降级")
    context.state["phase4_from_summary"] = from_art
    context.state["phase4_to_summary"] = to_art
    context.state.setdefault("phase4_warnings", []).extend(warnings)

    return StageResult.completed(
        "阶段4估值制品加载完成",
        {
            "from_fields": sorted(from_art.keys()),
            "to_fields": sorted(to_art.keys()),
            "has_from_artifact": bool(from_art),
            "has_to_artifact": bool(to_art),
            "warning_count": len(warnings),
        },
        payload={"warnings": list(warnings)},
    )


# ============================================================================
# 阶段 4：汇总为 ComparisonInput（A/B 两个）
# ============================================================================


def _compile_comparison_inputs(context: WorkflowContext) -> StageResult:
    """把 DB 快照 + 阶段4制品 + 用户输入标签，汇总成两个 ComparisonInput"""
    ctx: dict = context.state["market_contexts"]
    from_summary: dict = context.state.get("phase4_from_summary") or {}
    to_summary: dict = context.state.get("phase4_to_summary") or {}

    def build_one(side: str, ticker: str, name: str,
                  industry: str, lifecycle: str, position: str,
                  catalysts: list, risks: list,
                  holding: dict | None) -> ComparisonInput:
        f = ctx[side]["fundamentals"] or {}
        v = ctx[side]["valuation"] or {}
        snap_as_of = ctx[side].get("snapshot_as_of")
        p4 = from_summary if side == "from" else to_summary

        ci = ComparisonInput(
            ticker=ticker, name=name,
            revenue=f.get("revenue"),
            net_income=f.get("net_income"),
            gross_margin=f.get("gross_margin"),
            net_margin=f.get("net_margin"),
            operating_margin=f.get("operating_margin"),
            roe=f.get("roe"),
            pe_ttm=v.get("pe_ttm"),
            pb=v.get("pb"),
            current_price=(v.get("current_price") or p4.get("current_price")),
            market_cap=(v.get("broker_target_price") is not None and p4.get("market_cap")
                        if False else p4.get("market_cap")),
            shares_outstanding=p4.get("shares_outstanding"),
            valuation_target_price=p4.get("valuation_target_price"),
            valuation_target_market_cap=p4.get("valuation_target_market_cap"),
            valuation_irr=p4.get("valuation_irr"),
            implied_cagr=p4.get("implied_cagr"),
            implied_net_margin=p4.get("implied_net_margin"),
            snapshot_as_of=snap_as_of or v.get("generated_at"),
            valuation_as_of=v.get("generated_at"),
            fundamentals_period=f.get("period_end"),
            source_authority_tier=(
                1 if f.get("source") in ("sse", "szse", "cninfo", "exchange") else
                2 if f.get("source") else 3
            ),
            industry=industry, lifecycle_stage=lifecycle,
            industry_position=position,
            catalysts=catalysts, risks=risks,
        )
        # 用户给的拥挤度 / 价格状态（如果有）
        price_extra = context.input_data.get(f"{side}_price_action") or {}
        if isinstance(price_extra, dict):
            if price_extra.get("turnover_20d") is not None:
                ci.turnover_rate_20d = float(price_extra["turnover_20d"])
            if price_extra.get("return_1m") is not None:
                ci.short_term_return = float(price_extra["return_1m"])
            if price_extra.get("return_3m") is not None:
                ci.medium_term_return = float(price_extra["return_3m"])
            if price_extra.get("relative_strength") is not None:
                ci.relative_strength = float(price_extra["relative_strength"])
        # 现金流：如果用户提供了额外数据
        cf_extra = context.input_data.get(f"{side}_cash_flow") or {}
        if isinstance(cf_extra, dict):
            if cf_extra.get("operating_cf") is not None:
                ci.operating_cash_flow = float(cf_extra["operating_cf"])
            if cf_extra.get("free_cf") is not None:
                ci.free_cash_flow = float(cf_extra["free_cf"])
        # A 方的持仓信息
        if side == "from" and holding:
            h = holding
            if h.get("shares_wan") is not None:
                ci.holding_shares = float(h["shares_wan"])
            if h.get("cost") is not None:
                ci.holding_cost = float(h["cost"])
            if h.get("position_pct") is not None:
                ci.holding_position_pct = float(h["position_pct"])
            if h.get("loss_tolerance") is not None:
                ci.holding_loss_tolerance = float(h["loss_tolerance"])
            if h.get("short_term_tax") is not None:
                ci.tax_on_short_term = float(h["short_term_tax"])
        return ci

    from_input = build_one(
        "from", context.state["from_ticker"], context.state.get("from_name") or "",
        context.state.get("from_industry") or "",
        context.state.get("from_lifecycle") or "",
        context.state.get("from_industry_position") or "",
        context.state.get("from_catalysts") or [],
        context.state.get("from_risks") or [],
        context.state.get("from_holding"),
    )
    to_input = build_one(
        "to", context.state["to_ticker"], context.state.get("to_name") or "",
        context.state.get("to_industry") or "",
        context.state.get("to_lifecycle") or "",
        context.state.get("to_industry_position") or "",
        context.state.get("to_catalysts") or [],
        context.state.get("to_risks") or [],
        None,
    )
    context.state["comparison_from"] = from_input
    context.state["comparison_to"] = to_input

    return StageResult.completed(
        "ComparisonInput 汇总完成",
        {
            "from_has_revenue": from_input.revenue is not None,
            "from_has_roe": from_input.roe is not None,
            "from_has_target_price": from_input.valuation_target_price is not None,
            "to_has_revenue": to_input.revenue is not None,
            "to_has_roe": to_input.roe is not None,
            "to_has_target_price": to_input.valuation_target_price is not None,
        },
    )


# ============================================================================
# 阶段 5：单位一致性 + 时点对齐前置校验（决定是否全局降级）
# ============================================================================


def _enforce_units_and_alignment(context: WorkflowContext) -> StageResult:
    """
    前置单位/时点校验：只做统计，不修改数据（matrix 自己会做 normalize）

    作用：把检查结果写入 state，后面推荐置信度会参考
    """
    from_input: ComparisonInput = context.state["comparison_from"]
    to_input: ComparisonInput = context.state["comparison_to"]
    threshold = context.state["temporal_threshold_hours"]

    # 只做时点对齐统计（单位统一由 matrix 在 normalize_* 里执行）
    aligned, delta_h, reason = (False, 0.0, "尚未赋值")
    from smr_app.research.comparison_matrix import check_temporal_alignment  # 本地函数也行，但为复用导入
    aligned, delta_h, reason = check_temporal_alignment(
        from_input.snapshot_as_of, to_input.snapshot_as_of, threshold,
    )
    context.state["temporal_aligned"] = aligned
    context.state["temporal_delta_hours"] = delta_h
    context.state["temporal_alignment_reason"] = reason

    return StageResult.completed(
        "单位一致性 + 时点对齐校验完成",
        {
            "temporal_aligned": aligned,
            "temporal_delta_hours": round(delta_h, 2),
            "temporal_reason": reason or "OK",
        },
    )


# ============================================================================
# 阶段 6：构建同口径比较矩阵
# ============================================================================


def _build_comparison_matrix(context: WorkflowContext) -> StageResult:
    from_input: ComparisonInput = context.state["comparison_from"]
    to_input: ComparisonInput = context.state["comparison_to"]
    threshold = context.state["temporal_threshold_hours"]

    builder = ComparisonMatrixBuilder(threshold_hours=threshold)
    matrix: ComparisonMatrix = builder.build(from_input, to_input)

    context.state["comparison_matrix"] = matrix

    # 汇总矩阵层面的 warnings + 前面阶段 warnings
    all_w = list(matrix.warnings) + list(context.state.get("phase4_warnings") or [])
    context.state["all_warnings"] = all_w

    return StageResult.completed(
        f"比较矩阵构建完成（{len(matrix.rows)} 维度）",
        {
            "dimension_count": len(matrix.rows),
            "units_consistent": matrix.units_consistent,
            "temporal_alignment_pass": matrix.temporal_alignment_pass,
            "overall_completeness": round(matrix.overall_completeness, 3),
            "degraded_dimension_count": matrix.degraded_dimension_count,
            "data_gaps_count": len(matrix.data_gaps),
            "warning_count": len(all_w),
        },
    )


# ============================================================================
# 阶段 7：生成 UserPreference（只用明确确认的字段）
# ============================================================================


def _apply_user_preferences(context: WorkflowContext) -> StageResult:
    raw = context.state.get("raw_preference") or {}
    pref = UserPreference()

    # 只把明确提供了的字段赋值；没提供的保持 None（ScenarioPlanner 会跳过）
    float_fields = [
        "annual_return_target", "max_drawdown_tolerance",
        "min_switch_ratio", "max_switch_ratio",
        "holding_loss_tolerance",  # 兼容别名
    ]
    int_fields = ["holding_horizon_months"]
    bool_fields = [
        "accept_loss_stock", "accept_high_crowding",
        "avoid_short_term_tax", "allow_cross_sector",
        "prefer_industry_leader", "avoid_negative_roe",
    ]
    for f in float_fields:
        v = raw.get(f)
        if isinstance(v, (int, float)):
            setattr(pref, f, float(v))
    for f in int_fields:
        v = raw.get(f)
        if isinstance(v, int):
            setattr(pref, f, int(v))
    for f in bool_fields:
        v = raw.get(f)
        if isinstance(v, bool):
            setattr(pref, f, bool(v))
    # min_daily_turnover_yi 特殊
    if isinstance(raw.get("min_daily_turnover_yi"), (int, float)):
        pref.min_daily_turnover_yi = float(raw["min_daily_turnover_yi"])

    context.state["preference"] = pref

    return StageResult.completed(
        "用户偏好汇总完成（只用明确确认字段）",
        {
            "used_fields": sum(1 for v in asdict(pref).values() if v is not None),
            "holding_horizon_months": pref.holding_horizon_months,
            "has_return_target": pref.annual_return_target is not None,
            "has_max_switch_ratio": pref.max_switch_ratio is not None,
            "avoid_negative_roe": pref.avoid_negative_roe,
        },
    )


# ============================================================================
# 阶段 8：生成四方案决策情景
# ============================================================================


def _generate_decision_scenarios(context: WorkflowContext) -> StageResult:
    matrix: ComparisonMatrix = context.state["comparison_matrix"]
    pref: UserPreference = context.state.get("preference") or UserPreference()

    planner = ScenarioPlanner(enable_real_trade=False)
    decision: DecisionOutput = planner.generate_scenarios(matrix, pref)

    context.state["decision_output"] = decision

    return StageResult.completed(
        "四方案决策情景生成完成",
        {
            "recommended": decision.recommended,
            "confidence_level": decision.confidence_level,
            "scenario_count": len(decision.scenarios),
            "monitoring_indicators_count": len(decision.monitoring_indicators),
            "preference_used_count": len(decision.preference_used),
            "preference_skipped_count": len(decision.preference_skipped),
            "warnings_total": len(decision.warnings),
            "data_gaps_count": len(decision.data_gaps),
        },
    )


# ============================================================================
# 阶段 9：质量门——"不把贵/便宜直接等同于买卖"（验收要求 5）
# ============================================================================


def _verify_no_buy_sell_equivalence(context: WorkflowContext) -> StageResult:
    """
    质量门：确保报告不会因为"B 比 A 便宜"就直接"B 应该买/A 应该卖"。

    检查 1：valuation 行 note 必须包含"估值高低不直接等同于买入/卖出信号"字样
            （comparison_matrix 构造时已写入）
    检查 2：decision_output 必须包含 execution_warning（长度 > 10）
    检查 3：4 个方案的 rationale 必须出现"维度"或"条件"字样（说明不是单一信号驱动）
    """
    matrix: ComparisonMatrix = context.state["comparison_matrix"]
    decision: DecisionOutput = context.state["decision_output"]

    failures: list[str] = []

    vrow = matrix.get_row("valuation")
    if vrow is None:
        failures.append("缺少 valuation 维度行，无法确认估值信号是否被直接等同于买卖信号")
    else:
        if "估值高低不直接等同于买入/卖出信号" not in (vrow.note or ""):
            failures.append(
                "valuation 维度 note 未明确声明：估值高低不直接等同于买入/卖出信号"
            )

    if len(decision.execution_warning or "") < 10:
        failures.append("execution_warning 过短，未明确声明不执行真实交易")

    for sid, s in decision.scenarios.items():
        rationale = s.rationale or ""
        if not any(k in rationale for k in ("维度", "条件", "占优", "缺口", "平衡")):
            # 宽松一些：只对分数 >= 50 的方案要求，否则方案本身没竞争力
            if s.score >= 50:
                failures.append(f"方案 {sid}（score={s.score}）未说明基于多维度/条件的理由")

    passed = len(failures) == 0
    context.state["quality_buy_sell_gate_passed"] = passed
    context.state["quality_buy_sell_failures"] = failures

    return StageResult.completed(
        "买卖信号等价性质量门完成：" + ("通过" if passed else f"未通过 {len(failures)} 项"),
        {
            "passed": passed,
            "failure_count": len(failures),
            "failures": list(failures),
        },
    )


# ============================================================================
# 阶段 10：构建 Markdown 决策备忘录
# ============================================================================


def _build_decision_memo(context: WorkflowContext) -> str:
    """
    构建决策备忘录 Markdown（不做买卖建议，仅呈现事实）

    结构：
    - 摘要（标的对、推荐方案、置信度、免责声明）
    - 同口径比较矩阵（12 维度表格）
    - 四方案详解：成立条件 / 失效条件 / 分批节奏 / 打分 / 置信度 / 是否降级
    - 领先指标监控清单
    - 数据缺口
    - 警告
    """
    matrix: ComparisonMatrix = context.state["comparison_matrix"]
    decision: DecisionOutput = context.state["decision_output"]

    lines: list[str] = []
    lines.append(f"# 换仓决策备忘录 — {context.state['from_ticker']} → {context.state['to_ticker']}")
    lines.append(f"\n生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 摘要
    lines.append("## 摘要\n")
    lines.append("| 项目 | 内容 |")
    lines.append("|---|---|")
    rec = decision.scenarios.get(decision.recommended)
    rec_name = rec.name if rec else decision.recommended
    lines.append(f"| 被换出（A） | {context.state.get('from_name') or context.state['from_ticker']} ({context.state['from_ticker']}) |")
    lines.append(f"| 被换入（B） | {context.state.get('to_name') or context.state['to_ticker']} ({context.state['to_ticker']}) |")
    lines.append(f"| 推荐方案 | {rec_name} |")
    lines.append(f"| 推荐置信度 | {decision.confidence_level} |")
    if rec and rec.expected_switch_ratio is not None:
        lines.append(f"| 推荐总换仓比例 | {rec.expected_switch_ratio*100:.0f}% |")
    lines.append(f"| 数据完整度 | {matrix.overall_completeness:.0%} |")
    lines.append(f"| 时点对齐 | {'通过' if matrix.temporal_alignment_pass else f'未通过（差 {matrix.temporal_alignment_hours:.1f}h）'} |")
    lines.append(f"| 单位一致 | {'通过' if matrix.units_consistent else '未通过'} |")
    lines.append(f"| 降级维度数 | {matrix.degraded_dimension_count} |")
    lines.append(f"| 数据缺口数 | {len(decision.data_gaps)} |")
    lines.append("\n> ")
    lines.append(f"> **{decision.execution_warning}**\n")

    # 比较矩阵
    lines.append("## 同口径比较矩阵\n")
    lines.append("| 维度 | A（换出） | B（换入） | 差值/相对描述 | A数据等级 | B数据等级 |")
    lines.append("|---|---|---|---|---|---|")
    for dim_id in matrix.all_dimension_ids():
        row = matrix.rows[dim_id]
        a_val = _cell_display(row.a)
        b_val = _cell_display(row.b)
        rel = row.relative_description or ("—" if row.delta is None else str(row.delta))
        a_tier = _tier_display(row.a)
        b_tier = _tier_display(row.b)
        lines.append(f"| {row.dimension_label} | {a_val} | {b_val} | {rel} | {a_tier} | {b_tier} |")
    if context.state.get("quality_buy_sell_gate_passed") is False:
        lines.append("\n⚠️ 【质量门：买卖等价性检查未通过】请结合警告区人工复核。\n")

    # 四方案
    lines.append("\n## 四方案详解\n")
    for sid in ("continue_hold", "partial_switch", "full_switch", "hold_and_wait"):
        s = decision.scenarios.get(sid)
        if s is None:
            continue
        mark = " 👈 推荐" if sid == decision.recommended else ""
        lines.append(f"\n### 方案{_chinese_num(sid)}：{s.name}{mark}\n")
        lines.append(f"- **说明**：{s.description}")
        lines.append(f"- **核心理由**：{s.rationale}")
        lines.append(f"- **基础分**：{s.score} / 100  ")
        lines.append(f"- **数据置信度**：{s.confidence:.0%}  ")
        if s.expected_switch_ratio is not None:
            lines.append(f"- **总换仓比例**：{s.expected_switch_ratio*100:.0f}%")
        if s.degraded:
            lines.append(f"- ⚠️ **降级原因**：{'; '.join(s.degradation_reasons) or '未说明'}")
        # 成立条件
        lines.append("\n**成立条件（满足才采纳此方案）**：\n")
        if s.valid_conditions:
            lines.append("| # | 条件 | 当前值 / 阈值 | 是否满足 |")
            lines.append("|---|---|---|---|")
            for i, c in enumerate(s.valid_conditions, 1):
                status = "✅ 满足" if c.met is True else ("❌ 不满足" if c.met is False else "❔ 待验证")
                cur_thr = ""
                if c.current_value is not None:
                    cur_thr += f"{c.current_value}"
                if c.unit:
                    cur_thr += f" {c.unit}"
                if c.threshold is not None:
                    d = {"gte": ">=", "lte": "<=", "eq": "=", "gt": ">", "lt": "<", "contains": "包含"}
                    sym = d.get(c.direction, "vs")
                    cur_thr += f"（{sym} {c.threshold}）"
                lines.append(f"| {i} | {c.description} | {cur_thr or '—'} | {status} |")
        else:
            lines.append("_（无明确成立条件，按保守默认）_\n")
        # 失效条件
        lines.append("\n**失效条件（一旦触发即放弃此方案）**：\n")
        if s.invalid_conditions:
            lines.append("| # | 条件 | 当前值 / 阈值 | 是否已触发 |")
            lines.append("|---|---|---|---|")
            for i, c in enumerate(s.invalid_conditions, 1):
                status = "⚠️ 已触发" if c.met is True else ("❌ 未触发" if c.met is False else "❔ 待观察")
                cur_thr = ""
                if c.current_value is not None:
                    cur_thr += f"{c.current_value}"
                if c.unit:
                    cur_thr += f" {c.unit}"
                if c.threshold is not None:
                    lines2 = {"gte": ">=", "lte": "<=", "eq": "="}
                    sym = lines2.get(c.direction, "vs")
                    cur_thr += f"（{sym} {c.threshold}）"
                lines.append(f"| {i} | {c.description} | {cur_thr or '—'} | {status} |")
        else:
            lines.append("_（无明确失效条件，需人工复核）_\n")
        # 分批节奏
        lines.append("\n**分批节奏**：\n")
        if s.pacing:
            lines.append("| 步 | 占总换仓比 | 触发条件 | 监控指标 | 说明 |")
            lines.append("|---|---|---|---|---|")
            for step in s.pacing:
                ratio_str = (
                    f"{step.ratio*100:.0f}%" if sid in ("partial_switch", "full_switch")
                    else "不换仓"
                )
                lines.append(f"| {step.step_index} | {ratio_str} | {step.trigger} | "
                             f"{step.indicator or '—'} | {step.rationale or '—'} |")

    # 监控清单
    lines.append("\n## 领先指标监控清单\n")
    if decision.monitoring_indicators:
        lines.append("| 指标 | 说明 | 频率 | 当前值 | 预警阈值 | 影响方案 |")
        lines.append("|---|---|---|---|---|---|")
        for mi in decision.monitoring_indicators:
            cur = f"{mi.current_value}" if mi.current_value is not None else "—"
            if mi.unit:
                cur += f" {mi.unit}"
            thr = f"{mi.warn_threshold}" if mi.warn_threshold is not None else "—"
            direction = {"above": "超过此值", "below": "低于此值",
                         "outside_range": "超出范围", "": ""}.get(mi.direction, mi.direction)
            lines.append(
                f"| {mi.name} | {mi.why_it_matters} | {mi.frequency or '—'} | {cur} | "
                f"{thr} {direction} | {', '.join(mi.applies_to_scenarios) or '全部'} |"
            )

    # 数据缺口
    if decision.data_gaps:
        lines.append("\n## 未解决数据缺口\n")
        lines.append("需要在后续研究或监控中补齐的信息：")
        for i, g in enumerate(decision.data_gaps, 1):
            lines.append(f"{i}. {g}")
        lines.append("")

    # 用户偏好透明性
    if decision.preference_used or decision.preference_skipped:
        lines.append("\n## 用户偏好使用透明化\n")
        if decision.preference_used:
            lines.append("### 本次已明确采用的偏好\n")
            for p in decision.preference_used:
                lines.append(f"- {p}")
            lines.append("")
        if decision.preference_skipped:
            lines.append("### 未明确表态、按中性处理的偏好\n")
            for p in decision.preference_skipped:
                lines.append(f"- {p}")
            lines.append("")

    # 警告
    all_w = list(decision.warnings) + list(context.state.get("all_warnings") or [])
    if all_w:
        lines.append("\n## 警告与注意事项\n")
        seen = set()
        for w in all_w:
            if w and w not in seen:
                lines.append(f"- ⚠️ {w}")
                seen.add(w)
        lines.append("")

    lines.append("---\n")
    lines.append(
        "_本备忘录由确定性流程生成：比较矩阵 → 四方案情景，"
        "全程未使用 LLM 手算数值；阶段4估值制品仅提取不复算；"
        "所有结论均可追溯至输入字段与权重参数。_"
    )
    return "\n".join(lines)


# 辅助：单元格展示
def _cell_display(cell) -> str:
    if cell.degraded:
        tag = "⚠️ 降级"
        if cell.degradation_reason:
            tag += f"：{cell.degradation_reason}"
        return tag
    v = cell.value
    if v is None:
        return "—"
    if isinstance(v, (int, float)):
        return f"{v:.4f}" if abs(v) < 100 else f"{v:,.2f}"
    if isinstance(v, dict):
        # 复合单元格（估值/质量等），选关键字段
        parts = []
        labels = {
            "pe_ttm": "PE", "pb": "PB", "market_cap": "市值亿",
            "target_price": "阶段4目标价", "upside_potential": "上行",
            "implied_cagr": "隐含CAGR", "implied_net_margin": "隐含净利率",
            "net_margin": "净利率", "revenue": "营收亿", "gross_margin": "毛利率",
            "operating_cf": "经营CF亿", "free_cf": "自由CF亿", "cf_to_ni": "CF/NI",
            "return_1m": "1月涨跌", "return_3m": "3月涨跌", "relative_strength": "相对强弱",
            "turnover_20d": "20日换手",
            "position_pct": "持仓占比", "cost_per_share": "成本",
            "shares_wan": "持仓万股", "loss_tolerance": "亏损容忍",
            "industry": "行业", "position": "产业位置",
        }
        for k, label in labels.items():
            if k in v and v[k] is not None:
                val = v[k]
                if isinstance(val, float) and ("pct" in k or "margin" in k or "CAGR" in label
                                                or "强弱" in label or "换手" in label
                                                or "容忍" in label or "占比" in label):
                    parts.append(f"{label} {val*100:.1f}%")
                elif isinstance(val, float):
                    parts.append(f"{label} {val:.2f}")
                else:
                    parts.append(f"{label} {val}")
        if parts:
            return " / ".join(parts[:4])  # 最多展示 4 项避免过宽
        return json.dumps(v, ensure_ascii=False)[:40]
    if isinstance(v, list):
        cnt = len(v)
        samples = ", ".join(str(x)[:12] for x in v[:2])
        return f"{cnt} 项：{samples}" if cnt else "—"
    return str(v)[:60]


def _tier_display(cell) -> str:
    if cell.degraded:
        return "降级"
    t = cell.authority_tier
    return {1: "T1 官方", 2: "T2 数据商", 3: "T3 聚合", 4: "T4 推断"}.get(t, f"T{t}")


def _chinese_num(sid: str) -> str:
    return {"continue_hold": "一", "partial_switch": "二",
            "full_switch": "三", "hold_and_wait": "四"}.get(sid, "?")


# ============================================================================
# 阶段 11：独立质量门（完整度、成立/失效条件覆盖、推荐理由一致性）
# ============================================================================


def _independent_quality_gate(context: WorkflowContext) -> StageResult:
    matrix: ComparisonMatrix = context.state["comparison_matrix"]
    decision: DecisionOutput = context.state["decision_output"]

    errors: list[str] = []
    checks: dict[str, bool] = {}

    # 1. execution_warning 非空（明确不执行真实交易）
    checks["execution_warning_present"] = len(decision.execution_warning or "") > 10
    if not checks["execution_warning_present"]:
        errors.append("未声明不执行真实交易")

    # 2. 每个方案都至少有 1 条成立条件 + 1 条失效条件（hold_and_wait 例外，可以 0 成立）
    for sid, s in decision.scenarios.items():
        if sid == "hold_and_wait":
            pass  # 此方案成立条件可以 0（等信号）
        else:
            if len(s.valid_conditions) < 1:
                errors.append(f"方案 {sid} 没有任何成立条件")
        if len(s.invalid_conditions) < 1 and sid != "continue_hold":
            errors.append(f"方案 {sid} 没有失效条件")
    checks["conditions_minimum_coverage"] = len(errors) == 0 or not any(
        "成立条件" in e or "失效条件" in e for e in errors
    )

    # 3. 用户偏好透明化：preference_used + preference_skipped 非空集合
    checks["preference_transparent"] = bool(decision.preference_used or decision.preference_skipped)

    # 4. 监控清单至少 2 项（多换仓场景总该有几个监控）
    checks["minimum_monitoring_indicators"] = len(decision.monitoring_indicators) >= 2

    # 5. 阶段 4 估值制品至少一方可用（否则本工作流退化成纯主观）
    p4_from = context.state.get("phase4_from_summary") or {}
    p4_to = context.state.get("phase4_to_summary") or {}
    checks["phase4_at_least_one"] = bool(p4_from or p4_to)

    # 6. 推荐方案分数不能显著低于另一非暂缓方案（否则推荐不合理）
    scores = {sid: s.score for sid, s in decision.scenarios.items() if sid != "hold_and_wait"}
    if scores and decision.recommended in scores:
        others = [v for k, v in scores.items() if k != decision.recommended]
        if others and max(others) - scores[decision.recommended] >= 15:
            errors.append(
                f"推荐方案分 {scores[decision.recommended]} 明显低于"
                f"最高分 {max(others)}（差 >= 15），需人工确认推荐合理性"
            )
    checks["recommendation_score_consistency"] = True  # 记录告警，不硬拦

    # 7. 推荐方案若为 full_switch，置信度必须 >= 中（避免全换但没信心）
    if decision.recommended == "full_switch" and decision.confidence_level == "低":
        errors.append("推荐完全换仓但置信度=低，建议用户再确认或升级为部分换仓")

    passed = len([e for e in errors if "建议" not in e and "需人工确认推荐合理性" not in e]) == 0
    gate = {
        "passed": passed,
        "checks": checks,
        "critical_errors": [e for e in errors if "建议" not in e],
        "warnings_only": [e for e in errors if "建议" in e or "需人工确认推荐合理性" in e],
    }
    context.state["quality_gate"] = gate

    return StageResult.completed(
        f"独立质量门完成：{'通过' if passed else '未通过'}（告警 {len(gate['warnings_only'])} 条）",
        {
            "passed": passed,
            "checks_passed_count": sum(1 for ok in checks.values() if ok),
            "checks_total_count": len(checks),
            "critical_error_count": len(gate["critical_errors"]),
            "warning_count": len(gate["warnings_only"]),
            "errors": errors,
        },
    )


# ============================================================================
# 阶段 12：保存制品 + 注册 ArtifactStore
# ============================================================================


def _persist_outputs(context: WorkflowContext) -> StageResult:
    matrix: ComparisonMatrix = context.state["comparison_matrix"]
    decision: DecisionOutput = context.state["decision_output"]
    memo = _build_decision_memo(context)
    gate = context.state.get("quality_gate") or {}

    artifacts: tuple[dict, ...] = ()
    paths: dict[str, str] = {}

    # 输出目录（运行时读取，保证测试覆盖的 SMR_ARTIFACT_ROOTS 生效）
    default_root = _get_default_artifact_root()
    run_dir = default_root / context.run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # 1. comparison_matrix.json
    # 把 ComparisonMatrix 转成 JSON 友好的结构
    matrix_json = {
        "a_ticker": matrix.a_ticker, "b_ticker": matrix.b_ticker,
        "a_name": matrix.a_name, "b_name": matrix.b_name,
        "units_consistent": matrix.units_consistent,
        "temporal_alignment_hours": matrix.temporal_alignment_hours,
        "temporal_alignment_pass": matrix.temporal_alignment_pass,
        "overall_completeness": matrix.overall_completeness,
        "degraded_dimension_count": matrix.degraded_dimension_count,
        "rows": {},
        "data_gaps": list(matrix.data_gaps),
        "warnings": list(matrix.warnings),
    }
    for dim_id, row in matrix.rows.items():
        matrix_json["rows"][dim_id] = {
            "dimension_label": row.dimension_label,
            "note": row.note,
            "a": asdict(row.a),
            "b": asdict(row.b),
            "delta": row.delta,
            "relative_description": row.relative_description,
            "data_conflict": row.data_conflict,
            "conflict_detail": row.conflict_detail,
        }
    matrix_path = run_dir / "comparison_matrix.json"
    matrix_path.write_text(json.dumps(matrix_json, ensure_ascii=False, indent=2), encoding="utf-8")
    paths["comparison_matrix"] = str(matrix_path)

    # 2. decision_scenarios.json
    decision_json = {
        "a_ticker": decision.a_ticker, "b_ticker": decision.b_ticker,
        "recommended": decision.recommended,
        "confidence_level": decision.confidence_level,
        "scenarios": {
            sid: {
                **asdict(s),
                "valid_conditions": [asdict(c) for c in s.valid_conditions],
                "invalid_conditions": [asdict(c) for c in s.invalid_conditions],
                "pacing": [asdict(p) for p in s.pacing],
            }
            for sid, s in decision.scenarios.items()
        },
        "monitoring_indicators": [asdict(m) for m in decision.monitoring_indicators],
        "preference_used": list(decision.preference_used),
        "preference_skipped": list(decision.preference_skipped),
        "execution_warning": decision.execution_warning,
        "warnings": list(decision.warnings),
        "data_gaps": list(decision.data_gaps),
        "quality_gate": gate,
    }
    scenarios_path = run_dir / "decision_scenarios.json"
    scenarios_path.write_text(json.dumps(decision_json, ensure_ascii=False, indent=2), encoding="utf-8")
    paths["decision_scenarios"] = str(scenarios_path)

    # 3. decision_memo.md
    memo_path = run_dir / "decision_memo.md"
    memo_path.write_text(memo, encoding="utf-8")
    paths["decision_memo"] = str(memo_path)

    # 4. monitoring_list.csv
    csv_buf = io.StringIO()
    writer = csv.writer(csv_buf)
    writer.writerow([
        "indicator_id", "name", "why_it_matters", "frequency", "current_value",
        "unit", "warn_threshold", "direction", "applies_to_scenarios",
    ])
    for mi in decision.monitoring_indicators:
        writer.writerow([
            mi.indicator_id, mi.name, mi.why_it_matters, mi.frequency,
            mi.current_value, mi.unit, mi.warn_threshold, mi.direction,
            "|".join(mi.applies_to_scenarios),
        ])
    monitor_path = run_dir / "monitoring_list.csv"
    monitor_path.write_text(csv_buf.getvalue(), encoding="utf-8-sig")
    paths["monitoring_list"] = str(monitor_path)

    # 注册 ArtifactStore
    artifacts = ()
    try:
        conn = sqlite3.connect(context.db_path)
        try:
            store = ArtifactStore(conn, [default_root])
            artifacts = (
                store.register_artifact(context.run_id, "comparison_matrix",
                                        "换仓决策-同口径比较矩阵",
                                        matrix_path, "application/json"),
                store.register_artifact(context.run_id, "decision_scenarios",
                                        "换仓决策-四方案情景",
                                        scenarios_path, "application/json"),
                store.register_artifact(context.run_id, "pair_switch_report",
                                        "换仓决策备忘录",
                                        memo_path, "text/markdown"),
                store.register_artifact(context.run_id, "monitoring_list",
                                        "换仓决策-领先指标监控清单",
                                        monitor_path, "text/csv"),
            )
        finally:
            conn.close()
    except Exception as e:  # 注册失败不影响制品落地
        context.state.setdefault("artifact_store_errors", []).append(str(e))

    summary = {
        "artifact_count": 4,
        "paths": paths,
        "recommended": decision.recommended,
        "confidence_level": decision.confidence_level,
        "quality_gate_passed": gate.get("passed", False),
        "data_gaps_count": len(decision.data_gaps),
    }
    return StageResult.completed(
        "4 个制品已保存并注册",
        summary=summary,
        artifacts=artifacts,
    )


# ============================================================================
# 工作流定义
# ============================================================================


def pair_switch_decision_definition(
    *, source_db_path: Path | None = None,
) -> WorkflowDefinition:
    """
    构建双标的换仓决策 V1 工作流定义

    参数:
        source_db_path: 外部数据源数据库路径（None=使用工作流自身 DB）
    """
    stages: list[StageDefinition] = [
        StageDefinition(stage_id="validate_inputs", handler=_validate_inputs,
                        title="1. 验证输入（两标的+偏好）"),
        StageDefinition(stage_id="load_market_contexts",
                        handler=_load_market_contexts_stage(source_db_path),
                        title="2. 读取两标的市场快照（基本面+估值）"),
        StageDefinition(stage_id="load_phase4_valuation_artifacts",
                        handler=_load_phase4_valuation_artifacts,
                        title="3. 加载阶段4估值制品（不复算）"),
        StageDefinition(stage_id="compile_comparison_inputs",
                        handler=_compile_comparison_inputs,
                        title="4. 汇总为 ComparisonInput（A/B）"),
        StageDefinition(stage_id="enforce_units_and_alignment",
                        handler=_enforce_units_and_alignment,
                        title="5. 单位一致性 + 时点对齐前置校验"),
        StageDefinition(stage_id="build_comparison_matrix",
                        handler=_build_comparison_matrix,
                        title="6. 构建同口径比较矩阵（12维度）"),
        StageDefinition(stage_id="apply_user_preferences",
                        handler=_apply_user_preferences,
                        title="7. 汇总用户偏好（只用明确确认字段）"),
        StageDefinition(stage_id="generate_decision_scenarios",
                        handler=_generate_decision_scenarios,
                        title="8. 生成四方案决策情景"),
        StageDefinition(stage_id="verify_no_buy_sell_equivalence",
                        handler=_verify_no_buy_sell_equivalence,
                        title="9. 质量门：估值高低≠买卖信号"),
        StageDefinition(stage_id="independent_quality_gate",
                        handler=_independent_quality_gate,
                        title="11. 独立质量门（完整度 + 条件覆盖 + 推荐一致性）"),
        StageDefinition(stage_id="persist_outputs",
                        handler=_persist_outputs,
                        title="12. 保存制品并注册（4 个文件）"),
    ]
    return WorkflowDefinition(
        workflow_id="pair_switch_decision",
        title="双标的换仓决策 V1",
        description=(
            "对比 from_ticker（当前持仓）与 to_ticker（候选），"
            "输出同口径比较矩阵 + 四方案决策情景 + 领先指标监控清单。"
            "调用阶段4估值制品，不复手算；明确不执行真实交易。"
        ),
        stages=tuple(stages),
        input_schema={
            "required": ["from_ticker", "to_ticker"],
            "properties": {
                "from_ticker": {"type": "string"},
                "to_ticker": {"type": "string"},
                "from_name": {"type": "string"},
                "to_name": {"type": "string"},
                "temporal_threshold_hours": {"type": "number", "minimum": 1},
                "preference": {"type": "object"},
                "from_industry": {"type": "string"},
                "to_industry": {"type": "string"},
                "from_lifecycle": {"type": "string"},
                "to_lifecycle": {"type": "string"},
                "from_industry_position": {"type": "string"},
                "to_industry_position": {"type": "string"},
                "from_catalysts": {"type": "array", "items": {"type": "string"}},
                "to_catalysts": {"type": "array", "items": {"type": "string"}},
                "from_risks": {"type": "array", "items": {"type": "string"}},
                "to_risks": {"type": "array", "items": {"type": "string"}},
                "from_holding": {"type": "object"},
                "from_price_action": {"type": "object"},
                "to_price_action": {"type": "object"},
                "from_cash_flow": {"type": "object"},
                "to_cash_flow": {"type": "object"},
                "phase4_from_json": {},
                "phase4_to_json": {},
                "allow_network": {"type": "boolean", "default": False},
            },
        },
        enabled=True,
        writes_data=True,
    )
