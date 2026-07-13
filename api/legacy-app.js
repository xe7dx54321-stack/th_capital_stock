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
import {
  buildPeerAvgForSector,
  getFundamentalsData,
  getNewsClaimsAndRisks,
  getPeerGroupData,
  getValuationData,
} from "./repositories/research-readers.js";
import { getStockName } from "./registries/stock-registry.js";
import { createResearchRouter } from "./routes/research.js";
import { getDeepReport } from "./services/deep-report-service.js";
import { getEnhancedRecommendation } from "./services/recommendation-service.js";
import { getMoatReport, getPeerComparisonReport } from "./services/research-analysis-service.js";
import { getCatalystsReport } from "./services/report-service.js";
import { computeUnifiedScore, getTechnicalData } from "./services/scoring-service.js";

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

/**
 * 提取基本面相关数据（Task 1-b）
 * 优先走 fundamentals_snapshot；营收同比、净利润同比从 factorMap 补齐
 *
 * @returns {object} 结构化基本面数据
 */

/**
 * 提取技术面相关数据（Task 1-c）
 * RSI/MACD/趋势强度/波动率直接从 factorMap 获取；5 日/20 日涨跌幅由 priceHistory 推导
 *
 * @returns {object} 结构化技术数据
 */

/**
 * 提取同行业股票对比数据（Task 1-d）
 * 从 stock_pool_current 按 sector 过滤同行业股票，然后对每只股票查估值/基本面/技术因子，
 * 同时计算同行业均值，为后面的 peerComparison 引擎提供输入
 *
 * @returns {object} {sector, peerCount, peers:[], avg:{}, latest:{}}
 */

/**
 * 提取新闻、研究主张、风险提示三类数据（Task 1-e）
 * 这些都会作为"催化因素引擎"和"风险提示增强"的输入
 *
 * @returns {object} {news:[], claims:[], risks:[]}
 */

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

/**
 * 催化因素引擎（Task 5）
 *
 * 基于新闻标题和正文关键词启发式 + 研究主张 stance 字段，
 * 综合评估当前市场情绪方向和催化强度。
 *
 * @param {object} newsClaimsData { news, claims, risks }（来自 getNewsClaimsAndRisks）
 * @returns {object} { recentNews, upcomingClaims, catalystScore, netDirection, summary }
 */

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
