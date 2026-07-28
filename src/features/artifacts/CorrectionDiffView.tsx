/**
 * 组件：CorrectionDiffView（纠错 diff 面板）
 * --------------------------------------------
 * 功能（小白版）：把"某份研究报告改了哪些地方"列出来。
 * 每条变更展示：字段名 / 修改前 → 修改后 / 影响等级 / 下游依赖有啥重算
 *   - fully_recalculated = 下游所有依赖都自动重新算过了 ✅
 *   - record_only        = 改了但不影响下游（比如日期/元数据）✅
 *   - failed             = 下游有依赖重算 ❌ 失败了（测试清单 7：部分成功场景）
 *
 * UI 原则：
 *   - 先放纠错原因（先结论）
 *   - before → after 左右对比或上下对比，一目了然
 *   - downstream_status 用图标/颜色区分 success/warn/fail（清单 7：失败/部分成功可见）
 *   - 所有内容纯 React 文本输出，XSS payload 无法执行（清单 4）
 *   - changes 空数组时不崩，显示友好文案（清单 2）
 */

import React from "react";

export interface CorrectionChange {
  field: string;
  before: any;
  after: any;
  unit?: string;
  impact: "low" | "medium" | "high";
  affected_downstream?: string[];
  downstream_status?: "fully_recalculated" | "record_only" | "failed" | string;
}

export interface CorrectionDiffViewProps {
  data: {
    report_id?: string;
    original_report_id?: string;
    correction_reason?: string;
    corrected_at?: string;
    corrected_by?: string;
    changes?: CorrectionChange[];
  };
}

function formatDiffValue(v: any): string {
  if (v == null) return "（空）";
  if (typeof v === "number") {
    if (Math.abs(v) >= 1e8) return `${(v / 1e8).toFixed(2)}亿`;
    return v.toLocaleString("zh-CN");
  }
  if (typeof v === "object") {
    try { return JSON.stringify(v); } catch { return String(v); }
  }
  return String(v);
}

function downstreamStatusBadge(status?: string) {
  switch (status) {
    case "fully_recalculated":
      return <span className="status-chip ok">下游已自动重算 ✅</span>;
    case "record_only":
      return <span className="status-chip info">仅记录变更（无下游）</span>;
    case "failed":
      return <span className="status-chip warn">下游重算失败 ⚠</span>;
    default:
      return status
        ? <span className="status-chip">下游状态：{String(status)}</span>
        : null;
  }
}

function impactBadge(impact: string) {
  const cls =
    impact === "high" ? "impact-chip high" :
    impact === "medium" ? "impact-chip medium" :
    "impact-chip low";
  const zh = impact === "high" ? "高影响" : impact === "medium" ? "中影响" : "低影响";
  return <span className={cls}>{zh}</span>;
}

export default function CorrectionDiffView(props: CorrectionDiffViewProps) {
  const { data } = props;
  if (!data) return <div className="artifact-card degraded">暂无纠错 diff</div>;

  const {
    report_id, original_report_id, correction_reason,
    corrected_at, corrected_by, changes = [],
  } = data;

  const hasFailed = changes.some((c) => c.downstream_status === "failed");

  return (
    <article className="artifact-card correction-diff-view" aria-label="纠错变更对比">
      {/* ====== 顶部：先给纠错原因 / 纠错人 / 时间 ====== */}
      <header className={`card-header correction-header ${hasFailed ? "has-failure" : ""}`}>
        <div>
          <h3>研究报告纠错（Correction Diff）</h3>
          {correction_reason ? (
            <p className="correction-reason">纠错原因：{correction_reason}</p>
          ) : null}
          <div className="meta">
            {report_id ? <span>报告 ID：{report_id}</span> : null}
            {original_report_id ? <span>原报告 ID：{original_report_id}</span> : null}
            {corrected_at ? <span>纠错时间：{corrected_at}</span> : null}
            {corrected_by ? <span>纠错来源：{corrected_by}</span> : null}
          </div>
          {/* 清单 7：有 failed 时顶部 banner 警告 */}
          {hasFailed ? (
            <div className="warn-banner" role="alert">
              ⚠ 部分依赖项「未成功重算」，请人工确认。
            </div>
          ) : null}
        </div>
      </header>

      {/* ====== 每个字段的 diff 明细 ====== */}
      {changes.length === 0 ? (
        <div className="degraded">本次无变更字段 diff</div>
      ) : (
        <ul className="diff-list">
          {changes.map((c, i) => (
            <li className="diff-item" key={i}>
              <div className="diff-head">
                <code className="field-name">{c.field}</code>
                {impactBadge(c.impact)}
                {downstreamStatusBadge(c.downstream_status)}
                {c.unit ? <span className="unit-chip">单位：{c.unit}</span> : null}
              </div>

              <div className="diff-values">
                <div className="diff-cell before">
                  <div className="diff-label">修改前</div>
                  <div className="diff-content">{formatDiffValue(c.before)}</div>
                </div>
                <div className="diff-arrow">→</div>
                <div className="diff-cell after">
                  <div className="diff-label">修改后</div>
                  <div className="diff-content">{formatDiffValue(c.after)}</div>
                </div>
              </div>

              {(c.affected_downstream && c.affected_downstream.length > 0) ? (
                <details className="downstream-list">
                  <summary>受影响的下游字段 / 段落（{c.affected_downstream.length}）</summary>
                  <ul>
                    {c.affected_downstream.map((d, di) => <li key={di}>{d}</li>)}
                  </ul>
                </details>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}
