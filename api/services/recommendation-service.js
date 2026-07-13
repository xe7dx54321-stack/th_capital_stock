export function getEnhancedRecommendation(
  overallRecommendation,
  valuationData, fundamentalsData, technicalData,
  moatReport, peerComparisonReport, catalystsReport,
  latestPrice
) {
  // --- 各维度归一化得分（0-100） ---
  // 1) 估值：基于 historicalPercentile（0-100，越高越便宜）
  //    如果没有 percentile，用 PE/PB 与同行均值的相对位置来估算
  let valScore = null;
  if (valuationData?.historicalPercentile != null) valScore = Number(valuationData.historicalPercentile);
  else if (valuationData?.pe != null && peerComparisonReport?.avg?.pe != null && peerComparisonReport.avg.pe > 0) {
    // PE 低于同行均值越多得分越高
    const ratio = valuationData.pe / peerComparisonReport.avg.pe;
    valScore = Math.max(0, Math.min(100, (1 - (ratio - 0.5)) * 60));
  }

  // 2) 基本面：基于 ROE 和 毛利率的组合
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

  // 3) 技术面：基于 trendStrength (0-10) 和 change 5d/20d
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
    // 波动率作为风险调节：过高会压低技术得分
    const vol = Number(technicalData.volatility20);
    if (vol > 0.5) tSub -= 10;
    tCnt++;
  }
  if (tCnt > 0) techScore = Math.max(0, Math.min(100, Math.round(tSub / tCnt)));

  // 4) 护城河：0-100 直接用
  const moatScore = moatReport?.totalScore;

  // 5) 同业对标：综合百分位（0-100，越高越领先）
  let peerScore = null;
  if (peerComparisonReport?.metrics && peerComparisonReport.metrics.length) {
    const validPct = peerComparisonReport.metrics.map((m) => m.percentile).filter((p) => p != null);
    if (validPct.length) peerScore = Math.round(validPct.reduce((a, b) => a + b, 0) / validPct.length);
  }

  // 6) 催化因素：-100 ~ +100 归一化到 0-100
  let catalystScore = null;
  if (catalystsReport?.catalystScore != null) {
    catalystScore = Math.round((Number(catalystsReport.catalystScore) + 100) / 2);
  }

  // --- 综合得分（加权求和，缺省的维度不参与权重分配） ---
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

  // --- 判决 ---
  let verdict = "观望";
  if (compositeScore != null) {
    if (compositeScore >= 75) verdict = "强烈看多";
    else if (compositeScore >= 60) verdict = "看多";
    else if (compositeScore >= 45) verdict = "中性偏多";
    else if (compositeScore >= 35) verdict = "中性";
    else if (compositeScore >= 25) verdict = "中性偏空";
    else verdict = "看空";
  }

  // --- 价格区间：基于最新价 + 估值/基本面信号 ---
  let entryPrice = null, targetPrice = null, stopLoss = null;
  if (latestPrice != null && !isNaN(latestPrice)) {
    // 安全边际：估值百分位越低，安全边际越大
    let safetyMargin = 0.08;
    if (valuationData?.historicalPercentile != null) safetyMargin = 0.05 + (1 - valuationData.historicalPercentile / 100) * 0.15;

    // 合理涨幅空间：基本面 + 护城河 + 催化因素 的综合判断
    let upside = 0.15; // 默认 15%
    if (fundScore != null) upside += (fundScore - 50) / 200;
    if (moatScore != null) upside += (moatScore - 50) / 250;
    if (catalystsReport?.catalystScore != null) upside += catalystsReport.catalystScore / 400;
    upside = Math.max(0.05, Math.min(0.60, upside));

    entryPrice = Number((latestPrice * (1 - safetyMargin / 2)).toFixed(2));
    targetPrice = Number((latestPrice * (1 + upside)).toFixed(2));
    stopLoss = Number((latestPrice * (1 - safetyMargin * 1.5)).toFixed(2));
  }

  // --- 仓位建议（半凯利公式 f* = (p*(b+1) - 1) / b） ---
  let suggestedPositionSize = null, confidence = null;
  let upsidePotential = null, downsideRisk = null;
  if (entryPrice != null && targetPrice != null && stopLoss != null && compositeScore != null) {
    const p = Math.max(0.30, Math.min(0.85, compositeScore / 100)); // 胜率
    const upsideAmount = targetPrice - entryPrice;
    const downsideAmount = entryPrice - stopLoss;
    if (upsideAmount > 0 && downsideAmount > 0) {
      const b = upsideAmount / downsideAmount; // 赔率
      const kelly = (p * (b + 1) - 1) / b;
      // 半凯利（比全凯利更保守）
      const halfKelly = kelly / 2;
      suggestedPositionSize = Number(Math.max(0.05, Math.min(0.40, halfKelly)).toFixed(2));
    }
    confidence = Number((0.4 + compositeScore / 250).toFixed(2));

    // === 上行空间 / 下行风险（基于最新价计算） ===
    // 注意：latestPrice 在调用时传入，用于计算实际盈亏比例
    if (latestPrice != null && latestPrice > 0) {
      upsidePotential = Number(((targetPrice - latestPrice) / latestPrice * 100).toFixed(1));
      downsideRisk = Number(((stopLoss - latestPrice) / latestPrice * 100).toFixed(1));
    }
  }

  // --- 数据质量评估 ---
  // 统计有多少个维度有有效数据，用于判断结论可信度
  const availableDims = [valScore, fundScore, techScore, moatScore, peerScore, catalystScore].filter(s => s != null && !isNaN(s)).length;
  const totalDims = 6;
  let dataQuality = "数据不足，结论仅供参考";
  if (availableDims >= 5) dataQuality = "数据完整";
  else if (availableDims >= 3) dataQuality = "部分数据缺失";
  else if (availableDims >= 1) dataQuality = "数据稀疏，建议谨慎";

  // --- 持有期判断 ---
  let timeHorizon = "中长线 (3-12 个月)";
  if (techScore != null && catalystScore != null) {
    if (techScore >= 70 && catalystScore >= 60) timeHorizon = "中短线 (1-3 个月)";
    else if (techScore <= 40 && catalystScore <= 40) timeHorizon = "长线 (12 个月以上)";
  } else if (moatScore != null && moatScore >= 70) {
    timeHorizon = "长线持有 (12 个月以上)";
  }

  // --- 推理过程（聚合关键证据） ---
  const reasoning = [];
  if (valScore != null) reasoning.push(`估值得分 ${valScore}/100（${valScore >= 60 ? "偏便宜" : valScore >= 40 ? "中性" : "偏贵"}）`);
  if (fundScore != null) reasoning.push(`基本面 ${fundScore}/100（${fundScore >= 70 ? "优质" : fundScore >= 50 ? "稳健" : "偏弱"}）`);
  if (techScore != null) reasoning.push(`技术面 ${techScore}/100（${techScore >= 60 ? "趋势良好" : "震荡或偏弱"}）`);
  if (moatScore != null) reasoning.push(`护城河 ${moatScore}/100（${moatScore >= 60 ? "有竞争壁垒" : "壁垒不明显"}）`);
  if (peerScore != null) reasoning.push(`行业对标 ${peerScore}/100（${peerScore >= 60 ? "行业前列" : "行业中游或以下"}）`);
  if (catalystScore != null) reasoning.push(`催化评分 ${catalystScore}/100（${catalystScore >= 60 ? "情绪积极" : catalystScore >= 40 ? "中性" : "情绪偏弱"}）`);

  return {
    ...overallRecommendation,
    verdict,
    score: compositeScore != null ? compositeScore : (overallRecommendation?.score ?? null),
    compositeScore: compositeScore != null ? compositeScore : (overallRecommendation?.score ?? null),
    entryPrice,
    targetPrice,
    stopLoss,
    suggestedPositionSize,
    upsidePotential,
    downsideRisk,
    confidence,
    dataQuality,
    timeHorizon,
    reasoning: reasoning.length ? reasoning.join("；") + "。综合以上给出决策。" : (overallRecommendation?.text || "数据不足，无法给出综合建议"),
    // 保留原始文本供前端展示
    text: overallRecommendation?.text || "",
    bullSignals: overallRecommendation?.bullSignals || 0,
    bearSignals: overallRecommendation?.bearSignals || 0,
  };
}

