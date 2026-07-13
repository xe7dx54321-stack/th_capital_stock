export function getMoatReport(fundamentalsData, peerGroupData) {
  const f = fundamentalsData || {};
  const peerAvg = (peerGroupData && peerGroupData.avg) || {};

  const dimensions = [];
  const evidence = [];

  // --- 1. 品牌溢价（基于毛利率 vs 同行，权重 0.20） ---
  {
    let score = null;
    const ev = [];
    const gm = f.grossMargin != null && !isNaN(f.grossMargin) ? Number(f.grossMargin) : null;
    const peerGm = peerAvg.grossMargin != null && !isNaN(peerAvg.grossMargin) ? Number(peerAvg.grossMargin) : null;

    if (gm != null) {
      if (gm > 0.40) { score = 9; ev.push(`毛利率 ${(gm * 100).toFixed(1)}% 已超过 40%，显示出较强的品牌定价力。`); }
      else if (gm > 0.25) { score = 7; ev.push(`毛利率 ${(gm * 100).toFixed(1)}%，处于行业中上游水平。`); }
      else if (gm > 0.10) { score = 5; ev.push(`毛利率 ${(gm * 100).toFixed(1)}%，行业水平。`); }
      else { score = 3; ev.push(`毛利率 ${(gm * 100).toFixed(1)}%，相对偏低。`); }

      if (peerGm != null) {
        const diff = gm - peerGm;
        if (diff > 0.05) { score = Math.min(10, score + 1); ev.push(`相对于同行均值 ${(peerGm * 100).toFixed(1)}% 有显著溢价。`); }
        else if (diff < -0.05) { score = Math.max(0, score - 1); ev.push(`相对于同行均值 ${(peerGm * 100).toFixed(1)}% 存在差距。`); }
      }
    } else {
      ev.push("暂无可靠的毛利率数据，品牌溢价维度暂不评分。");
    }
    dimensions.push({ name: "品牌溢价", score, weight: 0.20, evidence: ev });
    if (score != null) evidence.push(...ev);
  }

  // --- 2. 成本优势（基于净利润率 + ROE vs 同行，权重 0.20） ---
  {
    let score = null;
    const ev = [];
    const nm = f.netMargin != null && !isNaN(f.netMargin) ? Number(f.netMargin) : null;
    const roe = f.roe != null && !isNaN(f.roe) ? Number(f.roe) : null;

    let sub = 0, count = 0;
    if (nm != null) {
      if (nm > 0.20) { sub += 9; ev.push(`净利润率 ${(nm * 100).toFixed(1)}%，非常出色。`); }
      else if (nm > 0.10) { sub += 7; ev.push(`净利润率 ${(nm * 100).toFixed(1)}%，较好。`); }
      else if (nm > 0.05) { sub += 5; }
      else { sub += 3; }
      count++;
    }
    if (roe != null) {
      if (roe > 0.20) { sub += 9; ev.push(`ROE ${(roe * 100).toFixed(1)}%，股东回报极强。`); }
      else if (roe > 0.15) { sub += 7; }
      else if (roe > 0.08) { sub += 5; }
      else { sub += 3; }
      count++;
    }
    if (count > 0) score = Math.round(sub / count * 10) / 10;
    else ev.push("暂无净利润率/ROE 数据，成本优势维度暂不评分。");

    dimensions.push({ name: "成本优势", score, weight: 0.20, evidence: ev });
    if (score != null) evidence.push(...ev);
  }

  // --- 3. 网络效应（基于营收规模与增速 vs 同行，权重 0.10） ---
  {
    let score = null;
    const ev = [];
    const rev = f.revenue != null && !isNaN(f.revenue) ? Number(f.revenue) : null;
    const revYoY = f.revenueYoY != null && !isNaN(f.revenueYoY) ? Number(f.revenueYoY) : null;
    // 同行收入均值用 peerAvg 里估算的值（目前只有 grossMargin 的数据，我们使用 revenueYoY 作为对比）
    const peerRevYoY = peerAvg.revenueYoY != null ? Number(peerAvg.revenueYoY) : null;

    let sub = 0, count = 0;
    if (rev != null) {
      // 如果收入在绝对规模上 > 100 亿（单位假设是元），认为有规模效应
      if (rev > 1e10) { sub += 8; ev.push(`营收规模 ${(rev / 1e8).toFixed(0)} 亿元，具备一定体量。`); }
      else if (rev > 1e9) { sub += 6; }
      else { sub += 4; }
      count++;
    }
    if (revYoY != null) {
      if (revYoY > 20) { sub += 9; ev.push(`营收同比增长 ${revYoY.toFixed(1)}%，高速成长。`); }
      else if (revYoY > 10) { sub += 7; }
      else if (revYoY > 0) { sub += 5; }
      else { sub += 2; }
      count++;
      if (peerRevYoY != null) {
        if (revYoY - peerRevYoY > 10) { sub = Math.min(10, sub + 1); ev.push(`显著高于同行营收增速均值。`); }
      }
    }
    if (count > 0) score = Math.round(sub / count * 10) / 10;
    else ev.push("暂无营收数据，网络效应维度暂不评分。");

    dimensions.push({ name: "网络效应", score, weight: 0.10, evidence: ev });
    if (score != null) evidence.push(...ev);
  }

  // --- 4. 转换成本（基于 ROE 持续水平，权重 0.15） ---
  {
    let score = null;
    const ev = [];
    const roe = f.roe != null && !isNaN(f.roe) ? Number(f.roe) : null;
    const fcf = f.freeCashFlow != null && !isNaN(f.freeCashFlow) ? Number(f.freeCashFlow) : null;
    const rev = f.revenue != null && !isNaN(f.revenue) ? Number(f.revenue) : null;

    let sub = 0, count = 0;
    if (roe != null) {
      if (roe > 0.20) { sub += 9; ev.push(`ROE 持续高于 20%，隐含较强客户粘性/转换成本。`); }
      else if (roe > 0.15) { sub += 7; }
      else if (roe > 0.08) { sub += 5; }
      else { sub += 3; }
      count++;
    }
    if (fcf != null && rev != null && rev > 0) {
      const fcfRatio = fcf / rev;
      if (fcfRatio > 0.15) { sub += 8; ev.push(`FCF/营收 ${(fcfRatio * 100).toFixed(1)}%，自由现金奶牛。`); }
      else if (fcfRatio > 0.05) { sub += 6; }
      else { sub += 4; }
      count++;
    }
    if (count > 0) score = Math.round(sub / count * 10) / 10;
    else ev.push("暂无 ROE/自由现金流数据，转换成本维度暂不评分。");

    dimensions.push({ name: "转换成本", score, weight: 0.15, evidence: ev });
    if (score != null) evidence.push(...ev);
  }

  // --- 5. 规模经济（基于营收 vs 同行均值，权重 0.15） ---
  {
    let score = null;
    const ev = [];
    const rev = f.revenue != null && !isNaN(f.revenue) ? Number(f.revenue) : null;
    const ops = f.operatingCashFlow != null && !isNaN(f.operatingCashFlow) ? Number(f.operatingCashFlow) : null;

    let sub = 0, count = 0;
    if (rev != null) {
      // 绝对规模评估
      if (rev > 1e11) { sub += 10; ev.push(`营收超千亿，绝对规模领先。`); }
      else if (rev > 1e10) { sub += 8; ev.push(`营收超百亿，具备规模效应。`); }
      else if (rev > 1e9) { sub += 6; }
      else { sub += 4; }
      count++;
    }
    if (ops != null) {
      if (ops > 0) { sub += 7; ev.push(`经营现金流为正，运营健康。`); }
      else { sub += 3; ev.push(`经营现金流为负，运营压力较大。`); }
      count++;
    }
    if (count > 0) score = Math.round(sub / count * 10) / 10;
    else ev.push("暂无营收数据，规模经济维度暂不评分。");

    dimensions.push({ name: "规模经济", score, weight: 0.15, evidence: ev });
    if (score != null) evidence.push(...ev);
  }

  // --- 6. 无形资产（基于综合盈利质量 + FCF，权重 0.20） ---
  {
    let score = null;
    const ev = [];
    const nm = f.netMargin != null && !isNaN(f.netMargin) ? Number(f.netMargin) : null;
    const roe = f.roe != null && !isNaN(f.roe) ? Number(f.roe) : null;
    const fcf = f.freeCashFlow != null && !isNaN(f.freeCashFlow) ? Number(f.freeCashFlow) : null;
    const rev = f.revenue != null && !isNaN(f.revenue) ? Number(f.revenue) : null;

    let sub = 0, count = 0;
    if (nm != null) {
      if (nm > 0.25) { sub += 9; ev.push(`高净利润率，产品/服务具有溢价能力。`); }
      else if (nm > 0.15) { sub += 7; }
      else if (nm > 0.05) { sub += 5; }
      else { sub += 3; }
      count++;
    }
    if (roe != null) {
      if (roe > 0.20) { sub += 9; }
      else if (roe > 0.12) { sub += 7; }
      else if (roe > 0.05) { sub += 5; }
      else { sub += 3; }
      count++;
    }
    if (fcf != null && rev != null && rev > 0) {
      const fcfRatio = fcf / rev;
      if (fcfRatio > 0.15) { sub += 9; ev.push(`高自由现金流转化率，体现无形资产变现能力。`); }
      else if (fcfRatio > 0.05) { sub += 6; }
      else { sub += 4; }
      count++;
    }
    if (count > 0) score = Math.round(sub / count * 10) / 10;
    else ev.push("暂无盈利质量数据，无形资产维度暂不评分。");

    dimensions.push({ name: "无形资产", score, weight: 0.20, evidence: ev });
    if (score != null) evidence.push(...ev);
  }

  // --- 计算综合评分 ---
  const scoredDims = dimensions.filter((d) => d.score != null);
  let moatScore = null;
  let moatStrength = "无";
  let moatTrend = "稳定";
  let summary = "暂无可靠的护城河数据。建议查看季度报告补充最新财务数据后重试。";

  if (scoredDims.length >= 3) {
    // 按可用维度的权重重新归一
    const totalWeight = scoredDims.reduce((a, b) => a + b.weight, 0);
    if (totalWeight > 0) {
      const weighted = scoredDims.reduce((a, b) => a + (b.score * b.weight), 0);
      const avg = weighted / totalWeight;
      moatScore = Math.round(avg * 100 / 10); // 0-100 分制
      
      // 确定护城河强度
      if (moatScore >= 80) {
        moatStrength = "强";
        summary = `综合护城河评分 ${moatScore}/100，具备深厚的竞争壁垒，值得长期关注。`;
      } else if (moatScore >= 60) {
        moatStrength = "中";
        summary = `综合护城河评分 ${moatScore}/100，具备一定的竞争优势。`;
      } else if (moatScore >= 40) {
        moatStrength = "弱";
        summary = `综合护城河评分 ${moatScore}/100，竞争优势不明显。`;
      } else {
        moatStrength = "无";
        summary = `综合护城河评分 ${moatScore}/100，竞争壁垒较薄弱，需谨慎。`;
      }
    }
  }

  return {
    moatScore,
    moatStrength,
    moatTrend,
    dimensions: dimensions.map((d) => ({
      name: d.name,
      score: d.score,
      weight: d.weight,
      evidence: d.evidence,
    })),
    summary,
    evidenceChain: evidence.slice(0, 8),
  };
}

export function getPeerComparisonReport(valuationData, fundamentalsData, technicalData, peerGroupData) {
  const sector = peerGroupData?.sector || "";
  const peerCount = peerGroupData?.peerCount || 0;
  const peers = peerGroupData?.peers || [];
  const peerAvg = peerGroupData?.avg || {};

  // --- 目标公司的指标值 ---
  const target = {
    pe: valuationData?.pe != null ? Number(valuationData.pe) : null,
    pb: valuationData?.pb != null ? Number(valuationData.pb) : null,
    roe: fundamentalsData?.roe != null ? Number(fundamentalsData.roe) : null,
    grossMargin: fundamentalsData?.grossMargin != null ? Number(fundamentalsData.grossMargin) : null,
    revenueYoY: fundamentalsData?.revenueYoY != null ? Number(fundamentalsData.revenueYoY) : null,
    // trendStrength 通常是 0-10 分制；而同行 peers 的也同样是
    trendStrength: technicalData?.trendStrength != null ? Number(technicalData.trendStrength) : null,
  };

  // --- 所有同行 + 目标 的值列表（含目标自身以便做"在行业中的位置"排名） ---
  const allForRanking = peers.slice(); // 复制

  // 指标定义（higherBetter 表示该指标越大越好）
  const metricDefs = [
    { key: "pe", name: "市盈率 (PE)", higherBetter: false, unit: "x" },
    { key: "pb", name: "市净率 (PB)", higherBetter: false, unit: "x" },
    { key: "roe", name: "净资产收益率 (ROE)", higherBetter: true, unit: "%" },
    { key: "grossMargin", name: "毛利率", higherBetter: true, unit: "%" },
    { key: "revenueYoY", name: "营收同比", higherBetter: true, unit: "%" },
    { key: "trendStrength", name: "技术趋势强度", higherBetter: true, unit: "分" },
  ];

  const metrics = [];

  for (const def of metricDefs) {
    const val = target[def.key];
    // 收集同行的该指标有效数据
    const peerVals = [];
    for (const p of peers) {
      const v = p[def.key];
      // —— 关键修复：PE 为负值表示公司亏损，不代表"便宜"，必须排除
      // —— PB 为负值通常表示净资产为负，同样无意义
      if (v != null && !isNaN(v)) {
        if ((def.key === "pe" || def.key === "pb") && Number(v) < 0) continue;
        peerVals.push(Number(v));
      }
    }
    // 加上自己，得到完整样本（但自己是负数PE/PB也不加入）
    let full = peerVals.slice();
    let effectiveVal = val;
    if (val != null && !isNaN(val)) {
      if ((def.key === "pe" || def.key === "pb") && Number(val) < 0) {
        effectiveVal = null; // 目标公司是亏损状态，不参与"便宜与否"排名
      } else {
        full = [...peerVals, Number(val)];
      }
    }
    const total = full.length;
    let rank = null, percentile = null, interpretation = "暂无足够同行数据";

    if (effectiveVal != null && total > 1) {
      // 计算"比目标公司差的公司数量"
      let worseCount;
      if (def.higherBetter) {
        // 对 ROE/毛利率等，比目标低的 = 比目标差
        worseCount = full.filter((v) => v < effectiveVal).length;
      } else {
        // 对 PE/PB 等，比目标高的 = 比目标差（因为越低越便宜）
        worseCount = full.filter((v) => v > effectiveVal).length;
      }
      percentile = Math.round((worseCount / total) * 100);
      // 排名（从 1 开始）
      const sorted = [...full].sort((a, b) => def.higherBetter ? b - a : a - b);
      rank = sorted.indexOf(effectiveVal) + 1;

      // 文本解释
      if (percentile >= 80) interpretation = `行业前 20%，${def.higherBetter ? "显著领先" : "估值极具吸引力"}`;
      else if (percentile >= 60) interpretation = `行业中上游，${def.higherBetter ? "表现良好" : "估值合理偏低"}`;
      else if (percentile >= 40) interpretation = `行业中游，表现中规`;
      else if (percentile >= 20) interpretation = `行业中下游，${def.higherBetter ? "弱于多数同行" : "估值偏高"}`;
      else interpretation = `行业后 20%，${def.higherBetter ? "显著弱于同行" : "估值较贵"}`;
    } else if ((def.key === "pe" || def.key === "pb") && val != null && Number(val) < 0) {
      // 目标公司是亏损状态，特殊标注
      interpretation = `当前${def.key === "pe" ? "市盈率为负" : "市净率为负"}（亏损或资不抵债），估值分析不适用`;
    }

    // 展示值的格式化
    let displayVal = val;
    if (displayVal != null && (def.key === "roe" || def.key === "grossMargin")) displayVal = Number((val * 100).toFixed(2));
    else if (displayVal != null) displayVal = Number(val.toFixed(2));

    let displayAvg = peerAvg[def.key];
    if (displayAvg != null && (def.key === "roe" || def.key === "grossMargin")) displayAvg = Number((peerAvg[def.key] * 100).toFixed(2));
    else if (displayAvg != null) displayAvg = Number(displayAvg.toFixed(2));

    metrics.push({
      name: def.name,
      value: displayVal,
      peerAvg: displayAvg,
      percentile,
      rank,
      total,
      interpretation,
    });
  }

  // --- 综合行业地位（根据有数据的指标的百分位求均值） ---
  const validPct = metrics.map((m) => m.percentile).filter((p) => p != null);
  let industryPosition = "暂无足够同行数据进行对标分析";
  if (validPct.length >= 3) {
    const avg = validPct.reduce((a, b) => a + b, 0) / validPct.length;
    if (avg >= 75) industryPosition = `综合百分位 ${avg.toFixed(0)}，处于行业领先地位。`;
    else if (avg >= 55) industryPosition = `综合百分位 ${avg.toFixed(0)}，处于行业中上游。`;
    else if (avg >= 40) industryPosition = `综合百分位 ${avg.toFixed(0)}，处于行业中游。`;
    else industryPosition = `综合百分位 ${avg.toFixed(0)}，处于行业下游。`;
  }

  // --- 返回：整理 avg 的格式，便于前端展示 ---
  const formattedAvg = {};
  for (const def of metricDefs) {
    const raw = peerAvg[def.key];
    if (raw == null || isNaN(raw)) { formattedAvg[def.key] = null; continue; }
    if (def.key === "roe" || def.key === "grossMargin") formattedAvg[def.key] = Number((raw * 100).toFixed(2));
    else formattedAvg[def.key] = Number(Number(raw).toFixed(2));
  }

  return {
    sector,
    peerCount,
    metrics,
    industryPosition,
    avg: formattedAvg,
  };
}

