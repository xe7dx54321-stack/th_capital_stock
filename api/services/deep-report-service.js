export function getDeepReport(
  tsCode, name, market, sector, latestPrice,
  valuationData, fundamentalsData, technicalData,
  moatReport, peerComparisonReport, catalystsReport,
  enhancedRecommendation
) {
  // --- 工具：根据数值和阈值生成定性描述
  function describe(v, thresholds, labels) {
    if (v == null || isNaN(v)) return null;
    for (let i = 0; i < thresholds.length; i++) {
      if (v >= thresholds[i]) return labels[i];
    }
    return labels[labels.length - 1];
  }

  // --- 工具：把数值格式化成可读字符串（百分比/小数点）
  function fmt(v, digits = 2) {
    if (v == null || isNaN(v)) return "—";
    return Number(v).toFixed(digits);
  }
  function fmtPct(v) {
    if (v == null || isNaN(v)) return "—";
    return (v * 100).toFixed(1) + "%";
  }

  const ratingMap = {
    "强烈看多": "BUY（买入）",
    "看多": "OUTPERFORM（增持）",
    "中性偏多": "NEUTRAL+（中性偏多）",
    "中性": "HOLD（持有）",
    "中性偏空": "NEUTRAL-（中性偏空）",
    "看空": "UNDERPERFORM（减持）",
    "强烈看空": "SELL（卖出）",
  };

  const verdict = enhancedRecommendation?.verdict || "中性";
  const rating = ratingMap[verdict] || "HOLD";
  const entry = enhancedRecommendation?.entryPrice;
  const target = enhancedRecommendation?.targetPrice;
  const stopLoss = enhancedRecommendation?.stopLoss;
  const upside = (latestPrice && target) ? ((target / latestPrice - 1) * 100).toFixed(1) + "%" : null;
  const downside = (latestPrice && stopLoss) ? ((stopLoss / latestPrice - 1) * 100).toFixed(1) + "%" : null;

  // ============================================================
  // 1. 投资摘要 (Investment Thesis)
  // ============================================================
  const thesisBullets = [];
  thesisBullets.push(`评级：${rating}（综合得分 ${enhancedRecommendation?.score != null ? enhancedRecommendation.score.toFixed(0) + "/100" : "—"}）`);
  if (entry != null) thesisBullets.push(`建议买入价：${entry.toFixed(2)}`);
  if (target != null) thesisBullets.push(`目标价：${target.toFixed(2)}（潜在上行空间 ${upside || "—"}）`);
  if (stopLoss != null) thesisBullets.push(`止损价：${stopLoss.toFixed(2)}（最大下行 ${downside || "—"}）`);
  if (enhancedRecommendation?.suggestedPositionSize) thesisBullets.push(`建议仓位：${enhancedRecommendation.suggestedPositionSize}`);
  if (enhancedRecommendation?.timeHorizon) thesisBullets.push(`建议持有期：${enhancedRecommendation.timeHorizon}`);
  if (enhancedRecommendation?.confidence != null) thesisBullets.push(`置信度：${(enhancedRecommendation.confidence * 100).toFixed(0)}%`);

  // ============================================================
  // 2. 执行摘要要点 (Executive Summary)
  // ============================================================
  const execSummary = [];
  execSummary.push(`${name}（${tsCode}）${sector ? "属" + sector + "板块" : ""}，${market ? market + "股市场交易" : ""}。当前价 ${fmt(latestPrice)}。`);

  // 估值要点
  if (valuationData?.pe != null) {
    const pe = valuationData.pe;
    if (pe > 0 && pe < 15) execSummary.push(`估值：PE = ${fmt(pe)}，处于低估区间，估值提供一定安全边际。`);
    else if (pe > 0 && pe < 30) execSummary.push(`估值：PE = ${fmt(pe)}，估值合理，与当前盈利水平匹配。`);
    else if (pe > 0) execSummary.push(`估值：PE = ${fmt(pe)}，估值偏高，需评估盈利增长能否支撑当前估值。`);
    else execSummary.push(`估值：PE 为负值，公司处于亏损状态，需关注盈利拐点。`);
  }
  if (valuationData?.pb != null) {
    const pb = valuationData.pb;
    if (pb < 1) execSummary.push(`PB = ${fmt(pb)}，已跌破净资产，存在深度价值机会或基本面风险信号。`);
    else if (pb < 3) execSummary.push(`PB = ${fmt(pb)}，估值水平温和。`);
    else execSummary.push(`PB = ${fmt(pb)}，估值溢价较为明显。`);
  }
  if (valuationData?.historicalPercentile != null) {
    execSummary.push(`历史估值百分位：${fmt(valuationData.historicalPercentile, 0)}%，${valuationData.historicalPercentile < 30 ? "低于历史上多数时间，估值有吸引力" : valuationData.historicalPercentile > 70 ? "高于历史上多数时间，需警惕回调" : "处于历史中性区间"}。`);
  }

  // 基本面要点
  if (fundamentalsData?.revenueYoY != null) {
    const rev = fundamentalsData.revenueYoY;
    execSummary.push(`营收同比增长 ${fmtPct(rev)}，${rev >= 0.15 ? "增速强劲" : rev >= 0.05 ? "稳健增长" : rev > 0 ? "温和增长" : "面临下滑压力"}。`);
  }
  if (fundamentalsData?.roe != null) {
    execSummary.push(`ROE = ${fmtPct(fundamentalsData.roe)}，${fundamentalsData.roe >= 0.15 ? "盈利能力优秀" : fundamentalsData.roe >= 0.08 ? "盈利能力中等" : fundamentalsData.roe > 0 ? "盈利能力偏弱" : "处于亏损状态"}。`);
  }
  if (fundamentalsData?.grossMargin != null) {
    execSummary.push(`毛利率 = ${fmtPct(fundamentalsData.grossMargin)}，${fundamentalsData.grossMargin >= 0.4 ? "毛利水平高，议价能力强" : fundamentalsData.grossMargin >= 0.2 ? "毛利中等" : "毛利偏低，竞争激烈"}。`);
  }
  if (fundamentalsData?.debtToEquity != null) {
    execSummary.push(`资产负债率 = ${fmt(fundamentalsData.debtToEquity, 2)}，${fundamentalsData.debtToEquity > 1 ? "杠杆偏高，财务风险较大" : fundamentalsData.debtToEquity > 0.6 ? "杠杆中等" : "财务结构稳健"}。`);
  }

  // 技术面要点
  if (technicalData?.trendStrength != null) {
    execSummary.push(`趋势强度 = ${fmt(technicalData.trendStrength, 2)}，${technicalData.trendStrength >= 0.7 ? "上升趋势明确，多头排列" : technicalData.trendStrength >= 0.4 ? "趋势中性偏多" : technicalData.trendStrength > 0.2 ? "震荡偏弱" : "下跌趋势明显"}。`);
  }
  if (technicalData?.rsi14 != null) {
    execSummary.push(`RSI(14) = ${fmt(technicalData.rsi14, 1)}，${technicalData.rsi14 >= 70 ? "超买区域，短期需警惕回调" : technicalData.rsi14 >= 50 ? "多头区域，动能健康" : technicalData.rsi14 >= 30 ? "中性偏弱" : "超卖区域，可能存在反弹机会"}。`);
  }
  if (technicalData?.volatility20 != null) {
    execSummary.push(`20日波动率 = ${fmtPct(technicalData.volatility20)}，${technicalData.volatility20 > 0.4 ? "波动剧烈，需严格止损" : technicalData.volatility20 > 0.25 ? "波动中等偏高" : "波动平稳，持仓成本可控"}。`);
  }

  // ============================================================
  // 3. 估值分析 (Valuation Analysis) —— 详细版
  // ============================================================
  const valuationSection = {
    title: "估值分析 (Valuation Analysis)",
    bullets: [],
    narrative: "",
  };
  if (valuationData?.pe != null && valuationData.pe > 0) {
    valuationSection.bullets.push(`PE(TTM) = ${fmt(valuationData.pe)}`);
    const peerPe = peerComparisonReport?.metrics?.find(m => m.name === "PE");
    if (peerPe) valuationSection.bullets.push(`行业均值 PE = ${fmt(peerPe.peerAvg)}，百分位 ${fmt(peerPe.percentile, 0)}%，${peerPe.percentile < 30 ? "估值较同行显著折价" : peerPe.percentile > 70 ? "估值较同行显著溢价" : "估值与同行相当"}`);
  }
  if (valuationData?.pb != null) {
    valuationSection.bullets.push(`PB = ${fmt(valuationData.pb)}`);
    const peerPb = peerComparisonReport?.metrics?.find(m => m.name === "PB");
    if (peerPb) valuationSection.bullets.push(`行业均值 PB = ${fmt(peerPb.peerAvg)}，百分位 ${fmt(peerPb.percentile, 0)}%`);
  }
  if (valuationData?.analystTargetPrice != null) {
    valuationSection.bullets.push(`券商一致预期目标价 = ${fmt(valuationData.analystTargetPrice)}`);
  }
  if (valuationData?.marginOfSafety != null) {
    valuationSection.bullets.push(`安全边际 = ${fmtPct(valuationData.marginOfSafety)}`);
  }
  valuationSection.narrative = valuationSection.bullets.length
    ? `${name} 当前估值水平${(valuationData?.historicalPercentile != null && valuationData.historicalPercentile < 40) ? "相对历史低位" : (valuationData?.historicalPercentile != null && valuationData.historicalPercentile > 60) ? "相对历史高位" : "中性"}。建议投资者结合公司盈利增速和行业景气度综合判断。`
    : "暂无足够的估值数据进行详细分析。";

  // ============================================================
  // 4. 基本面分析 (Fundamental Analysis) —— 详细版
  // ============================================================
  const fundamentalSection = {
    title: "基本面分析 (Fundamental Analysis)",
    bullets: [],
    narrative: "",
  };
  if (fundamentalsData?.revenue != null) fundamentalSection.bullets.push(`营收规模 = ${fmt(fundamentalsData.revenue / 1e8, 2)} 亿元`);
  if (fundamentalsData?.revenueYoY != null) fundamentalSection.bullets.push(`营收同比 = ${fmtPct(fundamentalsData.revenueYoY)}`);
  if (fundamentalsData?.netProfitYoY != null) fundamentalSection.bullets.push(`净利润同比 = ${fmtPct(fundamentalsData.netProfitYoY)}`);
  if (fundamentalsData?.roe != null) fundamentalSection.bullets.push(`ROE = ${fmtPct(fundamentalsData.roe)}`);
  if (fundamentalsData?.grossMargin != null) fundamentalSection.bullets.push(`毛利率 = ${fmtPct(fundamentalsData.grossMargin)}`);
  if (fundamentalsData?.fcfYield != null) fundamentalSection.bullets.push(`自由现金流收益率 = ${fmtPct(fundamentalsData.fcfYield)}`);
  if (fundamentalsData?.currentRatio != null) fundamentalSection.bullets.push(`流动比率 = ${fmt(fundamentalsData.currentRatio, 2)}`);
  if (fundamentalsData?.debtToEquity != null) fundamentalSection.bullets.push(`资产负债率 = ${fmt(fundamentalsData.debtToEquity, 2)}`);
  fundamentalSection.narrative = fundamentalSection.bullets.length
    ? `公司盈利能力${(fundamentalsData?.roe && fundamentalsData.roe >= 0.15) ? "优秀" : (fundamentalsData?.roe && fundamentalsData.roe >= 0.08) ? "稳健" : "偏弱"}。营收趋势${(fundamentalsData?.revenueYoY != null && fundamentalsData.revenueYoY >= 0.1) ? "向上" : (fundamentalsData?.revenueYoY != null && fundamentalsData.revenueYoY > 0) ? "平稳" : "承压"}。财务结构${(fundamentalsData?.debtToEquity != null && fundamentalsData.debtToEquity < 0.6) ? "稳健" : "有一定杠杆压力"}。`
    : "暂无足够的基本面数据进行详细分析。";

  // ============================================================
  // 5. 护城河与竞争地位 (Moat & Competitive Positioning)
  // ============================================================
  const moatSection = {
    title: "护城河与竞争地位 (Moat & Competitive Positioning)",
    bullets: [],
    narrative: "",
  };
  if (moatReport?.totalScore != null) {
    moatSection.bullets.push(`综合护城河评分 = ${moatReport.totalScore}/100（${describe(moatReport.totalScore, [75, 55, 35], ["宽护城河", "中等护城河", "窄护城河"]) || "弱护城河"}）`);
    moatReport.dimensions?.forEach(d => {
      moatSection.bullets.push(`${d.name}：${d.score}分 — ${d.evidence || d.summary || ""}`);
    });
  }
  if (peerComparisonReport?.industryPosition) {
    moatSection.bullets.push(`行业地位：${peerComparisonReport.industryPosition}`);
    peerComparisonReport.metrics?.forEach(m => {
      if (m.value != null) moatSection.bullets.push(`${m.name}：本公司 ${fmt(m.value, 2)}，同行均值 ${fmt(m.peerAvg, 2)}，百分位 ${fmt(m.percentile, 0)}%`);
    });
  }
  moatSection.narrative = moatSection.bullets.length
    ? `从 6 大维度评估公司的长期竞争优势：${(moatReport?.totalScore && moatReport.totalScore >= 60) ? "公司具备可持续的竞争壁垒，在品牌溢价、成本优势或网络效应等方面有明显优势，值得长期关注。" : "公司尚未形成深厚的护城河，行业竞争较激烈，需关注管理层战略与资源配置能力。"}`
    : "暂无护城河相关的详细数据。";

  // ============================================================
  // 6. 技术分析与交易信号 (Technical Analysis)
  // ============================================================
  const technicalSection = {
    title: "技术分析与交易信号 (Technical Analysis)",
    bullets: [],
    narrative: "",
  };
  if (technicalData?.trendStrength != null) technicalSection.bullets.push(`趋势强度 = ${fmt(technicalData.trendStrength, 2)}（0-1，越高趋势越强）`);
  if (technicalData?.rsi14 != null) technicalSection.bullets.push(`RSI(14) = ${fmt(technicalData.rsi14, 1)}`);
  if (technicalData?.macd != null) {
    const s = technicalData.macd;
    technicalSection.bullets.push(`MACD：DIF = ${fmt(s.dif, 2)}，DEA = ${fmt(s.dea, 2)}，柱状 = ${fmt(s.hist, 2)}（${s.hist > 0 ? "正值，动能偏多" : "负值，动能偏弱"}）`);
  }
  if (technicalData?.ma20 != null) technicalSection.bullets.push(`MA(20) = ${fmt(technicalData.ma20, 2)}`);
  if (technicalData?.support != null) technicalSection.bullets.push(`近期支撑位 = ${fmt(technicalData.support, 2)}`);
  if (technicalData?.resistance != null) technicalSection.bullets.push(`近期阻力位 = ${fmt(technicalData.resistance, 2)}`);
  if (technicalData?.momentum5d != null) technicalSection.bullets.push(`5日动量 = ${fmtPct(technicalData.momentum5d)}`);
  if (technicalData?.momentum20d != null) technicalSection.bullets.push(`20日动量 = ${fmtPct(technicalData.momentum20d)}`);
  technicalSection.narrative = technicalSection.bullets.length
    ? `技术面${(technicalData?.trendStrength && technicalData.trendStrength >= 0.5) ? "偏多，趋势向上" : (technicalData?.trendStrength && technicalData.trendStrength >= 0.3) ? "中性，横盘震荡" : "偏弱，趋势向下"}。当前 ${technicalData?.rsi14 ? "RSI 位于 " + technicalData.rsi14.toFixed(1) + " 点水平" : ""}。建议结合基本面的估值判断综合决策。`
    : "暂无足够的技术指标进行详细分析。";

  // ============================================================
  // 7. 催化因素 (Catalysts)
  // ============================================================
  const catalystsSection = {
    title: "催化因素 (Catalysts) — 潜在的股价驱动事件",
    bullets: [],
    narrative: "",
  };
  catalystsSection.bullets.push(`综合催化评分 = ${fmt(catalystsReport?.catalystScore, 0)}/100（${describe(catalystsReport?.catalystScore, [60, 40], ["情绪积极", "情绪中性", "情绪偏弱"]) || "—"}）`);
  catalystsSection.bullets.push(`市场情绪方向：${catalystsReport?.netDirection || "中性"}`);
  if (catalystsReport?.newsSentiment != null) catalystsSection.bullets.push(`新闻情绪 = ${fmt(catalystsReport.newsSentiment, 1)}/100`);
  if (catalystsReport?.researchStance != null) catalystsSection.bullets.push(`研究主张 = ${fmt(catalystsReport.researchStance, 1)}/100`);
  if (catalystsReport?.newsWithSentiment && catalystsReport.newsWithSentiment.length > 0) {
    catalystsReport.newsWithSentiment.slice(0, 5).forEach(n => {
      catalystsSection.bullets.push(`新闻【${n.sentiment || "中性"}】：${n.title || n.content || "（无标题）"}`);
    });
  }
  if (catalystsReport?.claimsWithSentiment && catalystsReport.claimsWithSentiment.length > 0) {
    catalystsReport.claimsWithSentiment.slice(0, 5).forEach(c => {
      catalystsSection.bullets.push(`研究主张【${c.stance || c.sentiment || "中性"}】：${c.claimText || c.title || "（无内容）"}`);
    });
  }
  catalystsSection.narrative = catalystsSection.bullets.length > 2
    ? `当前市场对 ${name} 的情绪${(catalystsReport?.catalystScore && catalystsReport.catalystScore >= 50) ? "整体偏积极，存在正向催化的可能性" : (catalystsReport?.catalystScore && catalystsReport.catalystScore >= 30) ? "中性，需等待更多基本面信息" : "整体偏谨慎，可能存在负面压力"}。建议持续关注新闻事件与公司公告。`
    : "暂无催化因素相关的显著数据。";

  // ============================================================
  // 8. 风险提示 (Risks)
  // ============================================================
  const riskSection = {
    title: "风险提示 (Key Risks)",
    bullets: [],
    narrative: "",
  };
  riskSection.bullets.push("宏观风险：宏观经济下行、利率上行、流动性收紧可能对股价形成压制");
  riskSection.bullets.push("行业风险：行业竞争加剧、技术路线变化、政策监管变化");
  riskSection.bullets.push("公司风险：管理层战略执行不达预期、关键客户流失、财务恶化");
  riskSection.bullets.push("估值风险：若盈利不及预期，估值可能下杀（需特别关注 PE 较高的公司）");
  if (technicalData?.volatility20 != null && technicalData.volatility20 > 0.4) {
    riskSection.bullets.push("交易风险：当前波动率偏高，持仓需严格控制仓位与止损");
  }
  if (fundamentalsData?.debtToEquity != null && fundamentalsData.debtToEquity > 1) {
    riskSection.bullets.push("财务风险：资产负债率偏高，需关注再融资压力与利息负担");
  }
  if (catalystsReport?.catalystScore != null && catalystsReport.catalystScore < 30) {
    riskSection.bullets.push("情绪风险：市场情绪偏弱，短期可能有抛压");
  }
  riskSection.narrative = `以上为基于公开数据与通用框架的风险提示。投资者需结合自身风险承受能力，独立判断并做好仓位管理与止损纪律。`;

  // ============================================================
  // 9. 投资结论 (Investment Conclusion)
  // ============================================================
  const conclusionSection = {
    title: "投资结论 (Investment Conclusion)",
    bullets: [],
    narrative: "",
  };
  conclusionSection.bullets.push(`综合评级：${rating}（${verdict}）`);
  if (enhancedRecommendation?.score != null) conclusionSection.bullets.push(`综合得分：${enhancedRecommendation.score.toFixed(0)}/100`);
  if (entry != null) conclusionSection.bullets.push(`建议买入价：${entry.toFixed(2)}`);
  if (target != null) conclusionSection.bullets.push(`目标价：${target.toFixed(2)}（潜在上行 ${upside || "—"}）`);
  if (stopLoss != null) conclusionSection.bullets.push(`止损价：${stopLoss.toFixed(2)}（最大下行 ${downside || "—"}）`);
  if (enhancedRecommendation?.suggestedPositionSize) conclusionSection.bullets.push(`建议仓位：${enhancedRecommendation.suggestedPositionSize}`);
  if (enhancedRecommendation?.timeHorizon) conclusionSection.bullets.push(`持有期建议：${enhancedRecommendation.timeHorizon}`);
  conclusionSection.narrative = enhancedRecommendation?.reasoning || "综合 6 大维度信号给出以上决策建议。请严格遵守仓位纪律与止损条件。";

  // ============================================================
  // 最终组装
  // ============================================================
  return {
    reportMeta: {
      name, tsCode, market, sector,
      generatedAt: new Date().toISOString(),
      disclaimer: "本报告为系统自动生成的研究框架内容，仅供参考，不构成投资建议。投资有风险，决策需独立判断。",
    },
    investmentThesis: {
      title: "投资摘要 (Investment Thesis)",
      bullets: thesisBullets,
      narrative: `${name}（${tsCode}）的综合投资评级为 ${rating}。核心投资逻辑基于 6 大维度的加权评估：估值、基本面、技术面、护城河、同业对标与催化因素。`,
    },
    executiveSummary: {
      title: "执行摘要 (Executive Summary)",
      bullets: execSummary,
      narrative: execSummary.length
        ? `以上为 ${name} 最关键的 5-8 条判断要点，是研究员在 30 秒内必须传达的核心信息。`
        : "暂无足够的量化数据生成执行摘要。",
    },
    valuation: valuationSection,
    fundamental: fundamentalSection,
    moat: moatSection,
    technical: technicalSection,
    catalysts: catalystsSection,
    risks: riskSection,
    conclusion: conclusionSection,
  };
}

