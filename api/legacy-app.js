/**
 * 后端 API 服务器
 * 读取 SQLite 数据库，提供 JSON API，为前端提供静态文件服务
 */

import express from "express";
import cors from "cors";
import Database from "better-sqlite3";
import path from "path";
import { fileURLToPath } from "url";
import { readdirSync, readFileSync, existsSync } from "fs";
import { loadAllPhaseConfigs, getSchedulerPhaseRuns } from "../08_scripts/lib/phase_status_loader.js";
import { ResearchRepository } from "./repositories/research-repository.js";
import { getStockName } from "./registries/stock-registry.js";
import { createResearchRouter } from "./routes/research.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DB_PATH = process.env.SMR_DB_PATH
  ? path.resolve(process.env.SMR_DB_PATH)
  : path.resolve(__dirname, "..", "01_data", "db", "smr.db");

const app = express();
const PORT = process.env.PORT ? parseInt(process.env.PORT) : 3000;

app.use(cors());
app.use(express.json());

const researchRepository = new ResearchRepository(DB_PATH);
app.use(createResearchRouter({ repository: researchRepository }));


// ============================================================
// 数据库连接
// ============================================================
function getDb() {
  return new Database(DB_PATH, { readonly: true });
}

// ============================================================
// 缓存
// ============================================================
const cache = new Map();
const CACHE_TTL = 5 * 60 * 1000;

function cached(key, fn) {
  const now = Date.now();
  const cached_item = cache.get(key);
  if (cached_item && now - cached_item.timestamp < CACHE_TTL) {
    return cached_item.data;
  }
  const data = fn();
  cache.set(key, { data, timestamp: now });
  return data;
}

// ============================================================
// API: GET /api/health
// ============================================================
app.get("/api/health", (_req, res) => {
  res.json({ status: "ok", timestamp: new Date().toISOString() });
});

// ============================================================
// API: GET /api/dashboard
// ============================================================

// ============================================================
// 辅助函数：从数据库读取增强数据
// ============================================================

/**
 * 读取某只股票最近 N 天的价格数据（用于计算动量）
 */
function loadPriceData(db, tsCode, days = 60) {
  const isUs = /^[A-Z]+$/.test(tsCode);
  let rows;
  if (isUs) {
    rows = db.prepare(
      `SELECT trade_date, close, pct_chg FROM us_daily_bar
       WHERE symbol=? ORDER BY trade_date ASC LIMIT ?`
    ).all(tsCode, days);
  } else {
    rows = db.prepare(
      `SELECT trade_date, close, pct_chg FROM daily_bar
       WHERE ts_code=? ORDER BY trade_date ASC LIMIT ?`
    ).all(tsCode, days);
  }
  return rows.map((r) => ({
    date: r.trade_date,
    close: r.close,
    pct_chg: r.pct_chg,
  }));
}

/**
 * 计算简单移动平均
 */
function calcSMA(closes, period) {
  if (closes.length < period) return null;
  const slice = closes.slice(-period);
  return slice.reduce((a, b) => a + b, 0) / period;
}

/**
 * 计算 EMA
 */
function calcEMA(closes, period) {
  if (closes.length < period) return null;
  const k = 2.0 / (period + 1);
  let ema = closes.slice(0, period).reduce((a, b) => a + b, 0) / period;
  for (let i = period; i < closes.length; i++) {
    ema = closes[i] * k + ema * (1 - k);
  }
  return ema;
}

/**
 * 计算价格动量指标（5日/20日收益、MACD信号）
 */
function computeMomentumIndicators(tsCode, db) {
  const prices = loadPriceData(db, tsCode, 90);
  if (prices.length < 5) {
    return { momentum5d: null, momentum20d: null, macdSignal: null, volumeRatio: null };
  }
  const closes = prices.map((p) => p.close).filter((c) => c != null);
  if (closes.length < 5) return { momentum5d: null, momentum20d: null, macdSignal: null, volumeRatio: null };

  const ret = (n) => {
    if (closes.length <= n) return null;
    const cur = closes[closes.length - 1];
    const old = closes[closes.length - n - 1];
    if (!cur || !old || old === 0) return null;
    return ((cur - old) / old) * 100;
  };

  const momentum5d = ret(5);
  const momentum20d = ret(20);

  // MACD：DIF = EMA12 - EMA26，DEA = EMA9(DIF)
  let macdSignal = null;
  if (closes.length >= 30) {
    const ema12 = calcEMA(closes, 12);
    const ema26 = calcEMA(closes, 26);
    const dif = ema12 !== null && ema26 !== null ? ema12 - ema26 : null;
    if (dif !== null && closes.length >= 35) {
      // 构建 DIF 历史用于计算 DEA
      const difHistory = [];
      for (let i = 26; i < closes.length; i++) {
        const e12 = calcEMA(closes.slice(0, i + 1), 12);
        const e26 = calcEMA(closes.slice(0, i + 1), 26);
        if (e12 !== null && e26 !== null) difHistory.push(e12 - e26);
      }
      const dea = calcEMA(difHistory, 9);
      if (dea !== null) {
        const macdHist = dif - dea;
        const prevHist = difHistory.length >= 2 ? difHistory[difHistory.length - 2] : null;
        const prevDea = calcEMA(difHistory.slice(0, -1), 9);
        if (prevHist !== null && prevDea !== null) {
          if (prevHist <= prevDea && dif > dea) macdSignal = "gold_cross";
          else if (prevHist >= prevDea && dif < dea) macdSignal = "death_cross";
          else if (dif > dea) macdSignal = "bullish";
          else macdSignal = "bearish";
        }
      }
    }
  }

  return { momentum5d, momentum20d, macdSignal, volumeRatio: null };
}

/**
 * 简单判断 PE/PB 历史分位（通过波动率估算）
 */
function computeSimplePercentile(tsCode, db) {
  // 从 factor_daily 取 PE 历史
  const peRows = db.prepare(
    `SELECT factor_value FROM factor_daily
     WHERE ts_code=? AND factor_name='pe_ttm' AND factor_value IS NOT NULL AND factor_value > 0
     ORDER BY trade_date DESC LIMIT 100`
  ).all(tsCode);
  if (!peRows || peRows.length < 10) return { pePercentile: null, pbPercentile: null };
  const peVals = peRows.map((r) => r.factor_value);
  const currentPE = peVals[0];
  const countBelow = peVals.filter((v) => v < currentPE).length;
  const pePercentile = Math.round((countBelow / peVals.length) * 1000) / 1000;

  return { pePercentile, pbPercentile: null };
}

// ============================================================
// API: GET /api/value-scores
// ============================================================
/**
 * 统一评分引擎（与 /api/stock/:code 详情页使用完全相同的评分公式
 *
 * 输入：与详情页同款的 valuationData / fundamentalsData / technicalData + latestPrice
 * 输出：6 维评分（0-100）+ 综合分 + verdict
 */
function computeUnifiedScore(valuationData, fundamentalsData, technicalData, moatReport) {
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

app.get("/api/value-scores", (_req, res) => {
  try {
    const data = cached("value_scores", () => {
      const db = getDb();

      // 1. 用 SQL 窗口函数去重：同一 ts_code 在多个池中只保留优先级最高的
      const poolRows = db.prepare(`
        SELECT ts_code, sector, pool_type
        FROM (
          SELECT ts_code, sector, pool_type,
            ROW_NUMBER() OVER (
              PARTITION BY ts_code
              ORDER BY CASE pool_type
                WHEN 'portfolio_seed' THEN 1
                WHEN 'seed' THEN 2
                WHEN 'watchlist' THEN 3
                WHEN 'candidate' THEN 4
                WHEN 'recommended' THEN 5
                WHEN 'us_benchmark' THEN 6
                ELSE 9
              END
            ) as rn
          FROM stock_pool_current
        ) sub
        WHERE rn = 1
      `).all();

      // 2. 预读取所有股票的因子数据（不使用白名单过滤，确保与详情页数据一致）
      // 之前使用 WHERE factor_name IN (...) 白名单导致遗漏 net_margin/pb/pe_dynamic/roic 等关键因子
      const factorRows = db.prepare(
        `SELECT ts_code, factor_name, factor_value FROM factor_daily`
      ).all();
      const factorsMap = new Map();
      for (const row of factorRows) {
        if (!factorsMap.has(row.ts_code)) factorsMap.set(row.ts_code, {});
        factorsMap.get(row.ts_code)[row.factor_name] = row.factor_value;
      }

      // 3. 预读取最新价
      const pricesMap = new Map();
      const ahPrices = db.prepare(
        `SELECT ts_code, close FROM daily_bar
         WHERE (ts_code, trade_date) IN (SELECT ts_code, MAX(trade_date) FROM daily_bar GROUP BY ts_code)`
      ).all();
      for (const row of ahPrices) pricesMap.set(row.ts_code, row.close);
      const usPrices = db.prepare(
        `SELECT symbol, close FROM us_daily_bar
         WHERE (symbol, trade_date) IN (SELECT symbol, MAX(trade_date) FROM us_daily_bar GROUP BY symbol)`
      ).all();
      for (const row of usPrices) pricesMap.set(row.symbol, row.close);

      // === 4b. 预读取价格历史（技术面 change5d/20d 计算使用，与详情页格式一致）
      // 重要：必须存为 {close: number} 对象数组，因为 getTechnicalData 使用 .close 访问
      const priceHistMap = new Map();
      const allBars = db.prepare(
        `SELECT ts_code, trade_date, close FROM daily_bar ORDER BY ts_code, trade_date ASC`
      ).all();
      for (const r of allBars) {
        if (!priceHistMap.has(r.ts_code)) priceHistMap.set(r.ts_code, []);
        priceHistMap.get(r.ts_code).push({ close: r.close, date: r.trade_date });
      }
      const allUSBars = db.prepare(
        `SELECT symbol as ts_code, trade_date, close FROM us_daily_bar ORDER BY symbol, trade_date ASC`
      ).all();
      for (const r of allUSBars) {
        if (!priceHistMap.has(r.ts_code)) priceHistMap.set(r.ts_code, []);
        priceHistMap.get(r.ts_code).push({ close: r.close, date: r.trade_date });
      }

      // === 4c. 预计算每只股票的同行均值（调用详情页同款 buildPeerAvgForSector ===
      // 确保列表页与详情页使用同一套 peer 均值数据
      const peerMap = new Map();
      for (const { ts_code, sector } of poolRows) {
        peerMap.set(ts_code, buildPeerAvgForSector(db, ts_code, sector));
      }

      // === 5. 对每只股票用详情页同款引擎计算评分 ===
      const scores = [];
      for (const { ts_code, sector } of poolRows) {
        const factorMap = factorsMap.get(ts_code) || {};
        const priceHistory = priceHistMap.get(ts_code) || [];
        let market = "其他";
        if (ts_code.endsWith(".SH") || ts_code.endsWith(".SZ")) market = "A";
        else if (ts_code.endsWith(".HK")) market = "H";
        else if (/^[A-Z]/.test(ts_code)) market = "US";
        const latestPrice = pricesMap.has(ts_code) ? Number(pricesMap.get(ts_code)) : null;

        // 调用与详情页同款的数据提取函数
        const valuationData = getValuationData(db, ts_code, factorMap);
        const fundamentalsData = getFundamentalsData(db, ts_code, factorMap);
        const technicalData = getTechnicalData(db, ts_code, factorMap, priceHistory);

        // 调用完整护城河引擎（与详情页同款：传入同行业均值）
        const peerGroupData = peerMap.get(ts_code);
        const moatReport = getMoatReport(fundamentalsData, peerGroupData);

        // 调用统一评分引擎（与详情页同一公式）
        const unified = computeUnifiedScore(valuationData, fundamentalsData, technicalData, moatReport);
        console.log(`[DEBUG-SCORE-LIST] ${ts_code} composite=${unified?.compositeScore} verdict=${unified?.verdict} val=${unified?.valScore} fund=${unified?.fundScore} tech=${unified?.techScore} moat=${unified?.moatScore}`);

        // 辅助：5日/20日涨跌幅（用于前端展示，与详情页同款格式）
        const closes = priceHistory.slice(-30).filter(c => c?.close != null);
        let change5d = null, change20d = null;
        if (closes.length >= 6) {
          const latest = closes[closes.length - 1].close;
          const p5 = closes[Math.max(0, closes.length - 5)].close;
          if (latest && p5 && p5 > 0) change5d = (latest / p5 - 1) * 100;
        }
        if (closes.length >= 21) {
          const latest = closes[closes.length - 1].close;
          const p20 = closes[Math.max(0, closes.length - 20)].close;
          if (latest && p20 && p20 > 0) change20d = (latest / p20 - 1) * 100;
        }

        const name = getStockName(ts_code) || ts_code;
        const cs10 = unified.compositeScore != null ? Math.round(unified.compositeScore / 10 * 10) / 10 : null;

        scores.push({
          tsCode: ts_code,
          name,
          market,
          compositeScore: cs10,
          fundamentalQuality: unified.fundScore != null ? Math.round(unified.fundScore / 10 * 10) / 10 : null,
          valuationPosition: unified.valScore != null ? Math.round(unified.valScore / 10 * 10) / 10 : null,
          technicalMomentum: unified.techScore != null ? Math.round(unified.techScore / 10 * 10) / 10 : null,
          themeRelevance: unified.moatScore != null ? Math.round(unified.moatScore / 10 * 10) / 10 : null,
          industryPosition: unified.moatScore != null ? Math.round(unified.moatScore / 10 * 10) / 10 : null,
          sector: sector || "未分类",
          latestClose: latestPrice != null ? Number(latestPrice.toFixed(2)) : null,
          verdict: unified.verdict,
          pePercentile: valuationData?.historicalPercentile,
          momentum5d: change5d != null ? Math.round(change5d * 10) / 10 : null,
          momentum20d: change20d != null ? Math.round(change20d * 10) / 10 : null,
          macdSignal: technicalData?.macdHist != null ? (technicalData.macdHist > 0 ? "bullish" : "bearish") : null,
        });
      }
      db.close();
      scores.sort((a, b) => (b.compositeScore || 0) - (a.compositeScore || 0));
      return { scores, updatedAt: new Date().toISOString() };
    });
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ============================================================
// 统一数据提取层（Task 1）
//
// 所有分析引擎（估值/基本面/技术面/护城河/同业/催化）
// 都只依赖下面 5 个函数的返回对象，不再直接操作数据库表。
// ============================================================

/**
 * 提取估值相关数据（Task 1-a）
 * 优先走 valuation_snapshot；pe/pb 缺失时用 factor_daily 的同名因子回退
 *
 * @param {*} db better-sqlite3 数据库句柄
 * @param {string} code 股票代码（如 "NVDA" / "09988.HK" / "300308.SZ"）
 * @param {object} factorMap factor_daily 的 factor_name -> factor_value 映射（已取最新值）
 * @returns {object} 结构化估值数据
 */
function getValuationData(db, code, factorMap) {
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

/**
 * 提取基本面相关数据（Task 1-b）
 * 优先走 fundamentals_snapshot；营收同比、净利润同比从 factorMap 补齐
 *
 * @returns {object} 结构化基本面数据
 */
function getFundamentalsData(db, code, factorMap) {
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

/**
 * 提取技术面相关数据（Task 1-c）
 * RSI/MACD/趋势强度/波动率直接从 factorMap 获取；5 日/20 日涨跌幅由 priceHistory 推导
 *
 * @returns {object} 结构化技术数据
 */
function getTechnicalData(db, code, factorMap, priceHistory) {
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

/**
 * 提取同行业股票对比数据（Task 1-d）
 * 从 stock_pool_current 按 sector 过滤同行业股票，然后对每只股票查估值/基本面/技术因子，
 * 同时计算同行业均值，为后面的 peerComparison 引擎提供输入
 *
 * @returns {object} {sector, peerCount, peers:[], avg:{}, latest:{}}
 */
function getPeerGroupData(db, code, sector) {
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

/**
 * 提取新闻、研究主张、风险提示三类数据（Task 1-e）
 * 这些都会作为"催化因素引擎"和"风险提示增强"的输入
 *
 * @returns {object} {news:[], claims:[], risks:[]}
 */
function getNewsClaimsAndRisks(db, code) {
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

/**
 * 护城河评分引擎（Task 3）
 *
 * 从 6 个维度评估公司的竞争优势，每个维度 0-10 分，
 * 综合加权得 0-100 分，同时输出关键证据链。
 *
 * @param {object} fundamentalsData 基本面结构化数据（来自 getFundamentalsData）
 * @param {object} peerGroupData 同行业数据（来自 getPeerGroupData）
 * @returns {object} { totalScore, dimensions, summary, evidenceChain }
 */
/**
 * 构建某行业的同行均值（getMoatReport 用）。
 * 列表页和详情页都调用这个函数，确保两个页面的同行对比数据完全一致。
 *
 * @param {object} db 数据库句柄
 * @param {string} code 当前股票代码
 * @param {string} sector 行业代码
 * @returns {object} { sector, peerCount, avg: { revenueYoY, grossMargin, roe } }
 */
function buildPeerAvgForSector(db, code, sector) {
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

/**
 * 护城河评分引擎（Task 3）
 *
 * 基于基本面数据（毛利率、ROE、营业利润率、自由现金流、营收等），
 * 对 6 个护城河维度打分：无形资产（品牌/技术）、成本优势、转换成本、
 * 网络效应、规模经济、渠道优势。每个维度输出 0-10 的评分及说明，
 * 汇总为 0-100 的综合护城河评分。
 *
 * @param {object} fundamentalsData 基本面结构化数据（来自 getFundamentalsData）
 * @param {object} peerGroupData 同行业数据（来自 buildPeerAvgForSector）
 * @returns {object} { totalScore, dimensions, summary, evidenceChain }
 */
function getMoatReport(fundamentalsData, peerGroupData) {
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

/**
 * 同业对标引擎（Task 4）
 *
 * 从估值（PE/PB）、盈利能力（ROE/毛利率）、成长（营收同比）、
 * 技术趋势（trendStrength）6 个维度，计算目标股票在行业内的百分位排名。
 *
 * @param {object} valuationData 估值数据（来自 getValuationData）
 * @param {object} fundamentalsData 基本面数据
 * @param {object} technicalData 技术面数据
 * @param {object} peerGroupData 同行业对标数据
 * @returns {object} { sector, peerCount, metrics, industryPosition, avg }
 */
function getPeerComparisonReport(valuationData, fundamentalsData, technicalData, peerGroupData) {
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

/**
 * 催化因素引擎（Task 5）
 *
 * 基于新闻标题和正文关键词启发式 + 研究主张 stance 字段，
 * 综合评估当前市场情绪方向和催化强度。
 *
 * @param {object} newsClaimsData { news, claims, risks }（来自 getNewsClaimsAndRisks）
 * @returns {object} { recentNews, upcomingClaims, catalystScore, netDirection, summary }
 */
function getCatalystsReport(newsClaimsData) {
  const news = (newsClaimsData?.news || []).slice(0, 10);
  const claims = newsClaimsData?.claims || [];
  const risks = newsClaimsData?.risks || [];

  // 利好 / 利空关键词（启发式匹配，中英文兼顾）
  const bullKeywords = ["增长", "上涨", "创新高", "买入", "增持", "超预期", "超预期增长",
    "获批", "中标", "签", "回购", "分红", "业绩预增", "预增", "利好",
    "涨价", "量价齐升", "订单", "突破", "入选", "上市",
    "buy", "hold", "outperform", "positive", "upgrade", "beat"];
  const bearKeywords = ["下跌", "亏损", "利空", "减持", "卖出", "下修", "调查",
    "诉讼", "违约", "风险", "暴雷", "下滑", "亏损", "承压", "拖累",
    "sell", "downgrade", "miss", "negative", "warning"];

  // --- 1) 分析每条新闻的方向 + 强度 ---
  const scoredNews = news.map((n) => {
    const txt = `${n.title || ""} ${n.summary || ""}`.toLowerCase();
    let bull = 0, bear = 0;
    for (const k of bullKeywords) if (txt.includes(k.toLowerCase())) bull++;
    for (const k of bearKeywords) if (txt.includes(k.toLowerCase())) bear++;
    // 方向：+1 利好，-1 利空，0 中性
    let direction = 0;
    if (bull > bear) direction = 1;
    else if (bear > bull) direction = -1;
    // 强度 = 关键词命中数量
    return { ...n, direction, intensity: bull + bear };
  });

  // --- 2) 分析研究主张（research claims） ---
  // 用 `stance` 字段作方向，`confidence` 作强度
  const scoredClaims = claims.map((c) => {
    const s = (c.stance || "").toLowerCase();
    let direction = 0;
    if (/买|多|加|bull|buy|outperform|strong|overweight/i.test(s)) direction = 1;
    else if (/卖|空|减|sell|bear|underweight|down|negative/i.test(s)) direction = -1;
    const intensity = (c.confidence != null ? Number(c.confidence) : 0.5) * 2;
    return { ...c, direction, intensity };
  });

  // --- 3) 综合催化评分：新闻占 60%，研究主张占 40% ---
  let newsScore = 0, newsTotal = 0;
  for (const n of scoredNews) {
    if (n.direction !== 0) {
      const w = Math.min(10, n.intensity);
      newsScore += n.direction * (10 + w * 10); // 每条 -100 ~ +100 之间加权
      newsTotal++;
    }
  }
  const newsAvg = newsTotal > 0 ? newsScore / newsTotal : 0;

  let claimScore = 0, claimTotal = 0;
  for (const c of scoredClaims) {
    if (c.direction !== 0) {
      claimScore += c.direction * (30 + c.intensity * 40); // 研究主张权重更大
      claimTotal++;
    }
  }
  const claimAvg = claimTotal > 0 ? claimScore / claimTotal : 0;

  // 风险提示对催化评分的负面影响
  let riskPenalty = 0;
  const highRisks = risks.filter((r) => (r.severity || "").toString().toLowerCase().includes("高") || (r.severity || "") === "HIGH");
  riskPenalty = Math.min(30, highRisks.length * 10);

  // 综合（-100 ~ +100）
  let catalystScore = null;
  let netDirection = "neutral";
  let summary = "暂无近期新闻或研究主张，无法评估催化方向。";
  if (newsTotal > 0 || claimTotal > 0) {
    // 按新闻 60%，研究主张 40% 加权（若无其中一项则 100% 给另一项）
    if (newsTotal > 0 && claimTotal > 0) catalystScore = Math.round(newsAvg * 0.6 + claimAvg * 0.4 - riskPenalty);
    else if (newsTotal > 0) catalystScore = Math.round(newsAvg - riskPenalty);
    else catalystScore = Math.round(claimAvg - riskPenalty);
    catalystScore = Math.max(-100, Math.min(100, catalystScore));

    if (catalystScore >= 30) netDirection = "bullish";
    else if (catalystScore <= -30) netDirection = "bearish";

    if (catalystScore >= 40) summary = `催化评分 ${catalystScore}，市场情绪显著偏多，需关注利好兑现时点。`;
    else if (catalystScore >= 10) summary = `催化评分 ${catalystScore}，市场情绪偏积极。`;
    else if (catalystScore >= -10) summary = `催化评分 ${catalystScore}，市场情绪中性，缺乏明确催化。`;
    else if (catalystScore >= -40) summary = `催化评分 ${catalystScore}，市场情绪偏谨慎，需关注利空消化。`;
    else summary = `催化评分 ${catalystScore}，市场情绪显著偏空，需高度谨慎。`;
  }

  // --- 4) 返回：取前 5 条新闻、前 10 条研究主张用于前端标签页展示 ---
  //    同时补充每条新闻的方向标签（bullish / bearish / neutral）
  const recentNews = scoredNews.slice(0, 5).map((n) => ({
    id: n.id, title: n.title, source: n.source, sourceName: n.sourceName,
    publishedAt: n.publishedAt, tickers: n.tickers, url: n.url,
    credibility: n.credibility, summary: n.summary, hasFullBody: n.hasFullBody,
    direction: n.direction > 0 ? "bullish" : (n.direction < 0 ? "bearish" : "neutral"),
    intensity: n.intensity,
  }));
  const upcomingClaims = scoredClaims.slice(0, 10).map((c) => ({
    claimId: c.claimId, claimType: c.claimType, theme: c.theme,
    claimText: c.claimText, stance: c.stance, importance: c.importance,
    confidence: c.confidence, createdAt: c.createdAt,
    direction: c.direction > 0 ? "bullish" : (c.direction < 0 ? "bearish" : "neutral"),
    intensity: c.intensity,
  }));

  return {
    recentNews,
    upcomingClaims,
    catalystScore,
    netDirection,
    summary,
  };
}

/**
 * 综合投资建议引擎（Task 6）
 *
 * 融合估值、基本面、技术面、护城河、同业对标、催化因素 6 大维度信号，
 * 输出完整决策：判决（看多/看空/中性）、综合得分、买入价、目标价、止损价、
 * 建议仓位、持有期、置信度和推理过程。
 *
 * @param {object} overallRecommendation 现有的基础推荐（来自原先的 3 个维度聚合）
 * @param {object} valuationData 估值数据
 * @param {object} fundamentalsData 基本面数据
 * @param {object} technicalData 技术面数据
 * @param {object} moatReport 护城河评分结果
 * @param {object} peerComparisonReport 同业对标结果
 * @param {object} catalystsReport 催化因素结果
 * @param {number|null} latestPrice 最新价格
 * @returns {object} 完整的投资建议对象
 */
function getEnhancedRecommendation(
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

// ============================================================
// 深度研究报告生成器（Task 9：华尔街投行风格）
//
// 参考高盛 / 摩根士丹利 / 摩根大通等顶级投行的
// Equity Research 报告格式，输出结构化文字：
//   1. 投资摘要 (Investment Thesis)
//   2. 执行摘要要点 (Executive Summary - bullets)
//   3. 估值分析 (Valuation Analysis)
//   4. 基本面分析 (Fundamental Analysis)
//   5. 护城河与竞争地位 (Moat & Competitive Positioning)
//   6. 技术分析与交易信号 (Technical Analysis)
//   7. 催化因素 (Catalysts)
//   8. 风险提示 (Risks)
//   9. 投资结论 (Investment Conclusion)
//
// 所有文字都基于数据事实自动生成，不依赖 LLM，保证稳定可用。
// ============================================================

/**
 * 生成华尔街投行风格的深度研究报告（Task 9）
 *
 * @param {string} tsCode - 股票代码
 * @param {string} name - 股票名称
 * @param {string} market - 市场标识
 * @param {string} sector - 行业
 * @param {number|null} latestPrice - 当前价
 * @param {object} valuationData - Task 1-a 的估值数据
 * @param {object} fundamentalsData - Task 1-b 的基本面数据
 * @param {object} technicalData - Task 1-c 的技术面数据
 * @param {object} moatReport - Task 3 护城河报告
 * @param {object} peerComparisonReport - Task 4 同业对标
 * @param {object} catalystsReport - Task 5 催化因素
 * @param {object} enhancedRecommendation - Task 6 综合投资建议
 * @returns {object} 结构化深度报告（每部分含标题+要点列表+文字解读）
 */
function getDeepReport(
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

// ============================================================
// API: GET /api/stock/:code - 标的详情（路由主体）
// ============================================================
app.get("/api/stock/:code", (req, res) => {
  try {
    const { code } = req.params;
    const db = getDb();

    // 1. 基本信息（池子）
    const poolInfo = db.prepare(
      "SELECT ts_code, sector, pool_type, added_date FROM stock_pool_current WHERE ts_code=?"
    ).get(code);

    // 2. 最新因子（作为所有引擎的共享数据源）
    const factorRows = db.prepare(
      `SELECT factor_name, factor_value, trade_date FROM factor_daily
       WHERE ts_code=? ORDER BY trade_date DESC LIMIT 100`
    ).all(code);
    const factorMap = {};
    for (const f of factorRows) {
      if (!factorMap[f.factor_name]) factorMap[f.factor_name] = f.factor_value;
    }

    // 3. 最新价格（区分 A/H/美股）
    let priceRows = [];
    if (code.endsWith(".SH") || code.endsWith(".SZ") || code.endsWith(".HK")) {
      priceRows = db.prepare(`SELECT close, open, high, low, vol, trade_date FROM daily_bar WHERE ts_code=? ORDER BY trade_date DESC LIMIT 30`).all(code);
    } else if (/^[A-Z]+$/.test(code)) {
      priceRows = db.prepare(`SELECT close, open, high, low, vol, trade_date FROM us_daily_bar WHERE symbol=? ORDER BY trade_date DESC LIMIT 30`).all(code);
    }

    // ===== 价格辅助变量 =====
    const priceHistory = (priceRows || []).reverse().map((r) => ({
      date: r.trade_date, close: r.close, open: r.open, high: r.high, low: r.low, vol: r.vol,
    }));

    // ===== [Task 1] 统一数据提取层：所有分析引擎只从这 5 个对象拿数据 =====
    const valuationData = getValuationData(db, code, factorMap);
    const fundamentalsData = getFundamentalsData(db, code, factorMap);
    const technicalData = getTechnicalData(db, code, factorMap, priceHistory);
    const peerGroupData = getPeerGroupData(db, code, poolInfo?.sector || null);
    // 专门用于 moatReport 的同行均值（与列表页同款，确保两个页面评分一致）
    const moatPeerAvg = buildPeerAvgForSector(db, code, poolInfo?.sector || null);
    const newsClaimsData = getNewsClaimsAndRisks(db, code);

    // ===== 兼容旧 report 逻辑（新引擎上线后可删除） =====
    const newsItems = newsClaimsData.news;
    const riskRows = newsClaimsData.risks;
    const claimRows = newsClaimsData.claims.map((c) => ({ claim_id: c.claimId, claim_type: c.claimType,
      theme: c.theme, claim_text: c.claimText, importance: c.importance,
      stance: c.stance, confidence: c.confidence, created_at: c.createdAt }));
    const valRow = { pe_ttm: valuationData.pe, pb: valuationData.pb,
      current_price: valuationData.currentPrice,
      historical_percentile: valuationData.historicalPercentile,
      valuation_confidence: valuationData.confidence,
      valuation_status: valuationData.status };
    const fundRow = { revenue: fundamentalsData.revenue, gross_profit: fundamentalsData.grossProfit,
      net_income: fundamentalsData.netIncome, gross_margin: fundamentalsData.grossMargin,
      net_margin: fundamentalsData.netMargin, roe: fundamentalsData.roe,
      operating_cash_flow: fundamentalsData.operatingCashFlow,
      free_cash_flow: fundamentalsData.freeCashFlow,
      total_debt: fundamentalsData.totalDebt, shareholders_equity: fundamentalsData.equity };

    // ===== 判断市场 + 名称 =====
    let market = "其他";
    if (code.endsWith(".SH") || code.endsWith(".SZ")) market = "A";
    else if (code.endsWith(".HK")) market = "H";
    else if (/^[A-Z]+$/.test(code)) market = "US";

    const name = getStockName(code) || code;
    const latestPrice = technicalData.latestPrice != null ? technicalData.latestPrice
                    : (valuationData.currentPrice != null ? valuationData.currentPrice : null);

    // ========== 【估值分析报告】中文解释 ==========
    const valuationReport = (() => {
      const items = [];
      if (!valRow && Object.keys(factorMap).length === 0) {
        return { score: null, summary: "暂无估值数据", items };
      }
      // 优先用 valuation_snapshot 的 PE/PB
      const pe = valRow?.pe_ttm ?? factorMap["pe_ttm"] ?? null;
      const pb = valRow?.pb ?? null;
      const marginOfSafety = valRow?.historical_percentile ?? null;
      const valScore = valRow?.valuation_confidence ?? null;

      if (pe !== null && !isNaN(pe)) {
        let label = "", text = "";
        if (pe < 15) { label = "低估"; text = `PE = ${pe.toFixed(1)}，低于 15 倍，估值偏便宜，安全边际较高。`; }
        else if (pe < 30) { label = "合理"; text = `PE = ${pe.toFixed(1)}，在 15-30 倍之间，估值基本合理。`; }
        else if (pe < 60) { label = "偏高"; text = `PE = ${pe.toFixed(1)}，超过 30 倍，估值偏高，需注意业绩兑现能力。`; }
        else { label = "泡沫"; text = `PE = ${pe.toFixed(1)}，超过 60 倍，估值严重偏高，需谨慎。`; }
        items.push({ label, metric: "PE(TTM)", value: pe.toFixed(1), text });
      }
      if (pb !== null && !isNaN(pb)) {
        let label = "", text = "";
        if (pb < 1) { label = "破净"; text = `PB = ${pb.toFixed(2)}，低于 1，已跌破净资产，深度价值股需要警惕（也可能意味着公司基本面有问题）。`; }
        else if (pb < 3) { label = "合理"; text = `PB = ${pb.toFixed(2)}，在 1-3 之间，估值合理。`; }
        else if (pb < 8) { label = "偏高"; text = `PB = ${pb.toFixed(2)}，超过 3 倍，估值偏高，通常意味着市场预期较高。`; }
        else { label = "泡沫"; text = `PB = ${pb.toFixed(2)}，超过 8 倍，估值严重偏高。`; }
        items.push({ label, metric: "PB", value: pb.toFixed(2), text });
      }
      if (marginOfSafety !== null && !isNaN(marginOfSafety)) {
        items.push({ label: "安全边际", metric: "MarginOfSafety", value: (marginOfSafety * 100).toFixed(0) + "%", text: `安全边际 = ${(marginOfSafety * 100).toFixed(0)}%，${marginOfSafety >= 0.3 ? "达到 30% 以上，较安全" : "低于 30%，需关注估值与基本面匹配度"}。` });
      }
      // 如果没有 valRow 的 PE/PB，尝试补充 factor_daily 的基础因子
      const extra = ["revenue_yoy", "net_profit_yoy", "eps_reported", "roe_reported", "debt_asset_ratio", "current_ratio"];
      for (const key of extra) {
        const v = factorMap[key];
        if (v === undefined || isNaN(v)) continue;
        const displayNames = {
          revenue_yoy: "营收同比增速", net_profit_yoy: "净利润同比增速",
          eps_reported: "EPS(每股收益)", roe_reported: "ROE(净资产收益率)",
          debt_asset_ratio: "资产负债率", current_ratio: "流动比率"
        };
        if (key === "roe_reported") {
          let label = v >= 15 ? "优秀" : v >= 8 ? "良好" : v >= 0 ? "一般" : "亏损";
          items.push({ label, metric: "ROE", value: v.toFixed(1) + "%", text: `ROE = ${v.toFixed(1)}%，${v >= 15 ? "超过 15%，属于优秀盈利能力" : v >= 8 ? "在 8-15% 之间，盈利能力尚可" : "低于 8%，盈利能力偏弱"}。` });
        } else if (key === "revenue_yoy" || key === "net_profit_yoy") {
          let label = v >= 20 ? "高增长" : v >= 5 ? "稳健" : v >= 0 ? "平缓" : "下滑";
          items.push({ label, metric: displayNames[key], value: v.toFixed(1) + "%", text: `${displayNames[key]} = ${v.toFixed(1)}%，${v >= 20 ? "增长强劲" : v >= 5 ? "增长稳健" : v >= 0 ? "增长基本持平" : "出现下滑"}。` });
        }
      }
      // 综合结论
      let summary = "暂无足够估值数据给出综合判断";
      if (items.length > 0) {
        const goodCount = items.filter(i => /低估|合理|优秀|高增长|稳健|破净/.test(i.label)).length;
        const badCount = items.filter(i => /偏高|泡沫|亏损|下滑/.test(i.label)).length;
        if (goodCount > badCount + 1) summary = `综合来看：${name} 当前估值偏合理或低估，基本面关键指标表现良好。`;
        else if (badCount > goodCount) summary = `综合来看：${name} 当前估值偏高或存在基本面隐忧，需谨慎。`;
        else summary = `综合来看：${name} 当前各项指标分化，需结合行业特性进一步分析。`;
      }
      return { 
        score: valScore, 
        pe: valRow?.pe_ttm ?? null, 
        pb: valRow?.pb ?? null, 
        ps: valRow?.ps_ttm ?? null, 
        evEbitda: valRow?.ev_ebitda_ttm ?? null, 
        marginOfSafety, 
        // FR-7 估值增强
        historicalPercentile: valRow?.historical_percentile ?? null,
        brokerTargetPrice: valRow?.broker_target_price ?? null,
        targetPrice: valRow?.broker_target_price ?? null,
        summary, 
        items 
      };
    })();

    // ========== 【基本面分析报告】中文解释 ==========
    const fundamentalsReport = (() => {
      const items = [];
      if (!fundRow && Object.keys(factorMap).length === 0) {
        return { summary: "暂无完整财务数据", items };
      }
      // 优先用 fundamentals_snapshot
      const row = fundRow || {};
      const revenue = row.revenue ?? null;
      const netIncome = row.net_income ?? null;
      const grossMargin = row.gross_margin ?? null;
      const netMargin = row.net_margin ?? null;
      const roe = row.roe ?? factorMap["roe_reported"] ?? null;
      const roic = row.roic ?? null;
      const operatingCashFlow = row.operating_cash_flow ?? null;
      const totalDebt = row.total_debt ?? null;
      const equity = row.shareholders_equity ?? null;

      // 毛利率
      if (grossMargin !== null && !isNaN(grossMargin) && grossMargin >= 0 && grossMargin <= 1) {
        const gmPct = grossMargin * 100;
        let label = gmPct >= 50 ? "高毛利" : gmPct >= 25 ? "良好" : gmPct >= 10 ? "一般" : "偏低";
        items.push({ label, metric: "毛利率", value: gmPct.toFixed(1) + "%", text: `毛利率 = ${gmPct.toFixed(1)}%，${gmPct >= 50 ? "毛利率非常高，产品/服务溢价能力强" : gmPct >= 25 ? "毛利率健康" : gmPct >= 10 ? "毛利率偏低，成本控制是关键" : "毛利率非常低，需关注是否存在亏损风险"}。` });
      }
      // 净利润率
      if (netMargin !== null && !isNaN(netMargin) && netMargin <= 1) {
        const nmPct = netMargin * 100;
        let label = nmPct >= 20 ? "优秀" : nmPct >= 10 ? "良好" : nmPct >= 0 ? "微薄" : "亏损";
        items.push({ label, metric: "净利润率", value: nmPct.toFixed(1) + "%", text: `净利润率 = ${nmPct.toFixed(1)}%，${nmPct >= 20 ? "非常优秀的盈利水平" : nmPct >= 10 ? "健康的净利润率" : nmPct >= 0 ? "净利润微薄，成本控制需加强" : "处于亏损状态"}。` });
      }
      // ROE
      if (roe !== null && !isNaN(roe) && roe < 100) {
        const roePct = roe;
        let label = roePct >= 15 ? "优秀" : roePct >= 8 ? "良好" : roePct >= 0 ? "一般" : "亏损";
        items.push({ label, metric: "ROE", value: roePct.toFixed(1) + "%", text: `ROE(净资产收益率) = ${roePct.toFixed(1)}%，${roePct >= 15 ? "长期能保持 15% 以上 ROE 的公司通常具备很强的护城河" : roePct >= 8 ? "ROE 处于中等水平" : roePct >= 0 ? "ROE 偏低，净资产使用效率有待提升" : "ROE 为负，股东权益在缩水"}。` });
      }
      // ROIC
      if (roic !== null && !isNaN(roic) && roic < 100 && roic > -100) {
        items.push({ label: roic >= 12 ? "优秀" : roic >= 8 ? "良好" : "一般", metric: "ROIC", value: roe.toFixed(1) + "%", text: `ROIC(投入资本回报率) = ${roic.toFixed(1)}%，衡量公司投入资本的真实回报。${roic >= 12 ? "明显高于 WACC，在创造价值" : "与资本成本相比需确认是否创造正收益"}。` });
      }
      // 营收规模
      if (revenue !== null && !isNaN(revenue) && revenue > 0 && revenue < 1e15) {
        const revenueText = revenue >= 1e8 ? (revenue / 1e8).toFixed(1) + "亿元" : (revenue / 1e4).toFixed(1) + "万元";
        items.push({ label: "营收规模", metric: "营业收入", value: revenueText, text: `当前报告期营收约 ${revenueText}，关注其同比增速与行业地位。` });
      }
      // 净利润规模
      if (netIncome !== null && !isNaN(netIncome) && Math.abs(netIncome) < 1e15) {
        const netIncomeText = Math.abs(netIncome) >= 1e8 ? (netIncome / 1e8).toFixed(2) + "亿元" : (netIncome / 1e4).toFixed(1) + "万元";
        items.push({ label: netIncome > 0 ? "盈利" : "亏损", metric: "净利润", value: netIncomeText, text: `当期净利润 ${netIncomeText}，${netIncome > 0 ? "盈利状态" : "亏损状态，关注亏损原因"}。` });
      }
      // 负债判断（总资产/总负债/股东权益关系）
      if (totalDebt !== null && equity !== null && !isNaN(totalDebt) && !isNaN(equity) && equity > 0) {
        const debtRatio = totalDebt / (totalDebt + equity) * 100;
        if (debtRatio < 100 && debtRatio > 0) {
          let label = debtRatio < 30 ? "稳健" : debtRatio < 60 ? "适中" : "偏高";
          items.push({ label, metric: "资产负债率", value: debtRatio.toFixed(1) + "%", text: `资产负债率约 ${debtRatio.toFixed(1)}%，${debtRatio < 30 ? "财务结构非常稳健" : debtRatio < 60 ? "财务结构适中" : "负债率较高，需关注利息负担和再融资风险"}。` });
        }
      }
      // 经营现金流
      if (operatingCashFlow !== null && !isNaN(operatingCashFlow) && operatingCashFlow < 1e15) {
        const ocfText = Math.abs(operatingCashFlow) >= 1e8 ? (operatingCashFlow / 1e8).toFixed(2) + "亿元" : (operatingCashFlow / 1e4).toFixed(1) + "万元";
        items.push({ label: operatingCashFlow > 0 ? "正向" : "负向", metric: "经营现金流", value: ocfText, text: `经营活动产生的现金流 ${ocfText}，${operatingCashFlow > 0 ? "公司自身经营能产生现金流入" : "经营活动现金流出，需关注是否依赖筹资度日"}。` });
      }
      let summary = items.length > 0 ? `${name} 的关键财务指标已汇总如上，建议结合行业对标进一步判断。` : "暂无完整财务数据，建议等待定期报告披露。";
      return { 
        summary, 
        items, 
        sourceQuality: row.source_quality || null, 
        freshness: row.freshness_status || null,
        // FR-5 增强型基本面诊断
        earningsQuality: fundamentalsData.earningsQuality,
        earningsQualityDesc: fundamentalsData.earningsQualityDesc,
        growthQuality: fundamentalsData.growthQuality,
        growthQualityDesc: fundamentalsData.growthQualityDesc,
        financialHealth: fundamentalsData.financialHealth,
        financialHealthDesc: fundamentalsData.financialHealthDesc,
      };
    })();

    // === FR-8 技术面指标计算函数 ===
    function computeTrendStrength(priceHistory) {
      if (!priceHistory || priceHistory.length < 5) return null; // 降低要求到5条
      const closes = priceHistory.map(p => p.close).filter(v => v != null && !isNaN(v));
      if (closes.length < 5) return null;
      
      // 计算线性回归斜率作为趋势强度
      const n = closes.length;
      let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
      for (let i = 0; i < n; i++) {
        sumX += i;
        sumY += closes[i];
        sumXY += i * closes[i];
        sumX2 += i * i;
      }
      const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
      const avgPrice = sumY / n;
      const trendStrength = slope / avgPrice * n; // 归一化
      return Math.round(trendStrength * 100) / 100;
    }

    function computeVolatility(priceHistory) {
      if (!priceHistory || priceHistory.length < 5) return null; // 降低要求到5条
      const closes = priceHistory.map(p => p.close).filter(v => v != null && !isNaN(v));
      if (closes.length < 5) return null;
      
      // 计算收益率的标准差（使用现有数据）
      const returns = [];
      for (let i = 1; i < closes.length; i++) {
        returns.push(Math.log(closes[i] / closes[i - 1]));
      }
      const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
      const variance = returns.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / returns.length;
      const volatility = Math.sqrt(variance) * Math.sqrt(252); // 年化波动率
      return Math.round(volatility * 1000) / 1000;
    }

    // ========== 【技术面分析报告】中文解释 ==========
    const technicalReport = (() => {
      const items = [];
      // 1. RSI
      const rsi = factorMap["rsi_14"] ?? null;
      if (rsi !== null && !isNaN(rsi)) {
        let label = "", text = "";
        if (rsi >= 70) { label = "超买"; text = `RSI(14) = ${rsi.toFixed(1)}，处于 70 以上超买区间，短期可能回调。建议关注是否形成顶背离或冲高回落。`; }
        else if (rsi >= 60) { label = "偏强"; text = `RSI(14) = ${rsi.toFixed(1)}，处于 60-70 强势区间，动能偏多。`; }
        else if (rsi >= 40) { label = "中性"; text = `RSI(14) = ${rsi.toFixed(1)}，在 40-60 中性区间，趋势不明。`; }
        else if (rsi >= 30) { label = "偏弱"; text = `RSI(14) = ${rsi.toFixed(1)}，在 30-40 弱势区间，动能偏空。`; }
        else { label = "超卖"; text = `RSI(14) = ${rsi.toFixed(1)}，低于 30 处于超卖区间，短期可能出现反弹或企稳信号。`; }
        items.push({ label, metric: "RSI(14)", value: rsi.toFixed(1), text });
      }
      // 2. MACD
      const macdHist = factorMap["macd_hist"] ?? null;
      const macdDif = factorMap["macd_dif"] ?? null;
      const macdDea = factorMap["macd_dea"] ?? null;
      if (macdDif !== null && macdDea !== null && !isNaN(macdDif)) {
        let label = "", text = "";
        if (macdDif > macdDea && macdDif > 0) { label = "金叉上涨"; text = `MACD DIF = ${macdDif.toFixed(4)}，DEA = ${macdDea.toFixed(4)}，DIF 上穿 DEA 且都在零轴上方，经典多头信号，趋势加速。`; }
        else if (macdDif > macdDea) { label = "金叉"; text = `MACD DIF = ${macdDif.toFixed(4)}，DEA = ${macdDea.toFixed(4)}，DIF 上穿 DEA（仍在零轴下方），反弹信号需结合量能确认。`; }
        else if (macdDif < macdDea && macdDif < 0) { label = "死叉下跌"; text = `MACD DIF = ${macdDif.toFixed(4)}，DEA = ${macdDea.toFixed(4)}，DIF 下穿 DEA 且都在零轴下方，经典空头信号。`; }
        else { label = "死叉"; text = `MACD DIF = ${macdDif.toFixed(4)}，DEA = ${macdDea.toFixed(4)}，DIF 下穿 DEA，动能转弱。`; }
        items.push({ label, metric: "MACD", value: `${macdDif.toFixed(4)} / ${macdDea.toFixed(4)}`, text });
      }
      // 3. 趋势强度
      const trend = factorMap["trend_strength"] ?? null;
      if (trend !== null && !isNaN(trend)) {
        items.push({ label: trend > 0.5 ? "强势" : trend > 0 ? "偏强" : "震荡", metric: "趋势强度", value: trend.toFixed(2), text: `趋势强度 = ${trend.toFixed(2)}，${trend > 0.8 ? "非常强势的单边趋势，注意追高风险" : trend > 0.5 ? "趋势较明显，跟随为主" : trend > 0 ? "趋势温和，震荡偏多" : "震荡偏弱，耐心等待方向"}。` });
      }
      // 4. 波动率
      const vol = factorMap["volatility_20"] ?? null;
      if (vol !== null && !isNaN(vol)) {
        items.push({ label: vol > 0.05 ? "高波动" : "正常波动", metric: "波动率(20日)", value: (vol * 100).toFixed(1) + "%", text: `20日波动率 = ${(vol * 100).toFixed(1)}%，${vol > 0.08 ? "波动较大，仓位和止损需更谨慎" : vol > 0.04 ? "波动正常" : "波动较低，需等待催化"}。` });
      }
      // 5. 价格动量：近 5 日 / 近 20 日涨跌幅
      if (priceHistory && priceHistory.length >= 5) {
        const pNow = priceHistory[priceHistory.length - 1]?.close;
        const p5 = priceHistory[Math.max(0, priceHistory.length - 5)]?.close;
        const p20 = priceHistory[Math.max(0, priceHistory.length - 20)]?.close;
        if (pNow && p5 && p5 > 0) {
          const r5 = (pNow / p5 - 1) * 100;
          let label = r5 >= 10 ? "5日暴涨" : r5 >= 5 ? "5日强势" : r5 > 0 ? "5日微涨" : r5 > -5 ? "5日微跌" : "5日大跌";
          items.push({ label, metric: "5日涨跌幅", value: r5.toFixed(2) + "%", text: `近 5 日累计 ${r5 >= 0 ? "上涨" : "下跌"} ${Math.abs(r5).toFixed(2)}%，${Math.abs(r5) > 10 ? "波动异常大，需关注是否有基本面催化" : "短期波动正常"}。` });
        }
        if (pNow && p20 && p20 > 0) {
          const r20 = (pNow / p20 - 1) * 100;
          let label = r20 >= 20 ? "20日暴涨" : r20 >= 10 ? "20日强势" : r20 > 0 ? "20日上涨" : r20 > -10 ? "20日回调" : "20日暴跌";
          items.push({ label, metric: "20日涨跌幅", value: r20.toFixed(2) + "%", text: `近 20 日累计 ${r20 >= 0 ? "上涨" : "下跌"} ${Math.abs(r20).toFixed(2)}%，${r20 >= 20 ? "短期强势，注意回调风险" : r20 <= -20 ? "短期超跌，可能有技术性反弹机会" : "处于常规波动"}。` });
        }
      }
      let summary = items.length > 0 ? `综合技术指标：${name} ${items.filter(i => /超买|强势|金叉|暴涨|上涨/.test(i.label)).length >= 2 ? "短期偏多，关注动能是否持续" : items.filter(i => /超卖|弱势|死叉|大跌|暴跌|下跌/.test(i.label)).length >= 2 ? "短期偏弱，注意风险" : "目前处于震荡阶段，等待更明确的信号"}。` : "暂无足够技术指标数据。";
      return { 
        summary, 
        items,
        // FR-8 技术面增强
        trendStrength: factorMap["trend_strength"] ?? computeTrendStrength(priceHistory),
        volatility20: factorMap["volatility_20"] ?? computeVolatility(priceHistory),
      };
    })();

    // ========== 综合投资建议 ==========
    const overallRecommendation = (() => {
      const allItems = [...valuationReport.items, ...fundamentalsReport.items, ...technicalReport.items];
      const bullSignals = allItems.filter(i => /低估|合理|优秀|高增长|稳健|高毛利|破净|正向|金叉|上涨|强势|超卖/.test(i.label) && !/偏高|泡沫|亏损|下滑|超买|大跌|暴跌|死叉|下跌|偏弱/.test(i.label)).length;
      const bearSignals = allItems.filter(i => /偏高|泡沫|亏损|下滑|超买|死叉|大跌|暴跌|下跌|偏弱/.test(i.label)).length;
      let verdict = "", text = "";
      if (bullSignals - bearSignals >= 3) {
        verdict = "偏多";
        text = `${name} 在估值、基本面、技术面三大维度中，正面信号明显多于负面信号。综合建议：在估值合理的前提下，可考虑纳入观察或试探性建仓。`;
      } else if (bullSignals - bearSignals >= 1) {
        verdict = "中性偏多";
        text = `${name} 正面信号略多于负面信号。综合建议：保持观察，等待更明确的切入点（如回调后估值更合理、或技术面确认突破）。`;
      } else if (bearSignals - bullSignals >= 2) {
        verdict = "偏空";
        text = `${name} 在估值、基本面或技术面存在多项负面信号。综合建议：若已持有，考虑降低仓位或严格止损；若未持有，建议等待更健康的信号出现。`;
      } else {
        verdict = "中性";
        text = `${name} 当前各维度信号分化，没有明确的多空结论。综合建议：耐心等待催化事件（财报/行业政策/重大订单）或更清晰的趋势信号。`;
      }
      const score = Math.round(Math.max(0, Math.min(10, 5 + bullSignals - bearSignals)) * 10) / 10;
      return { verdict, text, score, bullSignals, bearSignals };
    })();

    // ========== 风险提示整理 ==========
    const riskAlerts = riskRows.map((r) => ({
      alertId: r.alert_id, alertTime: r.alert_time, alertType: r.alert_type,
      severity: r.severity, message: r.message, action: r.action,
    }));

    // ========== 研究主张整理 ==========
    const claims = claimRows.map((r) => ({
      claimId: r.claim_id, claimType: r.claim_type, importance: r.importance,
      stance: r.stance, confidence: r.confidence, claimText: r.claim_text,
      theme: r.theme, createdAt: r.created_at,
    }));

    // ===== [Task 2] 决策引擎：综合推荐 + 护城河 + 同业对标 + 催化因素 =====
    // --- Task 3：护城河评分 ---
    const moatReport = getMoatReport(fundamentalsData, moatPeerAvg);

    // --- Task 4：同业对标 ---
    const peerComparisonReport = getPeerComparisonReport(valuationData, fundamentalsData, technicalData, peerGroupData);

    // --- Task 5：催化因素 ---
    const catalystsReport = getCatalystsReport(newsClaimsData);

    // --- Task 6：综合投资建议引擎 ---
    const enhancedRecommendation = getEnhancedRecommendation(
      overallRecommendation,
      valuationData, fundamentalsData, technicalData,
      moatReport, peerComparisonReport, catalystsReport,
      latestPrice
    );

    // === 一致性修复：使用与列表页同款的统一评分引擎作为主 compositeScore/verdict ===
    const unified = computeUnifiedScore(valuationData, fundamentalsData, technicalData, moatReport);
    const _dbg_beforeScore = enhancedRecommendation.compositeScore;
    const _dbg_beforeVerdict = enhancedRecommendation.verdict;
    if (unified?.compositeScore != null) {
      enhancedRecommendation.compositeScore = unified.compositeScore;
      enhancedRecommendation.score = unified.compositeScore;
    }
    if (unified?.verdict) {
      enhancedRecommendation.verdict = unified.verdict;
    }
    console.log(`[DEBUG-SCORE] ${code} enhanced=${_dbg_beforeScore} unified=${unified?.compositeScore} final=${enhancedRecommendation.compositeScore} verdict=${enhancedRecommendation.verdict}`);
    console.log(`[DEBUG-SCORE] dims val=${unified?.valScore} fund=${unified?.fundScore} tech=${unified?.techScore} moat=${unified?.moatScore} peer=${unified?.peerScore} cat=${unified?.catalystScore}`);

    // --- Task 9：深度研究报告（华尔街投行风格）
    const deepReport = getDeepReport(
      code, name, market, poolInfo?.sector || "", latestPrice,
      valuationData, fundamentalsData, technicalData,
      moatReport, peerComparisonReport, catalystsReport,
      enhancedRecommendation
    );

    res.json({
      tsCode: code, name, market,
      sector: poolInfo?.sector || "",
      poolType: poolInfo?.pool_type || "",
      addedDate: poolInfo?.added_date || "",
      latestPrice,
      priceHistory,
      factors: factorMap,
      news: newsItems,
      // ===== 新增：完整分析报告（Task 2-9 全部完成）
      report: {
        overallRecommendation: enhancedRecommendation,
        valuation: valuationReport,
        fundamentals: fundamentalsReport,
        technical: technicalReport,
        riskAlerts,
        claims,
        moat: moatReport,
        peerComparison: peerComparisonReport,
        catalysts: catalystsReport,
        // --- Task 9：华尔街投行风格的深度文字报告
        deepReport,
      },
      updatedAt: new Date().toISOString(),
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ============================================================
// API: GET /api/discoveries
// ============================================================

// ============================================================
// API: GET /api/phases - 研究流程状态
// 后端：从 config/phase*.json 读取 Phase 定义，
//       从 10_logs/ 读取运行历史，判断各 Phase 当前状态
// 前端暂不展示（PhaseTimeline 组件已禁用），但系统内部需要了解状态
// ============================================================
app.get("/api/phases", (_req, res) => {
  try {
    const data = cached("phases", () => {
      const phases = loadAllPhaseConfigs();
      const runInfo = getSchedulerPhaseRuns();

      // Phase ID → 中文名称映射
      const phaseNameMap = {
        phase100: "持续生产流水线",
        phase101: "实盘交易就绪",
        phase102: "回测就绪",
        phase103: "风控就绪",
        phase104: "人工审批就绪",
        phase105: "熔断就绪",
        phase106: "就绪集成",
        phase107: "模拟交易边界",
        phase108: "执行就绪",
        phase109: "操作员就绪",
        phase110: "操作员分配",
        phase111: "个人 Owner 模式",
        phase112: "机会雷达",
        phase113: "交叉评分",
        phase114: "催化剂检测",
        phase115: "候选看板",
        phase116: "研究循环",
        phase117: "每日主循环",
        phase118: "系统健康检查",
        phase119: "持续改进",
        phase120: "项目收尾",
        phase121: "外部源扩展",
        phase122: "每日研究简报",
        phase123: "反馈记忆",
        phase124: "决策日志",
        phase125: "结果追踪",
        phase126: "信号有效性评估",
        phase127: "主循环收尾",
        phase128: "外部源探测",
        phase129: "官方源兜底",
        phase130: "CNINFO 决议",
        phase131: "替代源集成",
        phase132: "估值硬化",
        phase133: "季节分析",
        phase134: "个人研究控制台",
        phase135: "Owner 反馈集成",
        phase136: "深度研究工作流",
        phase137: "深度研究执行",
        phase138: "研究论题库",
        phase139: "定时本地运行",
        phase140: "系统硬化",
        phase141: "HTML 看板",
        phase142: "标的详情页",
        phase143: "交叉链接导航",
        phase144: "反馈工作流",
        phase145: "Agent 编排",
        phase146: "Agent 记忆队列",
        phase147: "标的入池",
        phase148: "候选激活",
        phase149: "Agent 指令",
        phase150: "观察池分层",
        phase151: "自动发现管线",
        phase152: "候选入池评分",
        phase153: "候选入池评审",
        phase154: "多 Agent 研究循环",
        phase155: "Agent 调度",
        phase156: "Owner 激活评审",
        phase157: "决策输入工作流",
        phase158: "决策 UI",
        phase159: "决策提交",
        phase160: "决策示例包",
        phase161: "决策反馈 UI",
        phase162: "网络候选充实",
        phase163: "候选充实执行",
        phase164: "候选充实控制台",
        phase165: "就绪修复研究包",
        phase166: "实时证据填充",
        phase167: "决策评审包控制台",
        phase168: "决策提交",
        phase169: "决策撰写指南",
        phase170: "输入验证",
        phase171: "Owner 最终确认",
        phase172: "正式覆盖申请",
        phase173: "Owner 决策准备",
        phase174: "申请后覆盖控制台",
        phase175: "研究任务运行器",
      };

      // 判断状态：最近 24h 内运行 = active / 24h-7天 = completed / 从未运行 = pending
      const now = Date.now();
      const DAY_MS = 24 * 60 * 60 * 1000;
      const WEEK_MS = 7 * DAY_MS;

      const result = phases.map((p) => {
        const num = parseInt(p.phase_id.replace("phase", ""));
        const name = phaseNameMap[p.phase_id] || p.phase_id.replace("phase", "Phase ");
        const strategy = p.strategy.replace(/_/g, " ");
        const run = runInfo[num];

        let status = "pending";
        let pct = 0;
        let lastRunAt = null;

        if (run) {
          lastRunAt = run.latest;
          const runAge = now - new Date(run.latest).getTime();
          if (runAge < DAY_MS) {
            status = "active";
            pct = 100;
          } else if (runAge < WEEK_MS) {
            status = "completed";
            pct = 80;
          } else {
            status = "completed";
            pct = 60;
          }
        }

        return {
          phaseId: p.phase_id,
          phaseName: name,
          description: strategy,
          status,
          taskCount: 1,
          completedCount: pct === 100 ? 1 : 0,
          lastRunAt,
          runCount: run?.count || 0,
        };
      });

      // 只返回 phase100-175
      const mainPhases = result.filter((p) => {
        const n = parseInt(p.phaseId.replace("phase", ""));
        return n >= 100 && n <= 175;
      });

      return { phases: mainPhases, updatedAt: new Date().toISOString() };
    });
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ============================================================
// 静态文件服务
// ============================================================
const distDir = path.resolve(__dirname, "..", "dist");
app.use(express.static(distDir));
app.use((req, res, next) => {
  if (req.path.startsWith("/api/")) return next();
  if (req.method !== "GET") return next();
  res.sendFile(path.join(distDir, "index.html"));
});

// —— 调试导出（供 _debug_*.js 测试脚本使用；不影响服务器正常运行）
export {
  app as legacyApp,
  getValuationData, getFundamentalsData, getTechnicalData,
  buildPeerAvgForSector, getPeerGroupData, getMoatReport,
  getPeerComparisonReport, getCatalystsReport,
  computeUnifiedScore, getEnhancedRecommendation,
};
