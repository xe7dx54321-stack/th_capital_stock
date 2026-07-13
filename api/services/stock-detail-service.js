import { getStockName } from "../registries/stock-registry.js";
import { getDeepReport } from "./deep-report-service.js";
import { getEnhancedRecommendation } from "./recommendation-service.js";
import { getMoatReport, getPeerComparisonReport } from "./research-analysis-service.js";
import { getCatalystsReport } from "./report-service.js";
import { computeUnifiedScore, getTechnicalData } from "./scoring-service.js";


function marketForCode(code) {
  if (code.endsWith(".SH") || code.endsWith(".SZ")) return "A";
  if (code.endsWith(".HK")) return "H";
  if (/^[A-Z]+$/.test(code)) return "US";
  return "其他";
}

function finite(value) {
  return value != null && Number.isFinite(Number(value)) ? Number(value) : null;
}

function percentValue(value) {
  const number = finite(value);
  if (number == null) return null;
  return Math.abs(number) <= 1 ? number * 100 : number;
}

function metricItem(metric, value, suffix, text, label = "参考") {
  const number = finite(value);
  if (number == null) return null;
  return {
    label,
    metric,
    value: `${number.toFixed(2)}${suffix}`,
    text,
  };
}

function buildValuationReport(data) {
  const items = [
    metricItem("PE（TTM）", data.pe, " 倍", "市盈率用于衡量当前价格对应的盈利估值。", data.pe < 15 ? "偏低" : data.pe > 40 ? "偏高" : "合理"),
    metricItem("PB", data.pb, " 倍", "市净率用于观察价格相对净资产的溢价。", data.pb < 1 ? "破净" : data.pb > 5 ? "偏高" : "合理"),
    metricItem("PS（TTM）", data.ps, " 倍", "市销率适合辅助观察尚处成长阶段的公司。"),
    metricItem("EV/EBITDA", data.evEbitda, " 倍", "企业价值倍数用于跨资本结构比较。"),
    metricItem("历史估值百分位", data.historicalPercentile, "%", "百分位越低，通常代表估值更接近自身历史低位。"),
  ].filter(Boolean);
  return {
    score: finite(data.confidence),
    pe: finite(data.pe),
    pb: finite(data.pb),
    ps: finite(data.ps),
    evEbitda: finite(data.evEbitda),
    marginOfSafety: finite(data.historicalPercentile),
    historicalPercentile: finite(data.historicalPercentile),
    brokerTargetPrice: finite(data.brokerTargetPrice),
    targetPrice: finite(data.brokerTargetPrice),
    summary: items.length ? "估值指标已汇总，建议结合盈利质量、行业位置和历史区间综合判断。" : "暂无可用的估值数据。",
    items,
  };
}

function buildFundamentalsReport(data) {
  const grossMargin = percentValue(data.grossMargin);
  const netMargin = percentValue(data.netMargin);
  const roe = percentValue(data.roe);
  const items = [
    metricItem("毛利率", grossMargin, "%", "毛利率反映产品或服务的基础盈利空间。", grossMargin >= 40 ? "较强" : grossMargin >= 20 ? "稳健" : "关注"),
    metricItem("净利率", netMargin, "%", "净利率反映收入最终转化为利润的效率。", netMargin >= 15 ? "较强" : netMargin >= 5 ? "稳健" : "关注"),
    metricItem("ROE", roe, "%", "净资产收益率用于衡量股东资本的使用效率。", roe >= 15 ? "较强" : roe >= 8 ? "稳健" : "关注"),
    metricItem("营收同比", data.revenueYoY, "%", "营收同比用于观察业务扩张速度。", data.revenueYoY > 10 ? "增长" : data.revenueYoY < 0 ? "下滑" : "平稳"),
    metricItem("净利润同比", data.netProfitYoY, "%", "净利润同比用于观察盈利增长质量。", data.netProfitYoY > 10 ? "增长" : data.netProfitYoY < 0 ? "下滑" : "平稳"),
  ].filter(Boolean);
  return {
    summary: items.length ? "核心盈利、成长与资本效率指标已汇总，后续应继续核对现金流和负债结构。" : "暂无完整的基本面数据。",
    items,
    sourceQuality: data.sourceQuality || null,
    freshness: data.freshness || null,
    earningsQuality: finite(data.earningsQuality),
    earningsQualityDesc: data.earningsQualityDesc || "",
    growthQuality: finite(data.growthQuality),
    growthQualityDesc: data.growthQualityDesc || "",
    financialHealth: finite(data.financialHealth),
    financialHealthDesc: data.financialHealthDesc || "",
  };
}

function buildTechnicalReport(data) {
  const items = [
    metricItem("RSI（14）", data.rsi14, "", "RSI 用于观察短期超买或超卖程度。", data.rsi14 > 70 ? "偏热" : data.rsi14 < 30 ? "偏冷" : "中性"),
    metricItem("MACD 柱", data.macdHist, "", "MACD 柱用于辅助判断趋势动能方向。", data.macdHist > 0 ? "偏多" : data.macdHist < 0 ? "偏空" : "中性"),
    metricItem("5 日涨跌", data.change5d, "%", "近五个交易日价格变化。", data.change5d > 0 ? "上涨" : data.change5d < 0 ? "下跌" : "持平"),
    metricItem("20 日涨跌", data.change20d, "%", "近二十个交易日价格变化。", data.change20d > 0 ? "上涨" : data.change20d < 0 ? "下跌" : "持平"),
    metricItem("趋势强度", data.trendStrength, "", "趋势强度用于衡量价格方向的一致性。"),
  ].filter(Boolean);
  return {
    summary: items.length ? "技术指标仅用于描述当前价格状态，不单独构成投资结论。" : "暂无足够的技术面数据。",
    items,
  };
}

function buildBaseRecommendation(technicalData, newsClaimsData) {
  const signals = [technicalData.change20d, technicalData.macdHist, technicalData.trendStrength]
    .map(finite)
    .filter((value) => value != null);
  const bullSignals = signals.filter((value) => value > 0).length;
  const bearSignals = signals.filter((value) => value < 0).length + (newsClaimsData.risks?.length || 0);
  return {
    verdict: bullSignals > bearSignals ? "偏多" : bearSignals > bullSignals ? "偏空" : "观望",
    text: signals.length ? "已根据估值、基本面、技术面与事件信息生成综合判断。" : "当前数据不足，建议先补齐证据再做判断。",
    score: null,
    bullSignals,
    bearSignals,
  };
}

export function buildStockDetail(code, input, now = new Date()) {
  const {
    poolInfo,
    factorMap,
    priceHistory,
    valuationData,
    fundamentalsData,
    peerGroupData,
    moatPeerAvg,
    newsClaimsData,
  } = input;
  const market = marketForCode(code);
  const name = getStockName(code) || code;
  const technicalData = getTechnicalData(null, code, factorMap, priceHistory);
  const latestPrice = finite(technicalData.latestPrice) ?? finite(valuationData.currentPrice);
  const moatReport = getMoatReport(fundamentalsData, moatPeerAvg);
  const peerComparisonReport = getPeerComparisonReport(
    valuationData,
    fundamentalsData,
    technicalData,
    peerGroupData,
  );
  const catalystsReport = getCatalystsReport(newsClaimsData);
  const baseRecommendation = buildBaseRecommendation(technicalData, newsClaimsData);
  const recommendation = getEnhancedRecommendation(
    baseRecommendation,
    valuationData,
    fundamentalsData,
    technicalData,
    moatReport,
    peerComparisonReport,
    catalystsReport,
    latestPrice,
  );
  const unified = computeUnifiedScore(valuationData, fundamentalsData, technicalData, moatReport);
  if (unified.compositeScore != null) {
    recommendation.score = unified.compositeScore;
    recommendation.compositeScore = unified.compositeScore;
  }
  if (unified.verdict) recommendation.verdict = unified.verdict;

  const deepReport = getDeepReport(
    code,
    name,
    market,
    poolInfo.sector || "",
    latestPrice,
    valuationData,
    fundamentalsData,
    technicalData,
    moatReport,
    peerComparisonReport,
    catalystsReport,
    recommendation,
  );

  return {
    tsCode: code,
    name,
    market,
    sector: poolInfo.sector || "",
    poolType: poolInfo.pool_type || "",
    addedDate: poolInfo.added_date || "",
    latestPrice,
    priceHistory,
    factors: factorMap,
    news: newsClaimsData.news || [],
    report: {
      overallRecommendation: recommendation,
      valuation: buildValuationReport(valuationData),
      fundamentals: buildFundamentalsReport(fundamentalsData),
      technical: buildTechnicalReport(technicalData),
      riskAlerts: newsClaimsData.risks || [],
      claims: newsClaimsData.claims || [],
      moat: moatReport,
      peerComparison: peerComparisonReport,
      catalysts: catalystsReport,
      deepReport,
    },
    updatedAt: now.toISOString(),
  };
}
