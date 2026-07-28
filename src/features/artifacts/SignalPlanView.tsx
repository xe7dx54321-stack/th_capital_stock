/**
 * 组件：SignalPlanView（公司信号计划 / 公司观察清单）
 * ------------------------------------------------------
 * 功能（小白版）：把"这只股票我接下来要盯什么"列成结构化 3 个部分：
 *   1. 催化主题（哪个时点有什么事件会影响股价）
 *   2. 观察 KPI（季报/调研里我要核对的几个硬指标）
 *   3. Kill 条件（一旦触发就不再跟踪这只股票，立刻出池）
 *
 * UI 原则：
 *   - 先给股票名 + 计划基本信息（先展示制品）
 *   - 三个部分用卡片分块展示，信息密度高但不拥挤
 *   - 缺失值不崩（测试清单 2）
 *   - 所有文本纯 React 文本渲染，XSS 安全（测试清单 4）
 */

import React from "react";

export interface CatalystTheme {
  theme: string;
  window: string;
  impact?: number;
  evidence?: string[];
}

export interface ObservationKPI {
  kpi: string;
  threshold: string;
  frequency: string;
  source: string;
}

export interface SignalPlanViewProps {
  data: {
    ticker?: string;
    name?: string;
    plan_id?: string;
    plan_version?: string;
    generated_at?: string;
    catalyst_themes?: CatalystTheme[];
    observation_kpis?: ObservationKPI[];
    kill_conditions?: string[];
  };
}

export default function SignalPlanView(props: SignalPlanViewProps) {
  const { data } = props;
  if (!data) return <div className="artifact-card degraded">暂无信号计划</div>;

  const { ticker, name = "标的", plan_id, plan_version, generated_at,
          catalyst_themes = [], observation_kpis = [], kill_conditions = [] } = data;

  return (
    <article className="artifact-card signal-plan-view" aria-label={`${name}信号计划`}>
      <header className="card-header">
        <div>
          <h3>
            {name} 信号观察计划
            {ticker ? <small className="ticker-chip">{ticker}</small> : null}
          </h3>
          <div className="meta">
            {plan_id ? <span>计划 ID：{plan_id}</span> : null}
            {plan_version ? <span>版本：{plan_version}</span> : null}
            {generated_at ? <span>生成：{generated_at}</span> : null}
          </div>
        </div>
      </header>

      <div className="plan-grid">
        {/* ① 催化主题 */}
        <section className="plan-column catalysts" aria-label="催化主题">
          <h4>
            <span className="col-icon col-icon-catalyst">🔥</span>
            催化主题（{catalyst_themes.length}）
          </h4>
          {catalyst_themes.length === 0 ? <p className="degraded">暂无催化主题</p> : (
            <ul className="list-cards">
              {catalyst_themes.map((c, i) => (
                <li key={i} className="card-item">
                  <div className="row-main">
                    <strong className="theme-title">{c.theme}</strong>
                    {c.impact != null ? (
                      <span className="impact-chip" style={{ opacity: 0.4 + 0.6 * c.impact }}>
                        影响 {(c.impact * 10).toFixed(0)}/10
                      </span>
                    ) : null}
                  </div>
                  <div className="row-sub">窗口期：{c.window}</div>
                  {c.evidence && c.evidence.length ? (
                    <ul className="evidence-list small">
                      {c.evidence.map((e, ei) => <li key={ei}>{e}</li>)}
                    </ul>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* ② 观察 KPI */}
        <section className="plan-column kpis" aria-label="观察 KPI">
          <h4>
            <span className="col-icon col-icon-kpi">📊</span>
            观察 KPI（{observation_kpis.length}）
          </h4>
          {observation_kpis.length === 0 ? <p className="degraded">暂无观察指标</p> : (
            <ul className="list-cards">
              {observation_kpis.map((k, i) => (
                <li key={i} className="card-item">
                  <div className="row-main"><strong>{k.kpi}</strong></div>
                  <div className="row-sub">阈值：<code className="threshold">{k.threshold}</code></div>
                  <div className="row-sub">频率：{k.frequency} · 数据来源：{k.source}</div>
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* ③ Kill 条件 */}
        <section className="plan-column kills" aria-label="Kill 条件">
          <h4>
            <span className="col-icon col-icon-kill">🛑</span>
            Kill 条件（{kill_conditions.length}）
          </h4>
          {kill_conditions.length === 0 ? <p className="degraded">暂无 Kill 条件（建议至少设置 1 条）</p> : (
            <ol className="kill-list">
              {kill_conditions.map((k, i) => <li key={i}>{k}</li>)}
            </ol>
          )}
        </section>
      </div>
    </article>
  );
}
