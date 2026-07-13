import { getStockName } from "../registries/stock-registry.js";
import { getMoatReport } from "./research-analysis-service.js";


export function getTechnicalData(db, code, factorMap, priceHistory) {
  const rsi14 = factorMap["rsi_14"] != null ? Number(factorMap["rsi_14"]) : null;
  const macdHist = factorMap["macd_hist"] != null ? Number(factorMap["macd_hist"]) : null;
  const macdDif = factorMap["macd_dif"] != null ? Number(factorMap["macd_dif"]) : null;
  const macdDea = factorMap["macd_dea"] != null ? Number(factorMap["macd_dea"]) : null;
  const trendStrength = factorMap["trend_strength"] != null ? Number(factorMap["trend_strength"]) : null;
  const volatility20 = factorMap["volatility_20"] != null ? Number(factorMap["volatility_20"]) : null;
  const ma20 = factorMap["ma_20"] != null ? Number(factorMap["ma_20"]) : null;

  let change5d = null, change20d = null;
  if (priceHistory && priceHistory.length >= 2) {
    const latest = priceHistory[priceHistory.length - 1]?.close;
    const p5 = priceHistory[Math.max(0, priceHistory.length - 5)]?.close;
    const p20 = priceHistory[Math.max(0, priceHistory.length - 20)]?.close;
    if (latest && p5 && p5 > 0) change5d = (latest / p5 - 1) * 100;
    if (latest && p20 && p20 > 0) change20d = (latest / p20 - 1) * 100;
  }
  const latestClose = priceHistory && priceHistory.length ? priceHistory[priceHistory.length - 1]?.close : null;

  const keyFields = [rsi14, macdHist, macdDif, macdDea, trendStrength, volatility20, change5d, change20d];
  const dataQuality = Math.round((keyFields.filter(v => v != null).length / keyFields.length) * 100);

  return {
    rsi14, macdHist, macdDif, macdDea, trendStrength, volatility20, ma20,
    change5d, change20d, latestClose,
    // 兼容字段：latestPrice 与 latestClose 相同，供后续价格计算逻辑使用
    latestPrice: latestClose,
    dataQuality,
  };
}

export function computeUnifiedScore(valuationData, fundamentalsData, technicalData, moatReport) {
  // 1) 估值：historicalPercentile 直接用（0-100，越高越便宜）
  let valScore = null;
  if (valuationData?.historicalPercentile != null) valScore = Number(valuationData.historicalPercentile);
  else if (valuationData?.pe != null && !isNaN(valuationData.pe) && valuationData.pe > 0) {
    const pe = valuationData.pe;
    if (pe < 15) valScore = 80;
    else if (pe < 25) valScore = 60;
    else if (pe < 40) valScore = 40;
    else valScore = 20;
  }

  // 2) 基本面：ROE + 毛利率 + 营收同比
  let fundScore = null;
  let fSub = 0, fCnt = 0;
  if (fundamentalsData?.roe != null) {
    const roe = Number(fundamentalsData.roe);
    if (roe > 0.20) fSub += 90;
    else if (roe > 0.15) fSub += 80;
    else if (roe > 0.08) fSub += 60;
    else if (roe > 0) fSub += 40;
    else fSub += 20;
    fCnt++;
  }
  if (fundamentalsData?.grossMargin != null) {
    const gm = Number(fundamentalsData.grossMargin);
    if (gm > 0.40) fSub += 90;
    else if (gm > 0.25) fSub += 75;
    else if (gm > 0.10) fSub += 60;
    else fSub += 40;
    fCnt++;
  }
  if (fundamentalsData?.revenueYoY != null) {
    const r = Number(fundamentalsData.revenueYoY);
    if (r > 20) fSub += 90;
    else if (r > 10) fSub += 75;
    else if (r > 0) fSub += 60;
    else fSub += 30;
    fCnt++;
  }
  if (fCnt > 0) fundScore = Math.round(fSub / fCnt);

  // 3) 技术面：trendStrength + change20d + volatility20
  let techScore = null;
  let tSub = 0, tCnt = 0;
  if (technicalData?.trendStrength != null) {
    tSub += Number(technicalData.trendStrength) * 10;
    tCnt++;
  }
  if (technicalData?.change20d != null) {
    const c20 = Number(technicalData.change20d);
    if (c20 > 15) tSub += 90;
    else if (c20 > 5) tSub += 75;
    else if (c20 > -5) tSub += 55;
    else if (c20 > -15) tSub += 35;
    else tSub += 20;
    tCnt++;
  }
  if (technicalData?.volatility20 != null) {
    const vol = Number(technicalData.volatility20);
    if (vol > 0.5) tSub -= 10;
    tCnt++;
  }
  if (tCnt > 0) techScore = Math.max(0, Math.min(100, Math.round(tSub / tCnt)));

  // 4) 护城河：使用完整的 getMoatReport 引擎（与详情页一致）
  const moatScore = moatReport?.totalScore;

  // 5-6) 同业对标 & 催化因素：列表页快速计算（在详情页完整版另行计算）
  const peerScore = null;
  const catalystScore = null;

  // === 综合得分（权重与详情页 getEnhancedRecommendation 完全一致）
  const weights = { valScore: 0.20, fundScore: 0.25, techScore: 0.15, moatScore: 0.15, peerScore: 0.10, catalystScore: 0.15 };
  const scoreItems = { valScore, fundScore, techScore, moatScore, peerScore, catalystScore };
  let totalWeight = 0;
  let weighted = 0;
  for (const key of Object.keys(weights)) {
    const s = scoreItems[key];
    if (s != null && !isNaN(s)) {
      weighted += s * weights[key];
      totalWeight += weights[key];
    }
  }
  const compositeScore = totalWeight > 0 ? Math.round(weighted / totalWeight) : null;

  // === verdict 阈值与详情页保持一致
  let verdict = "观望";
  if (compositeScore != null) {
    if (compositeScore >= 75) verdict = "强烈看多";
    else if (compositeScore >= 60) verdict = "看多";
    else if (compositeScore >= 45) verdict = "中性偏多";
    else if (compositeScore >= 35) verdict = "中性";
    else if (compositeScore >= 25) verdict = "中性偏空";
    else verdict = "看空";
  }

  return { valScore, fundScore, techScore, moatScore, peerScore, catalystScore, compositeScore, verdict };
}

export function buildValueScores(inputs, now = new Date()) {
  const scores = inputs.map((input) => {
    const { tsCode, sector, factorMap, priceHistory, latestPrice, valuationData, fundamentalsData, peerGroupData } = input;
    let market = "其他";
    if (tsCode.endsWith(".SH") || tsCode.endsWith(".SZ")) market = "A";
    else if (tsCode.endsWith(".HK")) market = "H";
    else if (/^[A-Z]/.test(tsCode)) market = "US";

    const technicalData = getTechnicalData(null, tsCode, factorMap, priceHistory);
    const moatReport = getMoatReport(fundamentalsData, peerGroupData);
    const unified = computeUnifiedScore(valuationData, fundamentalsData, technicalData, moatReport);
    const closes = priceHistory.slice(-30).filter((item) => item?.close != null);
    let change5d = null;
    let change20d = null;
    if (closes.length >= 6) {
      const latest = closes[closes.length - 1].close;
      const previous = closes[Math.max(0, closes.length - 5)].close;
      if (latest && previous && previous > 0) change5d = (latest / previous - 1) * 100;
    }
    if (closes.length >= 21) {
      const latest = closes[closes.length - 1].close;
      const previous = closes[Math.max(0, closes.length - 20)].close;
      if (latest && previous && previous > 0) change20d = (latest / previous - 1) * 100;
    }

    return {
      tsCode,
      name: getStockName(tsCode) || tsCode,
      market,
      compositeScore: unified.compositeScore != null ? Math.round(unified.compositeScore) / 10 : null,
      fundamentalQuality: unified.fundScore != null ? Math.round(unified.fundScore) / 10 : null,
      valuationPosition: unified.valScore != null ? Math.round(unified.valScore) / 10 : null,
      technicalMomentum: unified.techScore != null ? Math.round(unified.techScore) / 10 : null,
      themeRelevance: unified.moatScore != null ? Math.round(unified.moatScore) / 10 : null,
      industryPosition: unified.moatScore != null ? Math.round(unified.moatScore) / 10 : null,
      sector: sector || "未分类",
      latestClose: latestPrice != null ? Number(latestPrice.toFixed(2)) : null,
      verdict: unified.verdict,
      pePercentile: valuationData?.historicalPercentile,
      momentum5d: change5d != null ? Math.round(change5d * 10) / 10 : null,
      momentum20d: change20d != null ? Math.round(change20d * 10) / 10 : null,
      macdSignal: technicalData?.macdHist != null ? (technicalData.macdHist > 0 ? "bullish" : "bearish") : null,
    };
  });
  scores.sort((a, b) => (b.compositeScore || 0) - (a.compositeScore || 0));
  return { scores, updatedAt: now.toISOString() };
}
