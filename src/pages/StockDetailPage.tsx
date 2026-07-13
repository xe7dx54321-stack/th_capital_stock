/**
 * 标的详情页（完整分析报告版）
 *
 * 点击股票后进入此页面，显示完整的分析报告，包含：
 *  - 顶部：股票基本信息 + 最新价 + 综合投资建议（评分 + 结论）
 *  - 标签页：价格走势 / 估值分析 / 基本面分析 / 技术面 / 风险提示 / 研究主张 / 相关新闻
 */

import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
  ArrowLeft, TrendingUp, BarChart2, Newspaper, ShieldCheck,
  AlertTriangle, DollarSign, Activity, Award, ClipboardCheck, Lightbulb, ExternalLink
} from "lucide-react";
import * as echarts from "echarts/core";
import { LineChart } from "echarts/charts";
import { GridComponent, TooltipComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import type { StockDetail, ReportItem } from "../lib/api";
import { fetchStockDetail } from "../lib/api";

echarts.use([LineChart, GridComponent, TooltipComponent, CanvasRenderer]);

// 标签页定义
type TabKey = "chart" | "valuation" | "fundamentals" | "technical" |
  "risks" | "claims" | "news" | "moat" | "peerComparison" | "catalysts" | "deepReport";

const TABS: { key: TabKey; label: string; icon: any; desc: string }[] = [
  { key: "deepReport", label: "深度报告", icon: ClipboardCheck, desc: "华尔街投行风格 Equity Research 完整报告" },
  { key: "chart", label: "价格走势", icon: BarChart2, desc: "近 30 个交易日价格与成交量" },
  { key: "valuation", label: "估值分析", icon: DollarSign, desc: "PE / PB / 安全边际" },
  { key: "fundamentals", label: "基本面分析", icon: Award, desc: "营收 / 利润 / ROE / 现金流" },
  { key: "technical", label: "技术面", icon: Activity, desc: "RSI / MACD / 动量" },
  { key: "moat", label: "护城河", icon: ShieldCheck, desc: "品牌 / 成本 / 规模 / 无形资产" },
  { key: "peerComparison", label: "同业对标", icon: TrendingUp, desc: "在行业中的相对位置" },
  { key: "catalysts", label: "催化因素", icon: Lightbulb, desc: "新闻情绪 + 研究主张" },
  { key: "risks", label: "风险提示", icon: AlertTriangle, desc: "系统识别到的风险事件" },
  { key: "claims", label: "研究主张", icon: ClipboardCheck, desc: "看涨/看跌观点与证据" },
  { key: "news", label: "相关新闻", icon: Newspaper, desc: "该标的相关的最新报道" },
];

function formatDate(s: string): string {
  if (!s) return "";
  return s.slice(0, 16).replace("T", " ");
}

// 将指标标签转换为颜色
function indicatorColor(label: string): string {
  if (!label) return "border-surface-4 text-text-muted bg-surface-3";
  // 正面信号
  const positive = /低估|合理|优秀|高增长|稳健|破净|高毛利|正向|金叉|上涨|强势|超卖/;
  // 负面信号
  const negative = /偏高|泡沫|亏损|下滑|超买|死叉|大跌|暴跌|下跌|偏弱/;
  if (positive.test(label) && !negative.test(label)) return "border-emerald-500/40 text-emerald-400 bg-emerald-500/10";
  if (negative.test(label)) return "border-rose-500/40 text-rose-400 bg-rose-500/10";
  // 中性
  return "border-sky-500/40 text-sky-400 bg-sky-500/10";
}

// 判断某个 label 是否属于正面或负面
function verdictBadge(verdict: string): string {
  if (/偏多|看涨|积极|看好/.test(verdict)) return "bg-emerald-500/15 text-emerald-400 border-emerald-500/30";
  if (/偏空|看跌|谨慎|风险/.test(verdict)) return "bg-rose-500/15 text-rose-400 border-rose-500/30";
  if (/中性偏多|观望/.test(verdict)) return "bg-amber-500/15 text-amber-400 border-amber-500/30";
  return "bg-sky-500/15 text-sky-400 border-sky-500/30";
}

// 评分的颜色（0-10分）
function scoreColor(score: number): string {
  if (score >= 7) return "#34d399"; // emerald
  if (score >= 5) return "#fbbf24"; // amber
  if (score >= 3) return "#fb923c"; // orange
  return "#f87171"; // red
}

// 通用：指标列表组件（展示一组 ReportItem）
function ReportItemList({ items, summary, emptyText }: { items: ReportItem[] | undefined; summary?: string; emptyText: string }) {
  if (!items || items.length === 0) {
    return (
      <div className="bg-surface-3 rounded-lg p-6 text-sm text-text-muted text-center">
        {emptyText}
      </div>
    );
  }
  return (
    <div className="space-y-3">
      {summary && (
        <div className="bg-surface-3 rounded-lg p-4 border border-surface-4 text-sm text-text leading-relaxed">
          <span className="inline-flex items-center gap-1.5 text-text font-medium mr-2">
            <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
            总结
          </span>
          {summary}
        </div>
      )}
      {items.map((it, idx) => (
        <div key={idx} className="bg-surface-3 rounded-lg border border-surface-4 overflow-hidden">
          <div className="px-4 py-3 flex items-start justify-between gap-3 border-b border-surface-4">
            <div className="flex items-center gap-2 min-w-0">
              <span className={`text-xs px-2 py-0.5 rounded-md border ${indicatorColor(it.label)}`}>
                {it.label}
              </span>
              <span className="text-sm font-medium text-text truncate">{it.metric}</span>
            </div>
            <div className="text-sm font-mono text-text flex-shrink-0">{it.value}</div>
          </div>
          <div className="px-4 py-3 text-xs text-text-muted leading-relaxed">{it.text}</div>
        </div>
      ))}
    </div>
  );
}

export default function StockDetailPage() {
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();
  const [detail, setDetail] = useState<StockDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabKey>("deepReport");

  useEffect(() => {
    if (!code) return;
    setLoading(true);
    fetchStockDetail(decodeURIComponent(code))
      .then((d) => {
        setDetail(d);
        setLoading(false);
      })
      .catch((e) => {
        setError(e.message);
        setLoading(false);
      });
  }, [code]);

  // 价格走势图
  useEffect(() => {
    if (!detail || activeTab !== "chart" || !detail.priceHistory.length) return;
    const chartDom = document.getElementById("price-chart");
    if (!chartDom) return;
    const chart = echarts.init(chartDom as HTMLElement);
    const dates = detail.priceHistory.map((p) => p.date.slice(0, 10));
    const closes = detail.priceHistory.map((p) => p.close);
    chart.setOption({
      backgroundColor: "transparent",
      grid: { top: 20, right: 20, bottom: 40, left: 60 },
      xAxis: { type: "category", data: dates, axisLine: { lineStyle: { color: "#2f2f2f" } }, axisTick: { show: false }, axisLabel: { color: "#8a8a8a", fontSize: 11 } },
      yAxis: { type: "value", axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: "#8a8a8a", fontSize: 11 }, splitLine: { lineStyle: { color: "#2a2a2a" } } },
      tooltip: { trigger: "axis", backgroundColor: "#1a1a1a", borderColor: "#2f2f2f", textStyle: { color: "#f5f1ea", fontSize: 12 } },
      series: [{ data: closes, type: "line", smooth: true, symbol: "none", lineStyle: { color: "#d4a373", width: 2 }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: "rgba(212,163,115,0.3)" }, { offset: 1, color: "rgba(212,163,115,0.02)" }]) } }],
    });
    const resizeObserver = new ResizeObserver(() => chart.resize());
    resizeObserver.observe(chartDom);
    return () => { chart.dispose(); resizeObserver.disconnect(); };
  }, [detail, activeTab]);

  if (loading) {
    return (
      <div className="min-h-screen bg-surface text-text flex items-center justify-center">
        <div className="text-text-muted">加载中…</div>
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="min-h-screen bg-surface text-text flex items-center justify-center flex-col gap-4">
        <div className="text-[#b74a2c]">加载失败：{error}</div>
        <button onClick={() => navigate("/")} className="text-accent underline text-sm">返回首页</button>
      </div>
    );
  }

  const report = detail.report || {} as any;
  const recommendation = report.overallRecommendation || { verdict: "暂无数据", text: "暂无综合投资建议", score: null, bullSignals: 0, bearSignals: 0 };

  return (
    <div className="min-h-screen bg-surface text-text">
      {/* 顶部：基本信息 + 综合投资建议 */}
      <header className="sticky top-0 z-20 bg-surface/90 backdrop-blur-sm border-b border-surface-4">
        <div className="max-w-5xl mx-auto px-6 py-4">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div className="flex items-start gap-3 min-w-0">
              <button onClick={() => navigate(-1)} className="flex-shrink-0 flex items-center gap-1.5 text-xs text-text-muted hover:text-accent transition-colors pt-1.5">
                <ArrowLeft className="w-4 h-4" /> 返回
              </button>
              <div className="min-w-0">
                <div className="text-xl font-medium text-text truncate">{detail.name}</div>
                <div className="text-xs text-text-dim mt-1">
                  {detail.tsCode} · {detail.market}股{detail.sector ? ` · ${detail.sector}` : ""}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-6">
              {detail.latestPrice != null && (
                <div className="text-right">
                  <div className="text-2xl font-light tabular-nums">{Number(detail.latestPrice).toFixed(2)}</div>
                  {detail.market === "US" && <div className="text-xs text-text-dim">USD</div>}
                </div>
              )}

              {/* 综合评分 + 结论 */}
              <div className="text-right">
                <div className="text-xs text-text-dim mb-1">综合投资建议</div>
                <div className="flex items-center justify-end gap-2">
                  {recommendation.score != null && (
                    <span
                      className="inline-flex items-center justify-center rounded-full border-2 w-11 h-11 text-base font-semibold tabular-nums"
                      style={{ color: scoreColor(recommendation.score), borderColor: scoreColor(recommendation.score) + "80" }}
                    >
                      {Number(recommendation.score).toFixed(1)}
                    </span>
                  )}
                  <span className={`text-xs px-2 py-1 rounded-md border ${verdictBadge(recommendation.verdict || "")}`}>
                    {recommendation.verdict}
                  </span>
                </div>
                {(recommendation.bullSignals > 0 || recommendation.bearSignals > 0) && (
                  <div className="text-[11px] text-text-dim mt-1.5">
                    正面 {recommendation.bullSignals} · 负面 {recommendation.bearSignals}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* 综合建议文本（放在标签页上方） */}
          {recommendation.text && (
            <div className="mt-4 bg-surface-2 rounded-lg border border-surface-4 p-4 text-sm text-text leading-relaxed">
              <span className="inline-flex items-center gap-1.5 text-text font-medium mr-2">
                <ShieldCheck className="w-3.5 h-3.5 text-amber-400" /> 综合解读
              </span>
              {recommendation.text}
            </div>
          )}

          {/* ===== 决策参数卡片（Task 7 新增） ===== */}
          {(recommendation.entryPrice != null || recommendation.targetPrice != null || recommendation.stopLoss != null) && (
            <div className="mt-4 bg-surface-2 rounded-lg border border-surface-4 p-4">
              <div className="text-xs text-text-dim mb-3">执行参数（仅供研究参考，不构成投资建议）</div>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div>
                  <div className="text-[11px] text-text-dim mb-1">建议买入价</div>
                  <div className="text-lg font-light tabular-nums text-emerald-400">
                    {recommendation.entryPrice != null ? Number(recommendation.entryPrice).toFixed(2) : "—"}
                  </div>
                </div>
                <div>
                  <div className="text-[11px] text-text-dim mb-1">目标价</div>
                  <div className="text-lg font-light tabular-nums text-amber-400">
                    {recommendation.targetPrice != null ? Number(recommendation.targetPrice).toFixed(2) : "—"}
                  </div>
                </div>
                <div>
                  <div className="text-[11px] text-text-dim mb-1">止损价</div>
                  <div className="text-lg font-light tabular-nums text-rose-400">
                    {recommendation.stopLoss != null ? Number(recommendation.stopLoss).toFixed(2) : "—"}
                  </div>
                </div>
                <div>
                  <div className="text-[11px] text-text-dim mb-1">建议仓位</div>
                  <div className="text-lg font-light tabular-nums text-text">
                    {recommendation.suggestedPositionSize != null ? `${Number(recommendation.suggestedPositionSize * 100).toFixed(0)}%` : "—"}
                  </div>
                </div>
                <div>
                  <div className="text-[11px] text-text-dim mb-1">持有期</div>
                  <div className="text-sm font-light text-text mt-1">{recommendation.timeHorizon || "—"}</div>
                </div>
              </div>
              {recommendation.reasoning && (
                <div className="mt-3 pt-3 border-t border-surface-4 text-xs text-text-dim leading-relaxed">
                  {recommendation.reasoning}
                </div>
              )}
            </div>
          )}
        </div>
      </header>

      {/* 主体：标签页 */}
      <main className="max-w-5xl mx-auto px-6 py-6 space-y-5">
        {/* 标签页导航 */}
        <div className="flex items-center gap-1 border-b border-surface-4 overflow-x-auto">
          {TABS.map(({ key, label, icon: Icon }) => {
            const isActive = activeTab === key;
            const badge = (() => {
              if (key === "risks") return (report.riskAlerts || []).length;
              if (key === "claims") return (report.claims || []).length;
              if (key === "news") return (detail.news || []).length;
              return null;
            })();
            return (
              <button
                key={key}
                onClick={() => setActiveTab(key)}
                className={
                  "flex items-center gap-1.5 px-3 py-2.5 text-xs whitespace-nowrap border-b-2 transition-colors " +
                  (isActive ? "border-accent text-accent" : "border-transparent text-text-muted hover:text-text")
                }
              >
                <Icon className="w-3.5 h-3.5" />
                {label}
                {badge != null && badge > 0 && (
                  <span className="ml-0.5 text-[10px] px-1.5 py-0 rounded bg-surface-4 text-text-muted tabular-nums">{badge}</span>
                )}
              </button>
            );
          })}
        </div>

        {/* ===== 标签页内容：价格走势 ===== */}
        {activeTab === "chart" && (
          <div className="space-y-4 animate-fade-in">
            <div className="card-base p-5">
              <div className="text-sm text-text-muted mb-3">近 {detail.priceHistory.length} 个交易日收盘价走势</div>
              {detail.priceHistory.length > 0 ? (
                <div id="price-chart" className="w-full h-72" />
              ) : (
                <div className="h-72 flex items-center justify-center text-text-dim text-sm">暂无价格数据</div>
              )}
            </div>

            {/* 关键财务因子快速展示（保留原有的快速概览） */}
            {Object.keys(detail.factors || {}).length > 0 && (
              <div className="card-base p-5">
                <div className="text-sm font-medium text-text mb-3">关键因子（原始数据）</div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(detail.factors).slice(0, 8).map(([key, val]) => (
                    <div key={key} className="text-center">
                      <div className="text-xs text-text-dim mb-1">{key}</div>
                      <div className="text-sm font-light tabular-nums text-text">
                        {typeof val === "number" ? (Number.isInteger(val) ? val : val.toFixed(2)) : String(val ?? "—")}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ===== 估值分析 ===== */}
        {activeTab === "valuation" && (
          <div className="animate-fade-in">
            <ReportItemList
              items={report.valuation?.items}
              summary={report.valuation?.summary}
              emptyText="暂无估值数据，可能是该股票未进入研究池。"
            />
          </div>
        )}

        {/* ===== 基本面分析 ===== */}
        {activeTab === "fundamentals" && (
          <div className="animate-fade-in space-y-3">
            {(report.fundamentals?.sourceQuality || report.fundamentals?.freshness) && (
              <div className="text-xs text-text-muted">
                数据来源质量: {report.fundamentals?.sourceQuality || "未知"} · 数据新鲜度: {report.fundamentals?.freshness || "未知"}
              </div>
            )}
            <ReportItemList
              items={report.fundamentals?.items}
              summary={report.fundamentals?.summary}
              emptyText="暂无基本面数据。该股票可能还未进入研究池，或暂无最新财报可解析。"
            />
          </div>
        )}

        {/* ===== 技术面分析 ===== */}
        {activeTab === "technical" && (
          <div className="animate-fade-in">
            <ReportItemList
              items={report.technical?.items}
              summary={report.technical?.summary}
              emptyText="暂无技术指标数据。"
            />
          </div>
        )}

        {/* ===== 风险提示 ===== */}
        {activeTab === "risks" && (
          <div className="animate-fade-in">
            {!report.riskAlerts || report.riskAlerts.length === 0 ? (
              <div className="bg-surface-3 rounded-lg p-6 text-sm text-text-muted text-center border border-surface-4">
                暂未识别到明显的风险信号。
              </div>
            ) : (
              <div className="space-y-3">
                {report.riskAlerts.map((r: any, idx: number) => (
                  <div key={idx} className="card-base p-4 border-rose-500/20">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xs px-2 py-0.5 rounded bg-rose-500/15 text-rose-400 border border-rose-500/30">
                          {r.alertType || "风险"}
                        </span>
                        {r.severity && (
                          <span className="text-[11px] text-text-dim">严重度: {r.severity}</span>
                        )}
                      </div>
                      <span className="text-[11px] text-text-muted tabular-nums">{formatDate(r.alertTime || "")}</span>
                    </div>
                    {r.message && <div className="text-sm text-text leading-relaxed">{r.message}</div>}
                    {r.action && <div className="text-xs text-text-muted mt-2">建议操作：{r.action}</div>}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ===== 研究主张 ===== */}
        {activeTab === "claims" && (
          <div className="animate-fade-in">
            {!report.claims || report.claims.length === 0 ? (
              <div className="bg-surface-3 rounded-lg p-6 text-sm text-text-muted text-center border border-surface-4">
                暂无来自新闻/研报的明确研究主张。
              </div>
            ) : (
              <div className="space-y-3">
                {report.claims.map((c: any, idx: number) => {
                  const typeLower = String(c.claimType || "").toLowerCase();
                  const isBull = /bull|long|buy|增持|买入/.test(typeLower);
                  const isBear = /bear|short|sell|减持|卖出/.test(typeLower);
                  const colorClass = isBull ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400" : isBear ? "bg-rose-500/10 border-rose-500/30 text-rose-400" : "bg-sky-500/10 border-sky-500/30 text-sky-400";
                  return (
                    <div key={idx} className="card-base p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className={`text-xs px-2 py-0.5 rounded border ${colorClass}`}>
                          {c.claimType || "观点"}
                        </span>
                        {c.importance && <span className="text-[11px] text-text-muted">{c.importance}</span>}
                      </div>
                      {c.claimText && <div className="text-sm text-text leading-relaxed whitespace-pre-wrap">{c.claimText}</div>}
                      {c.stance && <div className="text-xs text-text-dim mt-2">立场: {c.stance} · 置信度: {c.confidence ?? "—"}</div>}
                      {c.createdAt && <div className="text-[11px] text-text-muted mt-1 tabular-nums">{formatDate(c.createdAt)}</div>}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* ===== 相关新闻 ===== */}
        {activeTab === "news" && (
          <div className="animate-fade-in">
            {!detail.news || detail.news.length === 0 ? (
              <div className="bg-surface-3 rounded-lg p-6 text-sm text-text-muted text-center border border-surface-4">
                暂无相关新闻。
              </div>
            ) : (
              <div className="divide-y divide-surface-4 bg-surface-2 rounded-xl border border-surface-4">
                {detail.news.map((n) => (
                  <div key={n.id} className="px-5 py-4 hover:bg-surface-3 transition-colors">
                    <div className="flex items-center gap-2 text-xs text-text-dim mb-2">
                      <span className="px-2 py-0.5 bg-surface-3 rounded text-text-muted">
                        {n.sourceName || n.source}
                      </span>
                      <span className="tabular-nums">{formatDate(n.publishedAt)}</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <div className="text-sm text-text leading-relaxed flex-1">{n.title}</div>
                      {n.url && (
                        <a href={n.url} target="_blank" rel="noreferrer" className="flex-shrink-0 text-text-dim hover:text-accent transition-colors">
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      )}
                    </div>
                    {n.tickers && n.tickers.length > 0 && (
                      <div className="flex flex-wrap items-center gap-1.5 mt-2">
                        {n.tickers.slice(0, 5).map((t: string) => (
                          <Link
                            key={t}
                            to={`/stock/${encodeURIComponent(t)}`}
                            className="text-[11px] px-1.5 py-0.5 bg-surface-3 rounded text-accent border border-surface-4 hover:border-accent transition-colors"
                          >
                            {t}
                          </Link>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ===== 标签页：护城河评估 ===== */}
        {activeTab === "moat" && (
          <div className="space-y-4 animate-fade-in">
            <div className="card-base p-5">
              <div className="flex items-start justify-between gap-4 mb-4">
                <div>
                  <div className="text-sm font-medium text-text">综合护城河评分</div>
                  <div className="text-xs text-text-dim mt-1">6 个维度加权评估</div>
                </div>
                {report.moat?.totalScore != null ? (
                  <div
                    className="text-3xl font-light tabular-nums"
                    style={{ color: scoreColor(Number(report.moat.totalScore)) }}
                  >
                    {Number(report.moat.totalScore).toFixed(0)}
                    <span className="text-sm text-text-dim ml-1">/ 100</span>
                  </div>
                ) : (
                  <div className="text-sm text-text-dim">暂无评分</div>
                )}
              </div>
              <div className="text-sm text-text leading-relaxed">{report.moat?.summary || "暂无护城河分析数据。"}</div>
              {(report.moat?.evidenceChain || []).length > 0 && (
                <div className="mt-4 pt-4 border-t border-surface-4">
                  <div className="text-xs text-text-dim mb-2">关键证据</div>
                  <ul className="space-y-1.5">
                    {report.moat.evidenceChain.map((e: string, i: number) => (
                      <li key={i} className="text-sm text-text leading-relaxed pl-3 border-l-2 border-accent/40">
                        {e}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* 各维度得分 */}
            {(report.moat?.dimensions || []).length > 0 && (
              <div className="card-base p-5">
                <div className="text-sm font-medium text-text mb-4">维度得分</div>
                <div className="space-y-3">
                  {report.moat.dimensions.map((d: any, idx: number) => (
                    <div key={idx} className="space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-text">{d.name}</span>
                        <span className="text-xs tabular-nums text-text-dim">
                          {d.score != null ? `${Number(d.score).toFixed(1)} / 10` : "暂无"}
                        </span>
                      </div>
                      {d.score != null && (
                        <div className="w-full h-1.5 bg-surface-4 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all"
                            style={{
                              width: `${(Number(d.score) / 10) * 100}%`,
                              backgroundColor: scoreColor(Number(d.score) * 10),
                            }}
                          />
                        </div>
                      )}
                      {(d.evidence || []).length > 0 && (
                        <div className="text-xs text-text-dim pl-2">
                          {d.evidence.join(" · ")}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ===== 标签页：同业对标 ===== */}
        {activeTab === "peerComparison" && (
          <div className="space-y-4 animate-fade-in">
            <div className="card-base p-5">
              <div className="text-sm font-medium text-text mb-1">行业地位</div>
              <div className="text-sm text-text leading-relaxed">
                {report.peerComparison?.industryPosition || "暂无足够的同行数据进行对标分析。"}
              </div>
              {report.peerComparison?.sector && (
                <div className="text-xs text-text-dim mt-2">
                  所属行业：{report.peerComparison.sector} · 对比样本 {report.peerComparison.peerCount || 0} 家
                </div>
              )}
            </div>

            {(report.peerComparison?.metrics || []).length > 0 ? (
              <div className="card-base p-5">
                <div className="text-sm font-medium text-text mb-4">指标对标</div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-xs text-text-dim border-b border-surface-4">
                        <th className="text-left py-2 pr-4 font-normal">指标</th>
                        <th className="text-right py-2 pr-4 font-normal">本公司</th>
                        <th className="text-right py-2 pr-4 font-normal">同行均值</th>
                        <th className="text-right py-2 pr-4 font-normal">百分位</th>
                        <th className="text-right py-2 font-normal">排名</th>
                      </tr>
                    </thead>
                    <tbody>
                      {report.peerComparison.metrics.map((m: any, idx: number) => (
                        <tr key={idx} className="border-b border-surface-4/60 last:border-0">
                          <td className="py-2.5 pr-4 text-text">{m.name}</td>
                          <td className="py-2.5 pr-4 text-right tabular-nums text-text">
                            {m.value != null ? Number(m.value).toFixed(2) : "—"}
                          </td>
                          <td className="py-2.5 pr-4 text-right tabular-nums text-text-dim">
                            {m.peerAvg != null ? Number(m.peerAvg).toFixed(2) : "—"}
                          </td>
                          <td className="py-2.5 pr-4 text-right tabular-nums text-text-dim">
                            {m.percentile != null ? `${Number(m.percentile).toFixed(0)}%` : "—"}
                          </td>
                          <td className="py-2.5 text-right tabular-nums text-text-dim">
                            {m.rank != null && m.total != null ? `${Number(m.rank)} / ${Number(m.total)}` : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="mt-4 pt-3 border-t border-surface-4 text-xs text-text-dim leading-relaxed">
                  百分位越高表示在行业内的表现越靠前（PE/PB 则越低越好，已在计算时反向处理）。
                </div>
              </div>
            ) : (
              <div className="bg-surface-3 rounded-lg p-6 text-sm text-text-muted text-center border border-surface-4">
                暂无同行对标数据。
              </div>
            )}
          </div>
        )}

        {/* ===== 标签页：催化因素 ===== */}
        {activeTab === "catalysts" && (
          <div className="space-y-4 animate-fade-in">
            <div className="card-base p-5">
              <div className="flex items-start justify-between gap-4 mb-3">
                <div>
                  <div className="text-sm font-medium text-text">综合催化评分</div>
                  <div className="text-xs text-text-dim mt-1">基于新闻情绪与研究主张的加权评估</div>
                </div>
                {report.catalysts?.catalystScore != null ? (
                  <div
                    className="text-3xl font-light tabular-nums"
                    style={{ color: Number(report.catalysts.catalystScore) >= 0 ? "#fbbf24" : "#f87171" }}
                  >
                    {Number(report.catalysts.catalystScore) > 0 ? "+" : ""}{Number(report.catalysts.catalystScore).toFixed(0)}
                  </div>
                ) : (
                  <div className="text-sm text-text-dim">暂无评分</div>
                )}
              </div>
              <div className="text-sm text-text leading-relaxed">
                {report.catalysts?.summary || "暂无催化因素分析。"}
              </div>
              {report.catalysts?.netDirection && (
                <div className="mt-3 text-xs text-text-dim">
                  市场情绪方向：<span className={report.catalysts.netDirection === "bullish" ? "text-emerald-400" : report.catalysts.netDirection === "bearish" ? "text-rose-400" : "text-text-dim"}>
                    {report.catalysts.netDirection === "bullish" ? "偏多" : report.catalysts.netDirection === "bearish" ? "偏空" : "中性"}
                  </span>
                </div>
              )}
            </div>

            {/* 近期催化新闻 */}
            {(report.catalysts?.recentNews || []).length > 0 && (
              <div className="card-base p-5">
                <div className="text-sm font-medium text-text mb-3">近期催化事件（新闻）</div>
                <div className="space-y-2">
                  {report.catalysts.recentNews.slice(0, 10).map((n: any, idx: number) => (
                    <div key={idx} className="flex items-start gap-3 p-2 rounded-lg bg-surface-3/50 hover:bg-surface-3 transition-colors">
                      <div
                        className={`flex-shrink-0 mt-0.5 w-2 h-2 rounded-full ${
                          n.direction === "bullish" ? "bg-emerald-400" : n.direction === "bearish" ? "bg-rose-400" : "bg-surface-4"
                        }`}
                      />
                      <div className="flex-1 min-w-0">
                        <div className="text-sm text-text leading-relaxed">{n.title}</div>
                        <div className="text-[11px] text-text-dim mt-1">
                          {n.sourceName || n.source} · {formatDate(n.publishedAt)}
                        </div>
                      </div>
                      {n.url && (
                        <a href={n.url} target="_blank" rel="noreferrer" className="flex-shrink-0 text-text-dim hover:text-accent">
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 研究主张 */}
            {(report.catalysts?.upcomingClaims || []).length > 0 && (
              <div className="card-base p-5">
                <div className="text-sm font-medium text-text mb-3">研究主张</div>
                <div className="space-y-2">
                  {report.catalysts.upcomingClaims.map((c: any, idx: number) => (
                    <div key={idx} className="flex items-start gap-3 p-2 rounded-lg bg-surface-3/50">
                      <div
                        className={`flex-shrink-0 mt-0.5 w-2 h-2 rounded-full ${
                          c.direction === "bullish" ? "bg-emerald-400" : c.direction === "bearish" ? "bg-rose-400" : "bg-surface-4"
                        }`}
                      />
                      <div className="flex-1 min-w-0">
                        <div className="text-sm text-text leading-relaxed">{c.claimText}</div>
                        <div className="text-[11px] text-text-dim mt-1">
                          {c.stance || "立场未知"} · 置信度 {c.confidence ?? "—"} · {formatDate(c.createdAt)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ============ Task 9：深度研究报告（华尔街投行风格） ============ */}
        {activeTab === "deepReport" && report.deepReport && (
          <div className="space-y-6 animate-fade-in">
            {/* 报告头部 */}
            <div className="card-base p-6 border-l-4 border-l-accent">
              <div className="flex items-start justify-between gap-6 flex-wrap">
                <div>
                  <div className="text-xs text-text-dim uppercase tracking-wider mb-1">Equity Research · 个股深度研究</div>
                  <div className="text-2xl font-semibold text-text">
                    {report.deepReport.reportMeta?.name || detail.name}
                    <span className="text-text-muted text-base ml-2 font-normal">
                      ({report.deepReport.reportMeta?.tsCode || detail.tsCode})
                    </span>
                  </div>
                  <div className="text-sm text-text-dim mt-2">
                    {report.deepReport.reportMeta?.sector || report.sector || "—"}
                    {report.deepReport.reportMeta?.generatedAt && (
                      <span className="ml-4">生成时间：{formatDate(report.deepReport.reportMeta.generatedAt)}</span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {report.overallRecommendation?.verdict && (
                    <div className={`px-4 py-2 rounded-lg border text-sm font-medium ${
                      /看多|买入|强烈看多|超买/.test(report.overallRecommendation.verdict)
                        ? "border-emerald-500/40 text-emerald-400 bg-emerald-500/10"
                        : /看空|卖出|强烈看空|超卖/.test(report.overallRecommendation.verdict)
                          ? "border-rose-500/40 text-rose-400 bg-rose-500/10"
                          : "border-surface-4 text-text-muted bg-surface-3"
                    }`}>
                      综合评级：{report.overallRecommendation.verdict}
                    </div>
                  )}
                  {report.overallRecommendation?.score != null && (
                    <div className="px-4 py-2 rounded-lg border border-surface-4 bg-surface-3 text-text font-semibold text-lg tabular-nums">
                      {report.overallRecommendation.score.toFixed(0)}
                      <span className="text-xs text-text-dim ml-1 font-normal">/ 100</span>
                    </div>
                  )}
                </div>
              </div>
              <div className="mt-4 text-xs text-text-dim italic border-t border-surface-4 pt-3">
                ⚠️ {report.deepReport.reportMeta?.disclaimer || "本报告为系统自动生成的研究框架，仅供参考，不构成投资建议。"}
              </div>
            </div>

            {/* 投资摘要（Investment Thesis）*/}
            {report.deepReport.investmentThesis?.bullets?.length > 0 && (
              <div className="card-base p-6">
                <div className="text-base font-semibold text-text mb-3 flex items-center gap-2">
                  <div className="w-1 h-5 bg-accent rounded-full" />
                  {report.deepReport.investmentThesis.title || "投资摘要 (Investment Thesis)"}
                </div>
                <div className="text-sm text-text-muted mb-4 leading-relaxed">
                  {report.deepReport.investmentThesis.narrative}
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {report.deepReport.investmentThesis.bullets.map((b: string, i: number) => (
                    <div key={i} className="text-sm text-text bg-surface-3/60 px-4 py-3 rounded-lg border border-surface-4 flex items-start gap-2">
                      <span className="text-accent font-bold">›</span>
                      <span className="leading-relaxed">{b}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 通用段落渲染函数：执行摘要 / 估值 / 基本面 / 护城河 / 技术 / 催化 / 风险 / 结论 */}
            {[
              { key: "executiveSummary", label: "执行摘要" },
              { key: "valuation", label: "估值分析" },
              { key: "fundamental", label: "基本面分析" },
              { key: "moat", label: "护城河与竞争地位" },
              { key: "technical", label: "技术分析与交易信号" },
              { key: "catalysts", label: "催化因素" },
              { key: "risks", label: "风险提示" },
              { key: "conclusion", label: "投资结论" },
            ].map(({ key, label }) => {
              const section = (report.deepReport as any)[key];
              if (!section) return null;
              const bullets = section.bullets || [];
              const hasContent = bullets.length > 0 || section.narrative;
              if (!hasContent) return null;
              const isRisks = key === "risks";
              const isConclusion = key === "conclusion";
              return (
                <div key={key} className={`card-base p-6 ${isConclusion ? "border-l-4 border-l-emerald-500/50" : isRisks ? "border-l-4 border-l-rose-500/40" : ""}`}>
                  <div className="text-base font-semibold text-text mb-3 flex items-center gap-2">
                    <div className={`w-1 h-5 rounded-full ${isRisks ? "bg-rose-400" : isConclusion ? "bg-emerald-400" : "bg-sky-400"}`} />
                    {section.title || label}
                  </div>
                  {section.narrative && (
                    <div className="text-sm text-text-muted mb-4 leading-relaxed">{section.narrative}</div>
                  )}
                  {bullets.length > 0 && (
                    <div className="space-y-2">
                      {bullets.map((b: string, i: number) => (
                        <div key={i} className={`text-sm text-text leading-relaxed px-3 py-2 rounded-lg border ${isRisks ? "border-rose-500/20 bg-rose-500/5" : "border-surface-4 bg-surface-3/40"} flex items-start gap-2`}>
                          <span className={`font-bold flex-shrink-0 ${isRisks ? "text-rose-400" : "text-accent"}`}>•</span>
                          <span className="leading-relaxed">{b}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
