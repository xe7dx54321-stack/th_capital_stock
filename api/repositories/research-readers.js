/** Database readers retained from the classic research API. */

export function getValuationData(db, code, factorMap) {
  let snap = null;
  try {
    snap = db.prepare(
      `SELECT ticker, pe_ttm, ps_ttm, pb, ev_ebitda_ttm,
              historical_percentile, peer_percentile, broker_target_price,
              current_price, valuation_status, valuation_confidence, generated_at
       FROM valuation_snapshot WHERE ticker=? ORDER BY generated_at DESC LIMIT 1`
    ).get(code);
  } catch (err) {
    // 表不存在或列名变化时优雅降级：仅依赖 factorMap
    snap = null;
  }

  const pe = snap?.pe_ttm != null && !isNaN(snap.pe_ttm) ? Number(snap.pe_ttm)
           : (factorMap["pe_ttm"] != null ? Number(factorMap["pe_ttm"]) : null);
  const pb = snap?.pb != null && !isNaN(snap.pb) ? Number(snap.pb)
           : (factorMap["pb"] != null ? Number(factorMap["pb"]) : null);
  const ps = snap?.ps_ttm != null && !isNaN(snap.ps_ttm) ? Number(snap.ps_ttm) : null;
  const evEbitda = snap?.ev_ebitda_ttm != null && !isNaN(snap.ev_ebitda_ttm) ? Number(snap.ev_ebitda_ttm) : null;
  const historicalPercentile = snap?.historical_percentile != null && !isNaN(snap.historical_percentile) ? Number(snap.historical_percentile) : null;
  const peerPercentile = snap?.peer_percentile != null && !isNaN(snap.peer_percentile) ? Number(snap.peer_percentile) : null;
  const brokerTargetPrice = snap?.broker_target_price != null && !isNaN(snap.broker_target_price) ? Number(snap.broker_target_price) : null;
  const currentPrice = snap?.current_price != null && !isNaN(snap.current_price) ? Number(snap.current_price) : null;
  const status = snap?.valuation_status || "insufficient_data";
  const confidence = snap?.valuation_confidence != null ? Number(snap.valuation_confidence) : 0.5;
  const generatedAt = snap?.generated_at || null;

  const filled = [pe, pb, ps, evEbitda, historicalPercentile, brokerTargetPrice, currentPrice].filter(v => v != null).length;
  const dataQuality = Math.round((filled / 7) * 100);

  return {
    pe, pb, ps, evEbitda,
    historicalPercentile, peerPercentile,
    brokerTargetPrice, currentPrice,
    status, confidence, generatedAt,
    dataQuality,
  };
}

export function getFundamentalsData(db, code, factorMap) {
  let snap = null;
  try {
    snap = db.prepare(
      `SELECT ticker, market, revenue, gross_profit, operating_income, net_income,
              operating_cash_flow, free_cash_flow, total_debt, shareholders_equity,
              gross_margin, operating_margin, net_margin, roe, roic,
              source_quality, freshness_status, confidence, created_at
       FROM fundamentals_snapshot WHERE ticker=? ORDER BY created_at DESC LIMIT 1`
    ).get(code);
  } catch (err) {
    // 表不存在或列名变化时优雅降级
    snap = null;
  }

  const revenue = snap?.revenue != null && !isNaN(snap.revenue) ? Number(snap.revenue) : null;
  const grossProfit = snap?.gross_profit != null && !isNaN(snap.gross_profit) ? Number(snap.gross_profit) : null;
  const netIncome = snap?.net_income != null && !isNaN(snap.net_income) ? Number(snap.net_income) : null;
  const grossMargin = snap?.gross_margin != null && !isNaN(snap.gross_margin) ? Number(snap.gross_margin)
                  : (factorMap["gross_margin"] != null ? Number(factorMap["gross_margin"]) / 100 : null);
  const netMargin = snap?.net_margin != null && !isNaN(snap.net_margin) ? Number(snap.net_margin)
                : (factorMap["net_margin"] != null ? Number(factorMap["net_margin"]) / 100 : null);
  const roe = snap?.roe != null && !isNaN(snap.roe) ? Number(snap.roe)
          : (factorMap["roe_reported"] != null ? Number(factorMap["roe_reported"]) / 100 : null);
  const roic = snap?.roic != null && !isNaN(snap.roic) ? Number(snap.roic) : null;
  const operatingCashFlow = snap?.operating_cash_flow != null && !isNaN(snap.operating_cash_flow) ? Number(snap.operating_cash_flow) : null;
  const freeCashFlow = snap?.free_cash_flow != null && !isNaN(snap.free_cash_flow) ? Number(snap.free_cash_flow) : null;
  const totalDebt = snap?.total_debt != null && !isNaN(snap.total_debt) ? Number(snap.total_debt) : null;
  const equity = snap?.shareholders_equity != null && !isNaN(snap.shareholders_equity) ? Number(snap.shareholders_equity) : null;

  const revenueYoY = factorMap["revenue_yoy"] != null ? Number(factorMap["revenue_yoy"]) : null;
  const netProfitYoY = factorMap["net_profit_yoy"] != null ? Number(factorMap["net_profit_yoy"]) : null;

  let debtRatio = null;
  if (totalDebt != null && equity != null && (totalDebt + equity) > 0) {
    debtRatio = totalDebt / (totalDebt + equity);
  }

  const sourceQuality = snap?.source_quality || "n/a";
  const freshness = snap?.freshness_status || "n/a";

  // === FR-5 增强型基本面诊断 ===
  // 1. 盈利质量评分 (0-100)
  let earningsQuality = null;
  let earningsQualityDesc = "";
  {
    let score = 0, count = 0;
    if (grossMargin != null) { score += grossMargin > 0.3 ? 90 : (grossMargin > 0.15 ? 60 : 30); count++; }
    if (netMargin != null) { score += netMargin > 0.15 ? 90 : (netMargin > 0.05 ? 60 : 30); count++; }
    if (roe != null) { score += roe > 0.15 ? 90 : (roe > 0.08 ? 60 : 30); count++; }
    if (operatingCashFlow != null && netIncome != null && netIncome !== 0) {
      const cfRatio = operatingCashFlow / netIncome;
      score += cfRatio > 0.8 ? 90 : (cfRatio > 0.3 ? 60 : 30);
      count++;
    }
    if (count > 0) {
      earningsQuality = Math.round(score / count);
      if (earningsQuality >= 80) earningsQualityDesc = "盈利质量优秀，利润率稳定且现金流健康";
      else if (earningsQuality >= 60) earningsQualityDesc = "盈利质量良好";
      else if (earningsQuality >= 40) earningsQualityDesc = "盈利质量一般，需关注利润率变化";
      else earningsQualityDesc = "盈利质量较差，建议谨慎";
    }
  }

  // 2. 增长质量评分 (0-100)
  let growthQuality = null;
  let growthQualityDesc = "";
  {
    let score = 0, count = 0;
    if (revenueYoY != null) { score += revenueYoY > 20 ? 90 : (revenueYoY > 10 ? 60 : (revenueYoY >= 0 ? 30 : 10)); count++; }
    if (netProfitYoY != null) { score += netProfitYoY > 25 ? 90 : (netProfitYoY > 10 ? 60 : (netProfitYoY >= 0 ? 30 : 10)); count++; }
    if (count > 0) {
      growthQuality = Math.round(score / count);
      if (growthQuality >= 80) growthQualityDesc = "高速增长，营收和利润同步提升";
      else if (growthQuality >= 60) growthQualityDesc = "稳健增长";
      else if (growthQuality >= 40) growthQualityDesc = "增长放缓";
      else growthQualityDesc = "增长乏力或负增长";
    }
  }

  // 3. 财务健康评分 (0-100)
  let financialHealth = null;
  let financialHealthDesc = "";
  {
    let score = 0, count = 0;
    if (debtRatio != null) { score += debtRatio < 0.3 ? 90 : (debtRatio < 0.5 ? 60 : 30); count++; }
    if (operatingCashFlow != null) { score += operatingCashFlow > 0 ? 90 : 30; count++; }
    if (equity != null && equity > 0) { score += 70; count++; }
    if (freeCashFlow != null) { score += freeCashFlow > 0 ? 90 : 40; count++; }
    
    // 兜底：如果财务健康指标都缺失，但盈利和增长质量都很高，给出保守评分
    if (count === 0) {
      if (earningsQuality >= 80 && growthQuality >= 80) {
        financialHealth = 70;
        financialHealthDesc = "财务数据有限，但盈利和增长质量优秀，推测财务状况稳健";
      } else if (earningsQuality >= 60 || growthQuality >= 60) {
        financialHealth = 50;
        financialHealthDesc = "财务数据有限，基于盈利/增长质量推测财务状况一般";
      }
    } else {
      financialHealth = Math.round(score / count);
      if (financialHealth >= 80) financialHealthDesc = "财务状况健康，现金流充裕，负债合理";
      else if (financialHealth >= 60) financialHealthDesc = "财务状况稳健";
      else if (financialHealth >= 40) financialHealthDesc = "财务状况一般，建议关注偿债能力";
      else financialHealthDesc = "财务压力较大，需谨慎";
    }
  }

  const keyFields = [revenue, grossMargin, netMargin, roe, roic, operatingCashFlow, equity];
  const dataQuality = Math.round((keyFields.filter(v => v != null).length / keyFields.length) * 100);

  return {
    revenue, revenueYoY, grossProfit, netIncome, netProfitYoY,
    grossMargin, netMargin, roe, roic,
    operatingCashFlow, freeCashFlow, totalDebt, equity, debtRatio,
    sourceQuality, freshness,
    createdAt: snap?.created_at || null,
    dataQuality,
    // FR-5 增强型基本面诊断
    earningsQuality, earningsQualityDesc,
    growthQuality, growthQualityDesc,
    financialHealth, financialHealthDesc,
  };
}

export function getPeerGroupData(db, code, sector) {
  if (!sector) return { sector: null, peerCount: 0, peers: [], avg: {}, latest: {} };

  let poolRows = [];
  try {
    poolRows = db.prepare(
      `SELECT ts_code, sector, pool_type FROM stock_pool_current WHERE sector=? AND ts_code!=?`
    ).all(sector, code);
  } catch (err) {
    return { sector, peerCount: 0, peers: [], avg: {}, latest: {} };
  }
  if (!poolRows || poolRows.length === 0) {
    return { sector, peerCount: 0, peers: [], avg: {}, latest: {} };
  }

  const peers = [];
  for (const row of poolRows) {
    const peerCode = row.ts_code;
    let v = null;
    try {
      v = db.prepare(`SELECT pe_ttm, pb FROM valuation_snapshot WHERE ticker=? ORDER BY generated_at DESC LIMIT 1`).get(peerCode);
    } catch (err) { v = null; }
    let fRows = [];
    try {
      fRows = db.prepare(
        `SELECT factor_name, factor_value FROM factor_daily WHERE ts_code=? AND factor_name IN ('pe_ttm','pb','roe_reported','gross_margin','revenue_yoy','trend_strength')`
      ).all(peerCode);
    } catch (err) { fRows = []; }
    const fMap = {};
    for (const f of fRows) fMap[f.factor_name] = f.factor_value;
    const pe = v?.pe_ttm != null && !isNaN(v.pe_ttm) ? Number(v.pe_ttm) : (fMap["pe_ttm"] != null ? Number(fMap["pe_ttm"]) : null);
    const pb = v?.pb != null && !isNaN(v.pb) ? Number(v.pb) : (fMap["pb"] != null ? Number(fMap["pb"]) : null);
    // —— 单位说明：factor_daily 中 roe_reported/gross_margin 存的是百分比数字（如 37.18 代表 37.18%）
    //    而 fundamentalsData 中会除以100变成小数（0.3718）。这里做同样处理，保证单位一致。
    const roe = fMap["roe_reported"] != null ? Number(fMap["roe_reported"]) / 100 : null;
    const grossMargin = fMap["gross_margin"] != null ? Number(fMap["gross_margin"]) / 100 : null;
    const revenueYoY = fMap["revenue_yoy"] != null ? Number(fMap["revenue_yoy"]) : null;
    const trendStrength = fMap["trend_strength"] != null ? Number(fMap["trend_strength"]) : null;

    let latestClose = null;
    try {
      const priceRows = db.prepare(`SELECT close FROM daily_bar WHERE ts_code=? ORDER BY trade_date DESC LIMIT 1`).all(peerCode);
      latestClose = priceRows && priceRows[0] ? priceRows[0].close : null;
      if (latestClose == null && /^[A-Z]+$/.test(peerCode)) {
        const usRows = db.prepare(`SELECT close FROM us_daily_bar WHERE symbol=? ORDER BY trade_date DESC LIMIT 1`).all(peerCode);
        latestClose = usRows && usRows[0] ? usRows[0].close : null;
      }
    } catch (err) {}
    peers.push({
      tsCode: peerCode, name: getStockName(peerCode) || peerCode,
      pe, pb, roe, grossMargin, revenueYoY, trendStrength, latestClose,
    });
  }

  const avgField = (key) => {
    const valid = peers.filter(p => {
      if (p[key] == null || isNaN(p[key])) return false;
      // —— PE/PB 为负值不参与均值（代表亏损或资不抵债）
      if ((key === "pe" || key === "pb") && Number(p[key]) < 0) return false;
      return true;
    });
    if (valid.length === 0) return null;
    return valid.reduce((a, b) => a + Number(b[key]), 0) / valid.length;
  };
  const avg = {
    pe: avgField("pe"), pb: avgField("pb"),
    roe: avgField("roe"), grossMargin: avgField("grossMargin"),
    revenueYoY: avgField("revenueYoY"),
  };

  const closes = peers.map(p => p.latestClose).filter(v => v != null);
  const latestMedian = closes.length ? closes.sort((a, b) => a - b)[Math.floor(closes.length / 2)] : null;

  return {
    sector, peerCount: peers.length, peers, avg,
    latest: { medianClose: latestMedian, sampleSize: closes.length },
  };
}

export function getNewsClaimsAndRisks(db, code) {
  let newsRows = [];
  try {
    newsRows = db.prepare(
      `SELECT id, title, body, source_key, source_name, published_at, tickers_json, url, credibility
       FROM news_items WHERE tickers_json LIKE ? ORDER BY published_at DESC LIMIT 20`
    ).all(`%"${code}"%`);
  } catch (err) { newsRows = []; }
  const news = newsRows.map((r) => {
    let tickers = [];
    try { tickers = JSON.parse(r.tickers_json || "[]").filter((t) => t && typeof t === "string"); } catch {}
    const body = r.body || "";
    return {
      id: r.id, title: r.title,
      source: r.source_key, sourceName: r.source_name || r.source_key,
      publishedAt: r.published_at, tickers, url: r.url, credibility: r.credibility || "",
      summary: body.length > 180 ? body.substring(0, 180) + "…" : body,
      hasFullBody: body.length > 0,
    };
  });

  let claimRows = [];
  try {
    claimRows = db.prepare(
      `SELECT claim_id, claim_type, theme, claim_text, stance, importance, confidence, created_at
       FROM research_claims WHERE ticker=? ORDER BY created_at DESC LIMIT 20`
    ).all(code);
  } catch (err) { claimRows = []; }
  const claims = claimRows.map((r) => ({
    claimId: r.claim_id, claimType: r.claim_type, theme: r.theme || "",
    claimText: r.claim_text || "", stance: r.stance || "",
    importance: r.importance || "",
    confidence: r.confidence != null ? Number(r.confidence) : 0.5,
    createdAt: r.created_at,
  }));

  let riskRows = [];
  try {
    riskRows = db.prepare(
      `SELECT alert_id, alert_time, alert_type, severity, ts_code, message, action
       FROM risk_alert WHERE ts_code=? OR ts_code IS NULL ORDER BY severity DESC, alert_time DESC LIMIT 20`
    ).all(code);
  } catch (err) { riskRows = []; }
  const risks = riskRows.map((r) => ({
    alertId: r.alert_id, alertTime: r.alert_time, alertType: r.alert_type,
    severity: r.severity, tsCode: r.ts_code, message: r.message, action: r.action || "",
  }));

  return { news, claims, risks };
}

export function buildPeerAvgForSector(db, code, sector) {
  if (!sector) return { sector: null, peerCount: 0, avg: {} };
  let peers = [];
  try {
    peers = db.prepare(
      `SELECT ts_code FROM stock_pool_current WHERE sector=? AND ts_code!=?`
    ).all(sector, code);
  } catch (err) { peers = []; }
  if (peers.length === 0) return { sector, peerCount: 0, avg: {} };

  let revSum = 0, revCnt = 0;
  let gmSum = 0, gmCnt = 0;
  let roeSum = 0, roeCnt = 0;
  for (const p of peers) {
    const peerCode = p.ts_code;
    const fRows = db.prepare(
      `SELECT factor_name, factor_value FROM factor_daily WHERE ts_code=? AND factor_name IN ('gross_margin','roe_reported','revenue_yoy')`
    ).all(peerCode);
    const fMap = {};
    for (const r of fRows) fMap[r.factor_name] = r.factor_value;
    // 与 getFundamentalsData 保持一致的计算逻辑（0-1 scale）
    const gm = fMap["gross_margin"] != null ? Number(fMap["gross_margin"]) / 100 : null;
    const roe = fMap["roe_reported"] != null ? Number(fMap["roe_reported"]) / 100 : null;
    const rev = fMap["revenue_yoy"] != null ? Number(fMap["revenue_yoy"]) : null;
    if (gm != null && !isNaN(gm)) { gmSum += gm; gmCnt++; }
    if (roe != null && !isNaN(roe)) { roeSum += roe; roeCnt++; }
    if (rev != null && !isNaN(rev)) { revSum += rev; revCnt++; }
  }
  return {
    sector,
    peerCount: peers.length,
    avg: {
      revenueYoY: revCnt > 0 ? Number((revSum / revCnt).toFixed(2)) : null,
      grossMargin: gmCnt > 0 ? Number((gmSum / gmCnt).toFixed(4)) : null,
      roe: roeCnt > 0 ? Number((roeSum / roeCnt).toFixed(4)) : null,
    },
  };
}

