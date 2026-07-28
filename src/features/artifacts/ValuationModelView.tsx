/**
 * 组件：ValuationModelView
 * --------------------------
 * 功能（小白版）：把一只股票的"估值模型"完整展示出来——先放【结论】给用户看，再逐个放
 * 【每种估值方法的假设 + 合理价】，最后放数据来源/时点（让用户看懂估值怎么算的）。
 *
 * UI 原则（严格遵循 Master Plan §阶段 13）：
 *   - 浅色、中文、信息密度高但不拥挤
 *   - 先展示结论和制品，再展示证据和执行细节
 *   - 不把阶段编号、运行编号这些系统数据混进报告正文
 *
 * Props：
 *   data —— 估值数据（见测试里的 makeValuationData）
 *
 * 异常处理：
 *   - 重要字段缺失（如 models 空数组、conclusion 空）时，降级显示友好占位，不抛异常（测试清单 2）
 *   - 用户注入的 XSS payload 通过 React textContent 方式渲染，不使用 dangerouslySetInnerHTML（测试清单 4）
 */

import React from "react";

export interface ValuationModel {
  method: string;
  assumptions: Record<string, any>;
  fair_value: { per_share: number; enterprise: number; unit: string };
  upside: number;
  confidence?: number;
}

export interface ValuationModelViewProps {
  data: {
    ticker?: string;
    name?: string;
    snapshot_date?: string;
    currency?: string;
    market_cap?: { value: number; unit: string; source_level?: string };
    models?: ValuationModel[];
    conclusion?: { verdict?: string; summary_score?: number | null };
  };
}

/**
 * 把「元」这种大数字格式化成「xx 亿元 / xx 亿元」，小白一眼看懂
 */
function formatBigNumber(value: number, unit: string = "元"): string {
  if (value == null || Number.isNaN(value)) return "—";
  const yi = value / 1e8;
  if (yi >= 1) return `${yi.toFixed(1)}亿${unit === "元" ? "元" : unit}`;
  return `${value.toLocaleString("zh-CN")}${unit}`;
}

/**
 * 把 upside（涨跌幅百分比）颜色区分：+ 绿，- 红
 */
function upsideBadge(upside: number): React.ReactNode {
  if (upside == null || Number.isNaN(upside)) return <span className="upside neutral">—</span>;
  const cls = upside > 0 ? "upside up" : upside < 0 ? "upside down" : "upside neutral";
  const text = `${upside > 0 ? "+" : ""}${upside.toFixed(1)}%`;
  return <span className={cls}>{text}</span>;
}

export default function ValuationModelView(props: ValuationModelViewProps) {
  const { data } = props;
  if (!data) {
    return <div className="artifact-card degraded">暂无估值数据</div>;
  }

  const {
    ticker = "",
    name = "标的",
    snapshot_date = "—",
    currency = "CNY",
    market_cap,
    models = [],
    conclusion,
  } = data;

  return (
    <article className="artifact-card valuation-model-view" aria-label={`${name}估值模型`}>
      {/* ====== 一、先放结论（UI 原则：先结论后证据） ====== */}
      <header className="conclusion-band">
        <div className="conclusion-left">
          <h3>
            {name}
            {ticker ? <small className="ticker-chip">{ticker}</small> : null}
          </h3>
          <p className="verdict">{conclusion?.verdict || "暂无估值结论"}</p>
          {conclusion?.summary_score != null ? (
            <p className="score">综合分：<strong>{conclusion.summary_score.toFixed(1)}</strong> / 5.0</p>
          ) : null}
        </div>
        <div className="conclusion-right">
          {market_cap ? (
            <div className="market-cap-box">
              <div className="label">当前市值</div>
              <div className="value">{formatBigNumber(market_cap.value, market_cap.unit)}</div>
              {market_cap.source_level ? (
                <div className="source-level">{market_cap.source_level}</div>
              ) : null}
            </div>
          ) : null}
          <div className="snapshot-meta">
            <span>数据日期：{snapshot_date}</span>
            <span>币种：{currency}</span>
          </div>
        </div>
      </header>

      {/* ====== 二、再放每个估值模型细节 ====== */}
      <section className="models-section" aria-label="估值模型列表">
        <h4>估值模型明细</h4>
        {models.length === 0 ? (
          <div className="degraded">暂无估值模型</div>
        ) : (
          <div className="models-grid">
            {models.map((m, idx) => (
              <div className="model-card" key={`${m.method}-${idx}`}>
                <div className="model-head">
                  <strong className="method-name">{m.method}</strong>
                  {m.confidence != null ? (
                    <span className="confidence-chip">置信度 {(m.confidence * 100).toFixed(0)}%</span>
                  ) : null}
                </div>
                <div className="model-result-row">
                  <div>
                    <div className="label">合理每股价值</div>
                    <div className="value">{m.fair_value.per_share.toFixed(2)} {currency}</div>
                  </div>
                  <div>
                    <div className="label">合理总市值</div>
                    <div className="value">{formatBigNumber(m.fair_value.enterprise, m.fair_value.unit)}</div>
                  </div>
                  <div>
                    <div className="label">相对当前价</div>
                    <div className="value">{upsideBadge(m.upside)}</div>
                  </div>
                </div>
                <div className="assumptions">
                  <div className="label">关键假设</div>
                  <ul>
                    {Object.entries(m.assumptions || {}).length === 0 ? (
                      <li className="degraded">—</li>
                    ) : (
                      Object.entries(m.assumptions).map(([k, v]) => (
                        <li key={k}>
                          <span className="assumption-key">{k}：</span>
                          <span className="assumption-val">
                            {Array.isArray(v) ? v.join("、") : String(v)}
                          </span>
                        </li>
                      ))
                    )}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </article>
  );
}
