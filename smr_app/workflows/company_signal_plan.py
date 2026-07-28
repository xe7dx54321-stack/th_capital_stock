"""
公司信号计划 V1 工作流（company_signal_plan）

功能说明：
    阶段 7「公司信号计划 / 记忆持久化」的第二个工作流。
    输入：标的（ticker + name）+ 初始信号列表 + 证据（evidence_snippets）+ 选择哪条传导轴
    输出：
        * 一整个 CompanySignalPlan（信号集合 + 4 态分布 + 总体信心度 + building_position_ready）
        * 3 条传导时间轴（产品认证 / 工厂产能 / 上游订单），每轴进度百分比 + 跳步诊断
          + 下一步 + 利润影响路径（人话）
        * 可跟踪的 Markdown 作战计划（下一阶段要补的证据清单 / 监测频率 / 预期时间点）

    核心原则：
        - 每条信号 state 必须由 4 态机切（不允许直接把信号写死成 double_confirm）
        - 跳步会被 TransmissionEngine 自动标黄（diagnose_jumps）
        - 「领先/同步/滞后」分类；lagging 指标虽然有证据但不允许计入 building_position_ready
        - 总体 confidence = 关键 signal 加权的 4 态分；缺关键 leading 信号 → confidence <0.5

    工作流 7 阶段：
        1. validate_inputs        校验 ticker/signals/axes
        2. apply_state_machine    按输入 evidence + transition_requests 切 4 态
        3. build_plan             SignalRegistry.build_plan 汇总 plan（state_summary + confidence）
        4. build_timelines        对 3 条模板各跑一次 TransmissionEngine.build（如果匹配）
        5. build_position_readiness 计算 building_position_ready + 早建仓风险警告
        6. render_report          生成 Markdown 作战计划（当前态矩阵 + 传导进度 + 下一步清单 + 风险）
        7. persist_outputs        保存 5 个制品 + 注册 ArtifactStore + 调用 research_memory 归档

参数说明：
    输入 input_data：
        ticker              (必填) str，例 "300502.SZ"
        name                (可选) 中文名
        raw_signals         (必填) list[dict]，每个 dict 至少有 signal_id/name
        transition_requests (可选) list[dict]:
            [{"signal_id": "...", "target_state": STATE_FIRST_CONFIRM, "evidence": {...}, "reason": "...", "independent_from_existing": bool}]
        axes                (可选) list，默认 ["product", "factory", "upstream"] 都跑
        allow_network       (必须=False)

返回值说明：
    5 个制品：
        signal_plan.json          - CompanySignalPlan 整份
        timelines.json            - 三条轴的 TransmissionTimeline（dict 形式）
        signal_matrix.md          - 作战计划 Markdown
        next_actions.csv          - 下一步证据收集清单（Excel 友好）
        position_readiness.md     - 建仓准备度 & 早建仓风险提示

异常处理：
    - 状态机切态失败：记 warning + 保留原态，不 throw
    - transition_requests 里引用不存在 signal_id：跳过并记 warning
    - axes 全没匹配：生成空时间轴 + 明确"数据不足"提示
    - 不 allow_network
"""

from __future__ import annotations

import csv
import json
import os
import sqlite3
from dataclasses import asdict, is_dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from smr_app.research.signal_registry import (
    CATEGORY_LABELS,
    CompanySignalPlan,
    EvidenceSnippet,
    IND_LABELS,
    Signal,
    SignalRegistry,
    SignalStateMachine,
    SignalThreshold,
    STATE_DOUBLE_CONFIRM,
    STATE_FIRST_CONFIRM,
    STATE_INVALIDATED,
    STATE_LABELS,
    STATE_OBSERVING,
)
from smr_app.research.transmission_timeline import (
    TransmissionEngine,
    TransmissionTemplate,
    TransmissionTimeline,
    factory_capacity_template,
    product_cert_template,
    upstream_order_template,
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
    configured = os.environ.get("SMR_ARTIFACT_ROOTS", "").split(os.pathsep)
    if configured and configured[0]:
        return Path(configured[0])
    return PROJECT_ROOT / "06_outputs" / "workflows"


def _json_default(obj: Any) -> Any:
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, set):
        return list(obj)
    if isinstance(obj, TransmissionTemplate):
        return {
            "template_id": obj.template_id,
            "name": obj.name,
            "axis": obj.axis,
            "description": obj.description,
            "nodes": [asdict(n) for n in obj.nodes],
        }
    raise TypeError(f"Type {type(obj).__name__} not JSON serializable")


# ============================================================================
# 1. validate_inputs
# ============================================================================

def _validate_inputs(ctx: WorkflowContext) -> StageResult:
    data = ctx.input_data
    if not isinstance(data.get("ticker"), str) or not data["ticker"].strip():
        return StageResult(status="failed", message="ticker 必填", summary={"error": "ticker"})
    raw = data.get("raw_signals")
    if not isinstance(raw, list) or len(raw) == 0:
        return StageResult(
            status="failed",
            message="raw_signals 必须是非空 list（哪怕只是观测期空壳信号）",
            summary={"error": "raw_signals"},
        )
    bad_ids = [str(i) for i, s in enumerate(raw)
               if not (isinstance(s, dict) and s.get("signal_id") and s.get("name"))]
    if bad_ids:
        return StageResult(
            status="failed",
            message=f"第 {', '.join(bad_ids)} 条 raw_signals 缺少 signal_id/name",
            summary={"bad": bad_ids},
        )
    if data.get("allow_network", False):
        return StageResult(status="failed", message="本工作流不允许联网（allow_network=False）")
    return StageResult(
        status="completed",
        message=f"输入 OK：ticker={data['ticker']!r}，初始信号 {len(raw)} 条",
        summary={
            "ticker": data["ticker"],
            "signal_count": len(raw),
            "transition_count": len(data.get("transition_requests") or []),
            "axes": data.get("axes") or ["product", "factory", "upstream"],
        },
    )


# ============================================================================
# 2. apply_state_machine（把 signals + transitions 先过状态机）
# ============================================================================

def _dict_to_signal(d: dict) -> Signal:
    """把 dict 变成 Signal（容错：缺字段就给默认）"""
    th = d.get("thresholds") or {}
    threshold = SignalThreshold(
        trigger=th.get("trigger") or {},
        invalidate=th.get("invalidate") or {},
        double_confirm_cond=th.get("double_confirm_cond") or {},
        frequency=th.get("frequency") or "每周",
        expire_after=th.get("expire_after") or "",
    )
    ev_list = [EvidenceSnippet(
        evidence_id=(e.get("evidence_id") or f"ev_auto_{i}"),
        source=e.get("source") or "",
        published_at=e.get("published_at") or "",
        summary=e.get("summary") or "",
        authority_tier=int(e.get("authority_tier") or 4),
    ) for i, e in enumerate(d.get("evidence") or [])]
    return Signal(
        signal_id=d["signal_id"],
        name=d["name"],
        category=d.get("category") or "产品/认证",
        indicator_kind=d.get("indicator_kind") or "leading",
        current_state=d.get("current_state") or STATE_OBSERVING,
        thresholds=threshold,
        evidence=ev_list,
        transmission_order=int(d.get("transmission_order") or 0),
        expected_months_delay=int(d.get("expected_months_delay") or 0),
        importance=float(d.get("importance") or 0.5),
        note=d.get("note") or "",
        invalidated_reason=d.get("invalidated_reason") or "",
        last_updated_at=d.get("last_updated_at") or "",
    )


def _apply_state_machine(ctx: WorkflowContext) -> StageResult:
    raw = ctx.input_data["raw_signals"]
    signals: list[Signal] = [_dict_to_signal(s) for s in raw]
    transitions = ctx.input_data.get("transition_requests") or []
    idx = {s.signal_id: s for s in signals}
    results = []
    for req in transitions:
        sid = req.get("signal_id")
        if sid not in idx:
            results.append({"signal_id": sid, "ok": False, "new_state": "", "reason": "信号不存在"})
            continue
        sig = idx[sid]
        ev_d = req.get("evidence")
        ev_obj = None
        if ev_d and isinstance(ev_d, dict):
            ev_obj = EvidenceSnippet(
                evidence_id=ev_d.get("evidence_id") or f"ev_req_{len(results)}",
                source=ev_d.get("source") or "",
                published_at=ev_d.get("published_at") or "",
                summary=ev_d.get("summary") or "",
                authority_tier=int(ev_d.get("authority_tier") or 4),
            )
        ok, new_state, reason = SignalStateMachine.try_transition(
            signal=sig,
            target_state=req.get("target_state") or STATE_OBSERVING,
            evidence=ev_obj,
            reason=req.get("reason") or "",
            independent_from_existing=bool(req.get("independent_from_existing")),
        )
        results.append({"signal_id": sid, "ok": ok, "new_state": new_state, "reason": reason})
    ctx.state["signals"] = signals
    ctx.state["transition_log"] = results
    ok_cnt = sum(1 for r in results if r["ok"])
    fail_cnt = len(results) - ok_cnt
    return StageResult(
        status="completed",
        message=f"状态机执行：成功 {ok_cnt}，失败 {fail_cnt}；总信号 {len(signals)}",
        summary={
            "ok_count": ok_cnt,
            "fail_count": fail_cnt,
            "signal_count": len(signals),
            "gate_degraded": fail_cnt > 0,
        },
        payload={"transition_log": results},
    )


# ============================================================================
# 3. build_plan（SignalRegistry 组装 + 总信心度）
# ============================================================================

def _build_plan(ctx: WorkflowContext) -> StageResult:
    signals: list[Signal] = ctx.state["signals"]
    plan = SignalRegistry.build_plan(
        ticker=ctx.input_data["ticker"],
        name=ctx.input_data.get("name") or "",
        signals=signals,
    )
    ctx.state["plan"] = plan
    return StageResult(
        status="completed",
        message=(
            f"信号计划构建完成：总体信心度 {plan.overall_confidence:.0%}，"
            f"建仓准备度 {'✅' if plan.building_position_ready else '⛔'}"
        ),
        summary={
            "plan_id": plan.plan_id,
            "state_summary": plan.state_summary,
            "overall_confidence": plan.overall_confidence,
            "building_position_ready": plan.building_position_ready,
        },
    )


# ============================================================================
# 4. build_timelines（三条标准轴）
# ============================================================================

def _build_timelines(ctx: WorkflowContext) -> StageResult:
    plan: CompanySignalPlan = ctx.state["plan"]
    axes = ctx.input_data.get("axes") or ["product", "factory", "upstream"]
    templates: list[TransmissionTemplate] = []
    if "product" in axes:
        templates.append(product_cert_template())
    if "factory" in axes:
        templates.append(factory_capacity_template())
    if "upstream" in axes:
        templates.append(upstream_order_template())
    timelines: list[TransmissionTimeline] = [
        TransmissionEngine.build(plan, tmpl) for tmpl in templates
    ]
    ctx.state["timelines"] = timelines
    return StageResult(
        status="completed",
        message=f"构建 {len(timelines)} 条传导时间轴",
        summary={
            f"{t.template.axis}_{t.template.template_id}": {
                "progress_pct": t.overall_progress_pct,
                "warning_count": len(t.warnings),
            }
            for t in timelines
        },
    )


# ============================================================================
# 5. build_position_readiness（独立质量门：早建仓风险）
# ============================================================================

def _build_position_readiness(ctx: WorkflowContext) -> StageResult:
    """
    建仓准备度 + 早建仓风险

    独立质量门（小白版）：
        a) 不能把 lagging（滞后指标）当 leading（领先指标）用，
           若关键信号（importance>=0.7）是 lagging → warning
        b) 若 double_confirm 只有 lagging 指标 → 明确 warning："滞后指标领先，领先指标未达"
        c) 若任何关键信号 invalidated → ready 强行翻 False（即使 plan 之前算了 True）
        d) "还没看到批量订单却准备建仓" = 通过 timelines 看：mass_order / company_po 都没达到
           却 confidence>=0.6 → warning
    """
    plan: CompanySignalPlan = ctx.state["plan"]
    timelines: list[TransmissionTimeline] = ctx.state.get("timelines") or []
    warnings: list[str] = []
    critical: list[str] = []

    key_signals = [s for s in plan.signals if s.importance >= 0.7]
    # a) lagging 关键信号
    lag_key = [s for s in key_signals if s.indicator_kind == "lagging"]
    if lag_key:
        warnings.append(
            "关键信号（importance≥0.7）里有滞后指标："
            + ", ".join(f"{s.signal_id}={s.name}" for s in lag_key)
            + "；滞后指标不能当建仓前置依据（等批量订单确认更稳）"
        )
    # b) double_confirm 只剩 lagging
    dc = [s for s in key_signals if s.current_state == STATE_DOUBLE_CONFIRM]
    if dc and all(s.indicator_kind == "lagging" for s in dc) and not plan.building_position_ready:
        warnings.append("双确认信号全是滞后指标 → 领先指标尚未确认，暂不建仓")
    # c) 关键 invalidated → 强制 ready=False
    invalid_key = [s for s in key_signals if s.current_state == STATE_INVALIDATED]
    if invalid_key:
        critical.append("关键信号已证伪：" + ", ".join(s.signal_id for s in invalid_key))
        plan.building_position_ready = False
    # d) 还没看到批量订单/PO，却信心已经过半（≥0.5）→ 早建仓风险提示
    if plan.overall_confidence >= 0.5:
        po_reached = False
        for tl in timelines:
            for nid in ("mass_order", "company_po", "shipment"):
                prog = tl.node_progress.get(nid)
                if prog and prog.reached:
                    po_reached = True
                    break
            if po_reached:
                break
        if not po_reached:
            warnings.append(
                "当前信心度 ≥60%，但三条传导轴均未达到"
                "「批量订单/公司 PO/批量出货」任一节点 → 可能属于"
                "「市场 price-in 了故事，但订单兑现还没到」的早建仓风险。"
            )
    # 质量门重算 summary
    SignalRegistry.recompute_summary(plan)
    ready_flag = plan.building_position_ready
    ctx.state["position_gate"] = {
        "warnings": warnings,
        "critical_errors": critical,
        "ready": ready_flag and (len(critical) == 0),
    }
    passed = len(critical) == 0
    return StageResult(
        status="completed",
        message=(
            f"建仓质量门：{'✅ 通过' if passed else '❌ 关键错误'}；"
            f"warnings={len(warnings)}，最终 ready={ready_flag and passed}"
        ),
        summary={
            "ready": ready_flag and passed,
            "warnings_count": len(warnings),
            "critical_count": len(critical),
            "gate_degraded": not passed,
        },
    )


# ============================================================================
# 6. render_report
# ============================================================================

def _fmt_signal_state(state: str) -> str:
    label = STATE_LABELS.get(state, state)
    emoji = {"observing": "🔍", "first_confirm": "✔️", "double_confirm": "✅✅", "invalidated": "❌"}.get(state, "·")
    return f"{emoji} {label}"


def _render_report(ctx: WorkflowContext) -> StageResult:
    plan: CompanySignalPlan = ctx.state["plan"]
    timelines: list[TransmissionTimeline] = ctx.state.get("timelines") or []
    pgate: dict = ctx.state.get("position_gate") or {}
    warnings: list[str] = pgate.get("warnings") or []
    critical: list[str] = pgate.get("critical_errors") or []

    lines: list[str] = []
    lines.append(f"# 公司信号计划 V1：{plan.name or plan.ticker}（{plan.ticker}）")
    lines.append("")
    lines.append(f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
    lines.append(f"> plan_id：`{plan.plan_id}`  ")
    lines.append(f"> 建仓准备度：{'✅ 可以考虑进入建仓观察' if pgate.get('ready') else '⛔ 暂不建仓'}  ")
    lines.append(f"> 总体信心度：**{plan.overall_confidence:.0%}**  ")
    lines.append("> 【声明】本文件仅输出**研究信号跟踪计划**，不构成任何投资建议或买入/卖出指令。")
    lines.append("")

    # 1. 状态分布
    lines.append("## 1. 4 态分布")
    lines.append("")
    for st, label in STATE_LABELS.items():
        cnt = plan.state_summary.get(st, 0)
        lines.append(f"- {_fmt_signal_state(st)}：{cnt} 条")
    lines.append("")

    # 2. 信号矩阵
    lines.append("## 2. 信号矩阵（按重要度降序）")
    lines.append("")
    lines.append("| ID | 名称 | 类别 | 指标 | 当前态 | 重要度 | 监测频率 | 备注 |")
    lines.append("|---|---|---|---|---|---:|---|---|")
    sorted_sigs = sorted(plan.signals, key=lambda s: (-s.importance, s.transmission_order))
    for s in sorted_sigs:
        freq = s.thresholds.frequency or "-"
        ind_label = IND_LABELS.get(s.indicator_kind, s.indicator_kind)
        cat_label = CATEGORY_LABELS.get(s.category, s.category)
        note = (s.note + ("" if not s.invalidated_reason else f"；❌{s.invalidated_reason}")) or "-"
        lines.append(
            f"| {s.signal_id} | {s.name} | {cat_label} | {ind_label} |"
            f" {_fmt_signal_state(s.current_state)} | {s.importance:.2f} | {freq} | {note} |"
        )
    lines.append("")

    # 3. 传导时间轴
    lines.append("## 3. 传导时间轴（三条标准轴）")
    lines.append("")
    next_rows = []
    for tl in timelines:
        lines.append(f"### 3.{timelines.index(tl) + 1} {tl.template.name}（{tl.template.description}）")
        lines.append("")
        lines.append(f"- 进度：**{tl.overall_progress_pct:.1f}%**")
        lines.append(f"- 人话总结：{tl.notes}")
        lines.append(f"- 利润链路：{TransmissionEngine.profit_linkage_summary(tl)}")
        if tl.warnings:
            lines.append("- 跳步/缺口警告：")
            for w in tl.warnings:
                lines.append(f"  - ⚠️ {w}")
        nid, need, why = TransmissionEngine.next_step(tl)
        node = next((n for n in tl.template.nodes if n.node_id == nid), None)
        node_name = node.name if node else nid
        lines.append(f"- 下一步 → **「{node_name}」**：{why}（需要证据：{need}）")
        next_rows.append([plan.ticker, plan.name or "", tl.template.axis, tl.template.template_id,
                          node_name, need[:80], why[:80]])
        # 节点表格
        lines.append("")
        lines.append("| 序 | 节点 | 月份 | 状态 | 已达? | 对利润影响 | 映射信号 |")
        lines.append("|---:|---|---:|---|---|---:|---|")
        for node in tl.template.nodes_sorted():
            prog = tl.node_progress.get(node.node_id)
            if prog is None:
                continue
            st = _fmt_signal_state(prog.state)
            reached_mark = "✅" if prog.reached else ("❌" if prog.state == STATE_INVALIDATED else "·")
            impact = f"{node.affects_profit * 100:.0f}%"
            mapped = ", ".join(prog.mapped_signal_ids) or "-"
            lines.append(
                f"| {node.order_in_axis} | {node.name} | {node.typical_months:.0f}m |"
                f" {st} | {reached_mark} | {impact} | {mapped} |"
            )
        lines.append("")

    # 4. 建仓质量门
    lines.append("## 4. 建仓准备度 & 早建仓风险（独立质量门）")
    lines.append("")
    lines.append(f"- 最终 ready：{'✅' if pgate.get('ready') else '⛔'}（{plan.overall_confidence:.0%} 信心）")
    if critical:
        lines.append("- 关键错误（不建仓）：")
        for e in critical:
            lines.append(f"  - ❌ {e}")
    if warnings:
        lines.append("- 风险提醒：")
        for w in warnings:
            lines.append(f"  - ⚠️ {w}")
    lines.append("")
    # 下一步清单
    lines.append("## 5. 下一阶段要补的证据（行动清单）")
    lines.append("")
    if not next_rows:
        lines.append("- （空）")
    else:
        lines.append("| 轴 | 下一步节点 | 需要证据 | 原因 |")
        lines.append("|---|---|---|---|")
        for r in next_rows:
            lines.append(f"| {r[2]} | {r[4]} | {r[5]} | {r[6]} |")
    lines.append("")
    lines.append("---")
    lines.append("*所有 4 态切态必须经过 SignalStateMachine.try_transition；跳步会被自动识别；缺关键领先信号时 confidence 会被压到 0.5 以下。*")
    md_text = "\n".join(lines)
    ctx.state["signal_matrix_md"] = md_text
    ctx.state["next_rows"] = next_rows

    # 额外：position_readiness.md（短版，快速查看）
    short = [
        f"# {plan.ticker} 建仓准备度速览",
        "",
        f"- 最终 ready：**{'✅' if pgate.get('ready') else '⛔'}**",
        f"- 信心度：{plan.overall_confidence:.0%}",
        f"- 信号总览：{plan.state_summary}",
        "- 关键错误：" + (("；".join(critical)) if critical else "无"),
        "- 警告：" + (("\n" + "\n".join(f"  - {w}" for w in warnings)) if warnings else "无"),
    ]
    for tl in timelines:
        short.append(f"- {tl.template.axis} 进度：{tl.overall_progress_pct:.1f}%；{tl.notes}")
    ctx.state["position_readiness_md"] = "\n".join(short)

    return StageResult(
        status="completed",
        message=f"报告渲染完成：signal_matrix={len(md_text)} 字符，行动项 {len(next_rows)} 条",
        summary={"md_len": len(md_text), "action_items": len(next_rows)},
    )


# ============================================================================
# 7. persist_outputs
# ============================================================================

def _persist_outputs(ctx: WorkflowContext) -> StageResult:
    root = _get_default_artifact_root()
    out_dir = root / f"company_signal_plan_{ctx.input_data['ticker']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    out_dir.mkdir(parents=True, exist_ok=True)

    plan: CompanySignalPlan = ctx.state["plan"]
    timelines: list[TransmissionTimeline] = ctx.state.get("timelines") or []
    md = ctx.state.get("signal_matrix_md") or ""
    pr_md = ctx.state.get("position_readiness_md") or ""
    next_rows: list[list] = ctx.state.get("next_rows") or []

    (out_dir / "signal_plan.json").write_text(
        json.dumps(plan, default=_json_default, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    # timelines：简化 dict 化（避免 template 直接 asdict 问题）
    tl_dicts = []
    for tl in timelines:
        tl_dicts.append({
            "ticker": tl.ticker,
            "name": tl.name,
            "template": {
                "template_id": tl.template.template_id, "name": tl.template.name,
                "axis": tl.template.axis, "description": tl.template.description,
                "nodes": [asdict(n) for n in tl.template.nodes],
            },
            "overall_progress_pct": tl.overall_progress_pct,
            "warnings": tl.warnings,
            "notes": tl.notes,
            "node_progress": {k: asdict(v) for k, v in tl.node_progress.items()},
        })
    (out_dir / "timelines.json").write_text(
        json.dumps(tl_dicts, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "signal_matrix.md").write_text(md, encoding="utf-8")
    (out_dir / "position_readiness.md").write_text(pr_md, encoding="utf-8")
    csv_path = out_dir / "next_actions.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ticker", "name", "axis", "template_id", "next_node", "need_evidence", "reason"])
        for r in next_rows:
            w.writerow(r)
    paths = {
        "signal_plan_json": str(out_dir / "signal_plan.json"),
        "timelines_json": str(out_dir / "timelines.json"),
        "signal_matrix_md": str(out_dir / "signal_matrix.md"),
        "position_readiness_md": str(out_dir / "position_readiness.md"),
        "next_actions_csv": str(csv_path),
    }
    reg_ids = {}
    registered = []
    artifact_types = {
        "signal_plan_json": ("signal_plan", "公司信号计划", "application/json"),
        "timelines_json": ("signal_timelines", "信号传导时间轴", "application/json"),
        "signal_matrix_md": ("signal_matrix", "公司信号作战矩阵", "text/markdown"),
        "position_readiness_md": ("position_readiness", "建仓准备度", "text/markdown"),
        "next_actions_csv": ("signal_next_actions", "信号补证行动清单", "text/csv"),
    }
    conn = sqlite3.connect(ctx.db_path)
    try:
        store = ArtifactStore(conn, [_get_default_artifact_root()])
        for key, path in paths.items():
            artifact_type, title, mime_type = artifact_types[key]
            artifact = store.register_artifact(
                ctx.run_id, artifact_type, title, path, mime_type,
                metadata={"ticker": ctx.input_data.get("ticker")},
            )
            reg_ids[key] = artifact["artifact_id"]
            registered.append(artifact)
    finally:
        conn.close()

    # 记忆持久化（如果 research_memory 已经安装）
    try:
        from smr_app.research.research_memory import ResearchMemory  # 延迟导入避免循环
        try:
            ResearchMemory.from_env().persist_signal_plan(
                plan=plan, timelines=timelines, artifacts_dir=str(out_dir),
            )
        except Exception:
            pass  # memory 失败不影响主流程
    except Exception:
        pass  # 模块不存在就跳过

    return StageResult(
        status="completed",
        message=f"5 个制品 + 1 份 memory 归档 已保存到 {out_dir}",
        summary={"out_dir": str(out_dir), "artifacts": paths, "reg_ids": reg_ids},
        artifacts=tuple(registered),
    )


# ============================================================================
# 工作流定义
# ============================================================================

def company_signal_plan_definition(*, source_db_path: Path | None = None) -> WorkflowDefinition:
    """
    构建「公司信号计划 V1」工作流定义

    参数：
        source_db_path - 可选外部 DB，当前忽略
    """
    stages = [
        StageDefinition("validate_inputs", _validate_inputs,
                        title="1. 校验 ticker/raw_signals/axes + allow_network=False"),
        StageDefinition("apply_state_machine", _apply_state_machine,
                        title="2. 用 SignalStateMachine 切 4 态（transition_requests）"),
        StageDefinition("build_plan", _build_plan,
                        title="3. SignalRegistry.build_plan（state_summary + confidence + ready）"),
        StageDefinition("build_timelines", _build_timelines,
                        title="4. TransmissionEngine 构建 3 条传导时间轴 + 跳步诊断"),
        StageDefinition("build_position_readiness", _build_position_readiness,
                        title="5. 独立建仓质量门（早建仓风险 / 滞后错用 / 关键证伪）"),
        StageDefinition("render_report", _render_report,
                        title="6. 渲染作战计划 Markdown + 建仓速览 + 行动 CSV"),
        StageDefinition("persist_outputs", _persist_outputs,
                        title="7. 保存 5 个制品 + ArtifactStore 注册 + research_memory 归档"),
    ]
    return WorkflowDefinition(
        workflow_id="company_signal_plan",
        title="公司信号计划 V1",
        description=(
            "给单个公司构建：信号矩阵（4 态机+证据）+ 3 条传导时间轴"
            "（产品/工厂/订单，带跳步诊断）+ 建仓准备度质量门；不构成股票推荐。"
        ),
        stages=tuple(stages),
        input_schema={
            "required": ["ticker", "raw_signals"],
            "properties": {
                "ticker": {"type": "string"},
                "name": {"type": "string"},
                "raw_signals": {"type": "array", "items": {"type": "object"}},
                "transition_requests": {"type": "array", "items": {"type": "object"}},
                "axes": {"type": "array", "items": {"type": "string"},
                         "default": ["product", "factory", "upstream"]},
                "allow_network": {"type": "boolean"},
            },
        },
    )
