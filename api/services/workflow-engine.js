/**
 * Agent Workflow 引擎 - 真正的多轮对话工作流系统
 * 
 * 核心设计理念：
 *   1. LLM 作为"流程规划师"，分析问题后动态规划最佳执行流程
 *   2. 工具作为"执行者"，按规划执行具体操作
 *   3. 记忆系统作为"知识库"，提供历史上下文
 *   4. 上下文管理器维护多轮对话状态
 * 
 * 工作流生命周期：
 *   问题分析 → 流程规划 → 数据收集 → 记忆检索 → 分析综合 → 报告生成 → 决策建议
 * 
 * 小白讲解：
 *   这个系统就像一个"投研团队"：
 *   - LLM 是团队领导，负责分析问题、规划工作流程
 *   - 工具是团队成员，负责执行具体任务（查数据、找新闻、算估值）
 *   - 记忆系统是档案室，保存历史研究成果
 *   - 上下文管理器是会议记录，记录对话过程
 */

import { createChatCompletion, isModelAvailable } from "./llm-service.js";
import { VectorMemory } from "./vector-memory.js";
import { MemoryService } from "./memory-service.js";
import { MarketDataService } from "./market-data-service.js";
import { DecisionService } from "./decision-service.js";
import { buildValueScores } from "./scoring-service.js";
import { buildDiscoveries } from "./discovery-service.js";
import { ChineseNewsService } from "./chinese-news-service.js";
import { fetchRealtimeData, fetchTopGainers, fetchTopLosers, fetchVolumeSurge, fetchPriceMovement } from "./realtime-data-service.js";
import { EastmoneyDataService } from "./eastmoney-data-service.js";
import { WallstreetDataService } from "./wallstreet-data-service.js";
import { MappingAnalysisService } from "./mapping-analysis-service.js";
import { IntentEngine } from "./intent-engine.js";
import { STOCK_NAME_MAP, resolveKnownTicker, resolveKnownTickers } from "./security-aliases.js";
import { validateEvidenceCitations } from "./citation-validator.js";
import { resolveTaskRelation, isFollowUpQuestion } from "./research-task-contracts.js";
import { ResearchSessionState, SessionStateStore } from "./research-session-state.js";
import { TaskGraphRegistry, createDefaultRegistry } from "./task-graph-registry.js";
import { ConversationTaskRouterV2, createRegistryLlmRouter } from "./conversation-task-router-v2.js";
import {
  createEvidenceEnvelope,
  createEvidenceSnapshot,
  formatEvidenceCatalogForPrompt,
  summarizeDataHealth,
} from "./data-envelope.js";

// 东方财富增强数据服务单例（资金流向+龙虎榜+多季度财务历史）
// 全局复用，避免每个 SubAgent 重复创建实例
const eastmoneyDataService = new EastmoneyDataService();

// 华尔街数据服务单例（美股分析师评级+目标价+新闻）
const wallstreetDataService = new WallstreetDataService();

// 映射分析服务单例（A股-美股映射关系分析）
const mappingAnalysisService = new MappingAnalysisService();

// 意图引擎单例（自然语言理解与任务拆解）
const intentEngine = new IntentEngine();

const WRITE_TOOL_IDS = new Set(["save_memory", "create_decision"]);

function isWriteToolAuthorized(toolId, context) {
  if (toolId === "save_memory") return context.input?.allowMemoryWrite === true;
  if (toolId === "create_decision") {
    return context.input?.allowDecisionWrite === true && context.input?.decisionReviewApproved === true;
  }
  return true;
}

let intentEngineInitialized = false;
function initIntentEngine() {
  if (!intentEngineInitialized) {
    intentEngine.setAvailableTools(AGENT_TOOLS);
    intentEngine.setAvailableTasks(TASK_TYPES);
    intentEngineInitialized = true;
  }
}

/**
 * 合并两个新闻列表并去重
 *
 * 参数：
 *   primary:   优先级高的新闻列表（如中文源，排前面）
 *   secondary: 优先级低的新闻列表（如数据库，排后面）
 *   maxItems:  合并后最多保留几条，默认 8
 *
 * 返回：
 *   去重后的合并新闻列表
 */
function mergeNewsDedup(primary, secondary, maxItems = 8) {
  const seenUrls = new Set();
  const merged = [];
  for (const item of [...primary, ...secondary]) {
    const url = item.url || item.link || "";
    if (url && seenUrls.has(url)) continue;
    if (url) seenUrls.add(url);
    merged.push(item);
    if (merged.length >= maxItems) break;
  }
  return merged;
}

function isHighRiskTradingName(name = "") {
  return /(?:^|\*)ST|退市|退$/i.test(String(name).trim());
}

function opportunityCandidate(item) {
  return item && !isHighRiskTradingName(item.name) && Number.isFinite(Number(item.pct_chg));
}

/**
 * 解析单个股票代码/名称
 * 
 * 参数：
 *   input: 用户输入的字符串（如 "300308.SZ" 或 "中际旭创"）
 * 
 * 返回：
 *   标准化的股票代码（如 "300308.SZ"），如果没有匹配则返回原字符串
 */
export function resolveTicker(input) {
  if (!input) return null;
  const known = resolveKnownTicker(input);
  if (known) return known;
  return input.trim();
}

/**
 * 从用户查询中解析多个股票
 * 
 * 参数：
 *   query: 用户的完整查询字符串
 * 
 * 返回：
 *   股票代码数组（如 ["300308.SZ", "688627.SH"]）
 * 
 * 小白讲解：
 *   这个函数就像一个"多股票探测器"，从用户的话里找出所有提到的股票。
 *   比如用户说"帮我对比中际旭创和精智达"，它会返回两个股票代码。
 */
export function resolveMultipleTickers(query) {
  if (!query) return [];
  return resolveKnownTickers(query);
}

/**
 * 数据清洗和单位修正函数
 * 
 * 参数：
 *   fundamentals: 原始基本面数据对象
 * 
 * 返回：
 *   清洗后的基本面数据对象
 * 
 * 小白讲解：
 *   这个函数就像一个"数据医生"，检查财务数据是否正常。
 *   比如毛利润2806亿，但营收才382亿，这明显不对，
 *   它会自动把毛利润除以10，变成280亿，这样就合理了。
 */
function cleanFundamentals(fundamentals) {
  if (!fundamentals) return fundamentals;
  
  const cleaned = { ...fundamentals };
  const revenue = cleaned.revenue || 0;
  
  // 1. 修复毛利润单位（毛利率通常在10-80%）
  if (cleaned.gross_profit && revenue > 0) {
    let ratio = cleaned.gross_profit / revenue;
    // 如果毛利率 > 1（即100%以上），说明单位可能错了，除以10直到合理
    while (ratio > 1 && cleaned.gross_profit > 100) {
      cleaned.gross_profit = cleaned.gross_profit / 10;
      ratio = cleaned.gross_profit / revenue;
    }
    // 如果毛利率 < 0.05（5%以下），乘以10
    while (ratio < 0.05 && cleaned.gross_profit > 0) {
      cleaned.gross_profit = cleaned.gross_profit * 10;
      ratio = cleaned.gross_profit / revenue;
    }
    cleaned.gross_margin = cleaned.gross_profit / revenue;
  }
  
  // 2. 修复营业利润单位（营业利润率通常在0-50%）
  if (cleaned.operating_income && revenue > 0) {
    let ratio = cleaned.operating_income / revenue;
    while (ratio > 0.8 && cleaned.operating_income > 100) {
      cleaned.operating_income = cleaned.operating_income / 10;
      ratio = cleaned.operating_income / revenue;
    }
    while (ratio < 0.01 && cleaned.operating_income > 0 && ratio > 0) {
      cleaned.operating_income = cleaned.operating_income * 10;
      ratio = cleaned.operating_income / revenue;
    }
    cleaned.operating_margin = cleaned.operating_income / revenue;
  }
  
  // 3. 修复净利润单位（与营业利润的关系）
  if (cleaned.operating_income && cleaned.net_income && cleaned.operating_income > 0) {
    let ratio = cleaned.net_income / cleaned.operating_income;
    // 净利润通常是营业利润的0.5-1.2倍（考虑税费和其他收支）
    while (ratio < 0.1 && cleaned.net_income > 0) {
      cleaned.net_income = cleaned.net_income * 10;
      ratio = cleaned.net_income / cleaned.operating_income;
    }
    while (ratio > 2 && cleaned.net_income > 100) {
      cleaned.net_income = cleaned.net_income / 10;
      ratio = cleaned.net_income / cleaned.operating_income;
    }
    cleaned.net_margin = cleaned.net_income / revenue;
  }
  
  // 4. 修复股东权益单位（通常是营收的0.5-3倍）
  if (cleaned.shareholders_equity && revenue > 0) {
    let ratio = cleaned.shareholders_equity / revenue;
    // 如果股东权益远小于营收（<0.1倍），乘以1000000
    while (ratio < 0.1 && cleaned.shareholders_equity < 10000000000) {
      cleaned.shareholders_equity = cleaned.shareholders_equity * 10;
      ratio = cleaned.shareholders_equity / revenue;
    }
    // 如果股东权益远大于营收（>50倍），除以10
    while (ratio > 50 && cleaned.shareholders_equity > 1000000) {
      cleaned.shareholders_equity = cleaned.shareholders_equity / 10;
      ratio = cleaned.shareholders_equity / revenue;
    }
  }
  
  // 5. 修复总负债单位（通常不会超过股东权益的10倍）
  if (cleaned.total_debt && cleaned.shareholders_equity && cleaned.shareholders_equity > 0) {
    let ratio = cleaned.total_debt / cleaned.shareholders_equity;
    while (ratio > 50 && cleaned.total_debt > 1000000) {
      cleaned.total_debt = cleaned.total_debt / 10;
      ratio = cleaned.total_debt / cleaned.shareholders_equity;
    }
  }
  
  // 6. 修复现金单位（通常是亿元级别）
  if (cleaned.cash_and_equivalents) {
    if (cleaned.cash_and_equivalents < 100 && cleaned.cash_and_equivalents > 0) {
      cleaned.cash_and_equivalents = cleaned.cash_and_equivalents * 100000000;
    }
    if (cleaned.cash_and_equivalents > 100000000000000) {
      cleaned.cash_and_equivalents = cleaned.cash_and_equivalents / 1000000;
    }
  }
  
  // 7. 修复EPS单位（通常在0-50元之间）
  if (cleaned.eps_basic && cleaned.eps_basic > 100) {
    cleaned.eps_basic = cleaned.eps_basic / 1000;
  }
  if (cleaned.eps_diluted && cleaned.eps_diluted > 100) {
    cleaned.eps_diluted = cleaned.eps_diluted / 1000;
  }
  
  // 8. 修复资本支出单位
  if (cleaned.capex && revenue > 0) {
    let ratio = cleaned.capex / revenue;
    while (ratio > 2 && cleaned.capex > 100) {
      cleaned.capex = cleaned.capex / 10;
      ratio = cleaned.capex / revenue;
    }
  }
  
  // 9. 根据修复后的股东权益和净利润重新计算ROE
  if (cleaned.net_income && cleaned.shareholders_equity && cleaned.shareholders_equity > 0) {
    cleaned.roe = cleaned.net_income / cleaned.shareholders_equity;
  }
  
  // 10. 根据修复后的数据重新计算ROIC
  if (cleaned.operating_income && cleaned.shareholders_equity && cleaned.total_debt) {
    const investedCapital = cleaned.shareholders_equity + cleaned.total_debt;
    if (investedCapital > 0) {
      cleaned.roic = cleaned.operating_income / investedCapital;
    }
  }
  
  // 11. 确保ROE和ROIC是小数形式（0-1之间）
  if (cleaned.roe && cleaned.roe > 10) {
    cleaned.roe = cleaned.roe / 100;
  }
  if (cleaned.roe && cleaned.roe > 1) {
    cleaned.roe = cleaned.roe / 10;
  }
  if (cleaned.roic && cleaned.roic > 10) {
    cleaned.roic = cleaned.roic / 100;
  }
  if (cleaned.roic && cleaned.roic > 1) {
    cleaned.roic = cleaned.roic / 10;
  }
  
  return cleaned;
}

/**
 * 子Agent类 —— 用于并行执行单标深度分析
 * 
 * 功能：
 *   每个子Agent负责一只股票的全方位独立分析。
 *   主Agent派发多个子Agent并行执行，最后汇总结果。
 * 
 * 小白讲解：
 *   想象主Agent是投研总监，子Agent是各个行业的研究员。
 *   总监说"同时分析中际旭创、罗博特科、科瑞技术"，
 *   三个研究员就同时开工，各自深挖自己负责的标的，
 *   最后把研究成果汇总给总监做横向对比。
 */
class SubAgent {
  constructor(ticker, parentContext) {
    this.ticker = ticker;
    this.parentContext = parentContext;
    this.context = {
      userQuery: parentContext.userQuery,
      currentTaskType: "stock_deep_analysis",
      data: {},
      input: {},
      currentInput: {},
    };
    this.executionHistory = [];
  }

  addLog(stepId, message, data = null) {
    this.executionHistory.push({ stepId, message, data, timestamp: Date.now() });
  }

  async executeSingleStockAnalysis() {
    this.addLog("system", `子Agent开始分析 ${this.ticker}`);

    // 步骤1: 解析实体
    const dataService = new MarketDataService();
    try {
      const stockInfo = dataService.resolveEntity(this.ticker);
      this.context.data.stockEntity = stockInfo;
      this.context.data.currentTicker = stockInfo.tsCode || this.ticker;
      this.addLog("resolve_entity", `已解析：${stockInfo.name}（${stockInfo.tsCode}）`);
    } catch (e) {
      this.addLog("resolve_entity", `解析失败：${e.message}`);
      return { success: false, error: e.message, ticker: this.ticker };
    } finally { dataService.close(); }

    // 步骤2: 查询记忆
    try {
      const memService = new MemoryService();
      const vector = new VectorMemory();
      try {
        const stockMemories = memService.getMemoriesForTicker(this.ticker, { limit: 5 });
        this.context.data.memoryResults = stockMemories;
        this.context.data.memoryContextText = memService.formatMemoriesAsContext(stockMemories);
        this.addLog("query_memory", `找到 ${stockMemories.length} 条历史记忆`);
      } finally { memService.close(); vector.close(); }
    } catch (e) {
      this.addLog("query_memory", `记忆查询失败：${e.message}`);
    }

    // 步骤3: 获取股票全景数据（包含更多维度）
    try {
      const dataService = new MarketDataService();
      try {
        const dailyBars = dataService.getDailyBars(this.ticker, 20);
        const valuation = dataService.getValuation(this.ticker);
        const rawFundamentals = dataService.getFundamentals(this.ticker);
        const fundamentals = cleanFundamentals(rawFundamentals);
        const factors = dataService.getFactors(this.ticker);
        const riskAlerts = dataService.getRiskAlerts(this.ticker, 3);
        const stockPoolInfo = dataService.getStockPoolInfo(this.ticker);
        const decisions = dataService.getDecisions(this.ticker, 2);

        let momentum5d = null, momentum20d = null;
        if (dailyBars.length >= 2) {
          const latest = dailyBars[0];
          const fiveDaysAgo = dailyBars[Math.min(4, dailyBars.length - 1)];
          const twentyDaysAgo = dailyBars[Math.min(19, dailyBars.length - 1)];
          if (latest?.close && fiveDaysAgo?.close) momentum5d = ((latest.close - fiveDaysAgo.close) / fiveDaysAgo.close) * 100;
          if (latest?.close && twentyDaysAgo?.close) momentum20d = ((latest.close - twentyDaysAgo.close) / twentyDaysAgo.close) * 100;
        }

        const stockEntity = this.context.data.stockEntity || {};
        this.context.data.instrumentData = {
          ticker: this.ticker,
          name: stockEntity.name || this.ticker,
          sector: stockEntity.sector || "未知",
          peers: stockEntity.peers || [],
          usBenchmarks: stockEntity.usBenchmarks || [],
          dailyBars: dailyBars.slice(0, 5).map(b => ({ date: b.trade_date, open: b.open, close: b.close, high: b.high, low: b.low, volume: b.vol, pctChg: b.pct_chg })),
          latestPrice: dailyBars[0]?.close || valuation?.current_price || null,
          latestDate: dailyBars[0]?.trade_date || null,
          valuation: valuation ? {
            pe: valuation.pe_ttm, pb: valuation.pb, ps: valuation.ps_ttm,
            evEbitda: valuation.ev_ebitda_ttm, marketCap: valuation.market_cap,
            historicalPercentile: valuation.historical_percentile,
            historicalPercentile1y: valuation.historical_percentile_1y,
            historicalPercentile3y: valuation.historical_percentile_3y,
            historicalPercentile5y: valuation.historical_percentile_5y,
            peerPercentile: valuation.peer_percentile,
            brokerTargetPrice: valuation.broker_target_price,
            valuationStatus: valuation.valuation_status,
          } : null,
          fundamentals: fundamentals ? {
            revenue: fundamentals.revenue, grossProfit: fundamentals.gross_profit,
            operatingIncome: fundamentals.operating_income, netIncome: fundamentals.net_income,
            epsBasic: fundamentals.eps_basic, epsDiluted: fundamentals.eps_diluted,
            operatingCashFlow: fundamentals.operating_cash_flow, capex: fundamentals.capex,
            freeCashFlow: fundamentals.free_cash_flow, cash: fundamentals.cash_and_equivalents,
            totalDebt: fundamentals.total_debt, equity: fundamentals.shareholders_equity,
            grossMargin: fundamentals.gross_margin, operatingMargin: fundamentals.operating_margin,
            netMargin: fundamentals.net_margin, roe: fundamentals.roe, roic: fundamentals.roic,
            period: fundamentals.period, fiscalYear: fundamentals.fiscal_year,
            fiscalQuarter: fundamentals.fiscal_quarter,
          } : null,
          technical: {
            rsi14: factors.rsi_14 ?? null, macdDif: factors.macd_dif ?? null,
            ma20: factors.ma_20 ?? null, tradeDate: factors._tradeDate ?? null,
          },
          momentum: { m5d: momentum5d, m20d: momentum20d },
          riskAlerts: riskAlerts.map(a => ({ time: a.alert_time, type: a.alert_type, severity: a.severity, message: a.message })),
          poolInfo: stockPoolInfo ? { sector: stockPoolInfo.sector, poolType: stockPoolInfo.pool_type, status: stockPoolInfo.status } : null,
          decisions: decisions.map(d => ({ action: d.action, status: d.status, price: d.reference_price, thesis: d.thesis_summary })),
        };

        // 补充实时行情数据（腾讯财经 API：PB/PS/市值/换手率等）
        try {
          const rt = await fetchRealtimeData(this.ticker);
          if (rt) {
            const inst = this.context.data.instrumentData;
            if (rt.latest_price != null) inst.latestPrice = rt.latest_price;
            if (rt.change_percent != null) inst.changePercent = rt.change_percent;
            if (!inst.valuation) inst.valuation = {};
            if (rt.pe_ttm != null) inst.valuation.pe = rt.pe_ttm;
            if (rt.pb != null) inst.valuation.pb = rt.pb;
            if (rt.ps_ttm != null) inst.valuation.ps = rt.ps_ttm;
            if (rt.market_cap != null) inst.valuation.marketCap = rt.market_cap;
            if (!inst.technical) inst.technical = {};
            if (rt.turnover_rate != null) inst.technical.turnoverRate = rt.turnover_rate;
            this.addLog("get_stock_data", `腾讯实时数据补充: PE=${rt.pe_ttm}, PB=${rt.pb}, PS=${rt.ps_ttm}, 市值=${rt.market_cap}亿`);
          }
        } catch (err) {
          console.warn(`[SubAgent ${this.ticker}] 实时数据补充失败:`, err.message);
        }

        // 获取行业配置数据（同业标的和对标公司）
        const sectorConfig = dataService.getSectorConfig(this.ticker);
        if (sectorConfig) {
          this.context.data.instrumentData.sectorConfig = sectorConfig;
          this.addLog("get_sector_config", `获取到行业配置: ${sectorConfig.sectorName}`);
        }
        
        // 补充缺失数据：基于已有数据进行推算
        this.supplementMissingData();
        
        this.addLog("get_stock_data", `获取到 ${this.ticker} 的全景数据`);
      } finally { dataService.close(); }
    } catch (e) {
      this.addLog("get_stock_data", `数据获取失败：${e.message}`);
    }

    // 步骤4: 获取新闻（数据库 + 4 个中文 content_ready 源）
    try {
      const dataService = new MarketDataService();
      let allNews = [];
      let events = [];
      try {
        const dbNews = dataService.getNews(this.ticker, 5);
        events = dataService.getMarketEvents(this.ticker, 3);
        allNews = dbNews || [];
      } finally { dataService.close(); }

      // 4b. 抓取中文财经新闻
      try {
        const cnService = new ChineseNewsService();
        const allChineseNews = await cnService.fetchAll(5);

        // 4b-1. 先对所有新闻补充正文（这样所有源都有机会被补充）
        if (allChineseNews.length > 0) {
          try {
            await cnService.enrichWithFirecrawl(allChineseNews, { maxTotalScrape: 10 });
          } catch (fcErr) {
            console.warn(`[SubAgent ${this.ticker}] Firecrawl 正文补充失败:`, fcErr.message);
          }
        }

        const stockName = STOCK_NAME_MAP[this.ticker] || "";

        // 4b-2. 再尝试过滤与当前股票直接相关的新闻
        let chineseNews = cnService.filterByStock(allChineseNews, this.ticker, stockName);

        // 如果没有直接相关的，保留前 3 条行业热点作为市场参考
        // 因为中文财经首页反映的是当前市场热点，对行业对比分析非常有价值
        if (chineseNews.length === 0 && allChineseNews.length > 0) {
          chineseNews = allChineseNews.slice(0, 3).map(n => ({ ...n, isMarketReference: true }));
        }

        // 强制打印日志，确认中文新闻抓取状态
        console.log(`[SubAgent ${this.ticker}] 中文源共抓取 ${allChineseNews.length} 条，直接相关 ${cnService.filterByStock(allChineseNews, this.ticker, stockName).length} 条，最终保留 ${chineseNews.length} 条`);
        if (chineseNews.length > 0) {
          this.addLog("get_chinese_news", `从 4 个中文源获取到 ${chineseNews.length} 条中文新闻`);
          console.log(`[SubAgent ${this.ticker}] 中文新闻:`, chineseNews.map(n => `[${n.source_name}] ${n.title.substring(0, 40)}`));
        }

        // 4c. Tavily 多维度搜索：目标价/评级、业绩纪要、最新动态、海外观点
        let tavilyNews = [];
        try {
          const codeOnly = this.ticker.replace(/\.(SZ|SH|BJ|HK)$/i, "");
          tavilyNews = await cnService.fetchTavilyMultiDimension(stockName || codeOnly, this.ticker, 3);
          console.log(`[SubAgent ${this.ticker}] Tavily 多维度搜索返回 ${tavilyNews.length} 条结果`);
          if (tavilyNews.length > 0) {
            // 按维度统计
            const dimStats = {};
            for (const n of tavilyNews) {
              const dim = n.dimension_label || '未知';
              dimStats[dim] = (dimStats[dim] || 0) + 1;
            }
            console.log(`[SubAgent ${this.ticker}] Tavily 维度分布:`, dimStats);
            this.addLog("get_tavily_news", `Tavily 多维度搜索获取 ${tavilyNews.length} 条（目标价/纪要/新闻/海外观点）`);
          }
        } catch (tavilyErr) {
          console.warn(`[SubAgent ${this.ticker}] Tavily 搜索失败:`, tavilyErr.message);
        }

        // 4d. CNINFO 巨潮资讯：查询 A 股官方公告
        let cninfoNews = [];
        try {
          const codeOnly = this.ticker.replace(/\.(SZ|SH|BJ|HK)$/i, "");
          cninfoNews = await cnService.fetchCninfoAnnouncements(codeOnly, 5);
          console.log(`[SubAgent ${this.ticker}] CNINFO 公告查询 "${codeOnly}" 返回 ${cninfoNews.length} 条结果`);
          if (cninfoNews.length > 0) {
            this.addLog("get_cninfo_news", `CNINFO 巨潮资讯获取到 ${cninfoNews.length} 条官方公告`);
          }
        } catch (cninfoErr) {
          console.warn(`[SubAgent ${this.ticker}] CNINFO 查询失败:`, cninfoErr.message);
        }

        // 4e. 东方财富增强数据：资金流向 + 龙虎榜 + 多季度财务历史 + 券商研报
        // 小白讲解：这一步从东方财富拿到"聪明钱动向"和"业绩趋势"和"卖方共识"，是判断市场情绪和基本面拐点的关键
        try {
          const enhancedData = await eastmoneyDataService.getAllEnhancedData(this.ticker);
          this.context.data.eastmoneyData = enhancedData;
          const fundFlowCount = enhancedData.fundFlow?.length || 0;
          const dragonTigerCount = enhancedData.dragonTiger?.length || 0;
          const finHistoryCount = enhancedData.financialHistory?.length || 0;
          const researchCount = enhancedData.researchReports?.length || 0;
          this.addLog("get_eastmoney_data", `东方财富增强数据：资金流向${fundFlowCount}天/龙虎榜${dragonTigerCount}条/财务历史${finHistoryCount}期/券商研报${researchCount}篇`);
          console.log(`[SubAgent ${this.ticker}] 东方财富增强数据获取完成`);
        } catch (emErr) {
          console.warn(`[SubAgent ${this.ticker}] 东方财富增强数据获取失败:`, emErr.message);
          this.context.data.eastmoneyData = null;
        }

        // 4f. 华尔街数据：美股分析师评级 + 目标价 + 新闻
        // 小白讲解：如果股票有海外对标或属于美股，这一步从Finnhub/Morningstar/Benzinga拿到华尔街分析师的评级和目标价
        try {
          const sectorConfig = this.context.data.instrumentData?.sectorConfig || {};
          const usBenchmarks = sectorConfig.usBenchmarks || [];
          const allWallstreetData = {};
          let wsCount = 0;

          if (usBenchmarks.length > 0) {
            for (const symbol of usBenchmarks.slice(0, 3)) {
              const wsData = await wallstreetDataService.getAllWallstreetData(symbol);
              if (Object.keys(wsData.ratings).length > 0) {
                allWallstreetData[symbol] = wsData;
                wsCount++;
              }
            }
          }

          if (wsCount > 0) {
            this.context.data.wallstreetData = allWallstreetData;
            this.addLog("get_wallstreet_data", `华尔街数据：${wsCount}个海外对标获取到评级数据`);
            console.log(`[SubAgent ${this.ticker}] 华尔街数据获取完成: ${wsCount}个海外对标`);
          }
        } catch (wsErr) {
          console.warn(`[SubAgent ${this.ticker}] 华尔街数据获取失败:`, wsErr.message);
          this.context.data.wallstreetData = null;
        }

        // 合并并去重（优先 CNINFO 官方公告 + Tavily 定向搜索，再中文源，再数据库）
        const seenUrls = new Set();
        const merged = [];
        for (const item of [...cninfoNews, ...tavilyNews, ...chineseNews, ...allNews]) {
          const url = item.url || item.link || "";
          if (url && seenUrls.has(url)) continue;
          if (url) seenUrls.add(url);
          merged.push(item);
          if (merged.length >= 12) break;
        }
        allNews = merged;
      } catch (err) {
        // fail-soft：中文源抓取失败不影响主流程
        console.warn(`[SubAgent ${this.ticker}] 中文新闻抓取失败:`, err.message);
      }

      this.context.data.news = allNews;
      this.context.data.events = events;
      this.addLog("get_news", `获取到 ${allNews.length} 条新闻（含中文源）`);
    } catch (e) {
      this.addLog("get_news", `新闻获取失败：${e.message}`);
    }

    // 步骤5: AI单标深度分析
    try {
      const analysis = await this.generateSingleStockAnalysis();
      this.context.data.llmAnalysis = { rawAnalysis: analysis };
      this.addLog("analyze_with_llm", `单标深度分析完成`);
    } catch (e) {
      this.addLog("analyze_with_llm", `分析失败：${e.message}`);
      return { success: false, error: e.message, ticker: this.ticker };
    }

    return {
      success: true,
      ticker: this.ticker,
      stockEntity: this.context.data.stockEntity,
      instrumentData: this.context.data.instrumentData,
      eastmoneyData: this.context.data.eastmoneyData || null,
      wallstreetData: this.context.data.wallstreetData || null,
      analysis: this.context.data.llmAnalysis?.rawAnalysis || "",
      executionHistory: this.executionHistory,
    };
  }

  /**
   * 补充缺失数据
   * 
   * 功能：基于已有数据推算缺失的估值指标
   * 
   * 小白讲解：
   *   数据库里有些数据缺失了（比如市值、PB、PS），
   *   这个方法就像一个"数据修补匠"，用已有数据算出缺失的值。
   *   比如知道股价和EPS，就能估算市值。
   */
  supplementMissingData() {
    const data = this.context.data.instrumentData;
    if (!data) return;
    
    const valuation = data.valuation || {};
    const fundamentals = data.fundamentals || {};
    const latestPrice = data.latestPrice;
    
    // 1. 基于EPS和PE反推市值（如果缺失）
    if (!valuation.marketCap && latestPrice && fundamentals.epsBasic && valuation.pe) {
      // 市值 = 股价 × 总股本，但需要总股本
      // 暂时用 EPS × PE × 1亿 作为粗略估算
      valuation.marketCap = fundamentals.epsBasic * valuation.pe * 100000000;
      valuation._marketCapDerived = true; // 标记为推算值
    }
    
    // 2. 基于营收和PS反推市值（如果缺失）
    if (!valuation.marketCap && latestPrice && fundamentals.revenue && valuation.ps) {
      valuation.marketCap = fundamentals.revenue * valuation.ps;
      valuation._marketCapDerived = true;
    }
    
    // 3. 基于股东权益和PB反推市值（如果缺失）
    if (!valuation.marketCap && latestPrice && fundamentals.equity && valuation.pb) {
      valuation.marketCap = fundamentals.equity * valuation.pb;
      valuation._marketCapDerived = true;
    }
    
    // 4. 基于市值和股东权益计算PB（如果缺失）
    if (!valuation.pb && valuation.marketCap && fundamentals.equity && fundamentals.equity > 0) {
      valuation.pb = valuation.marketCap / fundamentals.equity;
      valuation._pbDerived = true;
    }
    
    // 5. 基于市值和营收计算PS（如果缺失）
    if (!valuation.ps && valuation.marketCap && fundamentals.revenue && fundamentals.revenue > 0) {
      valuation.ps = valuation.marketCap / fundamentals.revenue;
      valuation._psDerived = true;
    }
    
    // 6. 基于市值和净利润计算PE（如果缺失）
    if (!valuation.pe && valuation.marketCap && fundamentals.netIncome && fundamentals.netIncome > 0) {
      valuation.pe = valuation.marketCap / fundamentals.netIncome;
      valuation._peDerived = true;
    }
    
    // 7. 记录数据补充日志
    const derivedFields = [];
    if (valuation._marketCapDerived) derivedFields.push("市值");
    if (valuation._pbDerived) derivedFields.push("PB");
    if (valuation._psDerived) derivedFields.push("PS");
    if (valuation._peDerived) derivedFields.push("PE");
    
    if (derivedFields.length > 0) {
      this.addLog("supplement_data", `补充了 ${derivedFields.join("、")} 数据`);
    }
  }

  async generateSingleStockAnalysis() {
    const stock = this.context.data.stockEntity || {};
    const data = this.context.data.instrumentData || {};
    const news = this.context.data.news || [];
    const memoryContextText = this.context.data.memoryContextText || "无历史记忆";
    const userQuery = this.context.userQuery || "";

    const now = new Date();
    const currentDate = now.toLocaleDateString("zh-CN");
    const dataDate = data.latestDate || currentDate;

    const systemPrompt = `你是顶级卖方分析师+买方基金经理，请对单只股票进行深度投资分析。输出中文。

【核心方法论：不要描述数据，要分析逻辑】
描述 = 复述数据（"营收XX亿，增长XX%"）
分析 = 解释数据背后的逻辑（"营收增长主要来自XX产品放量，反映XX趋势，意味着XX"）

你必须按以下框架推理，而不是填模板：

【分析框架】
一、市场共识是什么？（关键！）
- 当前股价反映了什么预期？（用估值历史分位倒推：分位>80%=高预期，<20%=低预期）
- 市场主流观点是什么？（从新闻/研报/评级信息提取，如果有目标价数据要引用）
- 如果缺少卖方一致预期数据，明确说"缺少卖方一致预期数据"，基于公开信息推断市场共识

二、我们的判断 vs 市场共识
- 哪些是高确定性的？（基本面硬数据支撑的判断）
- 哪些可能与市场共识有偏差？为什么会有偏差？
- 预期差的方向（偏多/偏空）和幅度

三、投资逻辑（我们赌什么）
- 核心赌点（1-2个，如"赌AI算力capex超预期"、"赌国产替代加速"）
- 这个赌点当前price in了吗？（用估值分位+市场情绪判断）
- 如果赌对了，上行空间多大？如果赌错了，下行风险多大？

四、多情景分析
- 乐观情景（概率XX%）：目标价XX，触发条件
- 中性情景（概率XX%）：目标价XX，触发条件
- 悲观情景（概率XX%）：目标价XX，触发条件
- 注意：目标价要参考市场一致预期（如果Tavily搜到了分析师目标价，必须引用并对比）

五、择时判断
- 当前是不是好的买点？（结合RSI、MACD、均线、估值分位综合判断）
- 如果不是，什么位置/什么信号出现时是更好的买点？
- 短期（1-4周）/中期（1-6月）/长期（6月+）视角分别怎么看

六、风险提示
- 2-3个核心风险，每个风险说明触发条件和影响幅度

七、操作建议
- 买入/持有/卖出/观望
- 建议仓位（如5-10%）
- 加仓触发条件（2-3个具体、可跟踪的条件）
- 减仓/止损触发条件（2-3个）
- 关键观察指标（需要持续跟踪的1-2个核心指标）

【数据处理规则】
1. 对于缺失的财务数据必须明确标注缺失，禁止估算或补造具体数值
2. 异常数据（如PE>200倍、PE为负）需标注"⚠️"并说明原因
3. 如果Tavily搜索返回了分析师目标价/评级，必须引用并在"市场共识"部分对比
4. 绝对禁止脱离市场预期凭空给出目标价——必须基于市场一致预期+预期差分析
5. 【东方财富数据使用规则】资金流向+龙虎榜+财务趋势+券商研报是核心硬证据，必须在分析中引用：
   - 资金流向反映"聪明钱"动向：主力净流入连续为正=机构建仓，连续为负=机构出货
   - 龙虎榜机构席位净买入=机构看好，净卖出=机构撤退
   - 多季度财务趋势是判断"加速增长"还是"减速增长"的硬证据，必须引用最新一期和上期的同比对比
   - 券商研报反映"卖方共识"：买入/增持比例高=市场看好，评级集中上调=预期改善
   - 一致预期EPS/PE是估值锚点，必须与当前估值对比，判断高估/低估
   - 资金面与基本面背离时（如业绩加速但资金流出），必须明确提示背离信号`;

    // 准备新闻信息，重点突出Tavily多维度搜索结果（目标价/评级/纪要）
    const tavilyTargetPriceNews = news.filter(n => n.dimension === 'target_price_rating');
    const tavilyEarningsNews = news.filter(n => n.dimension === 'earnings_guidance');
    const tavilyOverseasNews = news.filter(n => n.dimension === 'overseas_view');
    const otherNews = news.filter(n => !n.dimension);

    let newsSection = `## 近期新闻（共 ${news.length} 条）\n`;

    if (tavilyTargetPriceNews.length > 0) {
      newsSection += `\n### 🎯 分析师目标价与评级（Tavily搜索，高价值）\n`;
      for (const n of tavilyTargetPriceNews) {
        newsSection += `${n.title}\n${(n.body || '').substring(0, 500)}\n\n`;
      }
    }

    if (tavilyEarningsNews.length > 0) {
      newsSection += `\n### 📋 业绩纪要与指引（Tavily搜索）\n`;
      for (const n of tavilyEarningsNews) {
        newsSection += `${n.title}\n${(n.body || '').substring(0, 500)}\n\n`;
      }
    }

    if (tavilyOverseasNews.length > 0) {
      newsSection += `\n### 🌍 海外分析师观点（Tavily搜索）\n`;
      for (const n of tavilyOverseasNews) {
        newsSection += `${n.title}\n${(n.body || '').substring(0, 500)}\n\n`;
      }
    }

    if (otherNews.length > 0) {
      newsSection += `\n### 📰 其他近期新闻\n`;
      newsSection += otherNews.slice(0, 5).map((n, i) => `${i + 1}. [${n.published_at?.substring(0, 10)}] ${n.source_name}: ${n.title}`).join("\n");
    }

    let userPrompt = `## 用户问题
${userQuery}

## 股票信息
名称：${stock.name || data.name || this.ticker}
代码：${stock.tsCode || this.ticker}
行业：${stock.sector || data.sector || "未知"}
${data.sectorConfig ? `所属行业：${data.sectorConfig.sectorName}` : ""}
${data.sectorConfig?.ahUniverse?.length ? `同业标的：${data.sectorConfig.ahUniverse.join("、")}` : ""}
${data.sectorConfig?.usBenchmarks?.length ? `海外对标：${data.sectorConfig.usBenchmarks.join("、")}` : ""}

## 最新行情
最新价：${data.latestPrice || "无数据"}
数据日期：${data.latestDate || "未知"}
5日涨跌：${data.momentum?.m5d != null ? data.momentum.m5d.toFixed(2) + "%" : "无数据"}
20日涨跌：${data.momentum?.m20d != null ? data.momentum.m20d.toFixed(2) + "%" : "无数据"}

## 估值数据
${data.valuation ? `PE(TTM)：${data.valuation.pe ?? "N/A"}
PB：${data.valuation.pb ?? "N/A"}
PS(TTM)：${data.valuation.ps ?? "N/A"}
EV/EBITDA：${data.valuation.evEbitda ?? "N/A"}
市值：${data.valuation.marketCap ?? "N/A"}
历史分位数：${data.valuation.historicalPercentile ?? "N/A"}%（当前）/ ${data.valuation.historicalPercentile1y ?? "N/A"}%（1年）/ ${data.valuation.historicalPercentile3y ?? "N/A"}%（3年）/ ${data.valuation.historicalPercentile5y ?? "N/A"}%（5年）
同业分位数：${data.valuation.peerPercentile ?? "N/A"}%
券商目标价：${data.valuation.brokerTargetPrice ?? "N/A"}` : "无估值数据"}

## 基本面数据
${data.fundamentals ? `报告期：${data.fundamentals.period ?? "N/A"}（${data.fundamentals.fiscalYear ?? ""}年${data.fundamentals.fiscalQuarter ?? ""}季度）
营收：${data.fundamentals.revenue ?? "N/A"}
毛利润：${data.fundamentals.grossProfit ?? "N/A"}
营业利润：${data.fundamentals.operatingIncome ?? "N/A"}
净利润：${data.fundamentals.netIncome ?? "N/A"}
EPS（基本）：${data.fundamentals.epsBasic ?? "N/A"}
经营现金流：${data.fundamentals.operatingCashFlow ?? "N/A"}
资本支出：${data.fundamentals.capex ?? "N/A"}
自由现金流：${data.fundamentals.freeCashFlow ?? "N/A"}
现金及等价物：${data.fundamentals.cash ?? "N/A"}
总负债：${data.fundamentals.totalDebt ?? "N/A"}
股东权益：${data.fundamentals.equity ?? "N/A"}
毛利率：${data.fundamentals.grossMargin != null ? (data.fundamentals.grossMargin * 100).toFixed(2) + "%" : "N/A"}
营业利润率：${data.fundamentals.operatingMargin != null ? (data.fundamentals.operatingMargin * 100).toFixed(2) + "%" : "N/A"}
净利率：${data.fundamentals.netMargin != null ? (data.fundamentals.netMargin * 100).toFixed(2) + "%" : "N/A"}
ROE：${data.fundamentals.roe != null ? (data.fundamentals.roe * 100).toFixed(2) + "%" : "N/A"}
ROIC：${data.fundamentals.roic != null ? (data.fundamentals.roic * 100).toFixed(2) + "%" : "N/A"}` : "无基本面数据"}

## 技术面数据
RSI(14)：${data.technical?.rsi14 ?? "无数据"}
MACD DIF：${data.technical?.macdDif ?? "无数据"}
MA20：${data.technical?.ma20 ?? "无数据"}

## 东方财富增强数据（资金动向+财务趋势+券商研报，高价值）
${this.context.data.eastmoneyData ? eastmoneyDataService.formatForLLM(this.context.data.eastmoneyData) : "（获取失败或无数据）"}

## 华尔街数据（海外对标分析师评级+目标价，高价值）
${this.context.data.wallstreetData ? this.formatWallstreetDataForLLM(this.context.data.wallstreetData) : "（无海外对标或获取失败）"}

${newsSection}

## 历史研究记忆
${memoryContextText}`;

    if (!isModelAvailable()) {
      return `【${stock.name || this.ticker}单标分析报告】\n\n由于AI模型不可用，仅提供数据摘要：\n- 最新价：${data.latestPrice || "-"}\n- PE：${data.valuation?.pe || "-"}\n- PB：${data.valuation?.pb || "-"}\n- 营收：${data.fundamentals?.revenue || "-"}\n- 净利：${data.fundamentals?.netIncome || "-"}`;
    }

    const response = await createChatCompletion([
      { role: "system", content: systemPrompt },
      { role: "user", content: userPrompt },
    ], { maxTokens: 16000 });

    let content = response?.content || "分析失败";
    // 修复Unicode换行符问题
    content = content.replace(/_x000A_/g, "\n");
    return content;
  }

  /**
   * 格式化华尔街数据为LLM可读文本
   *
   * 参数：
   *   wallstreetData: getAllWallstreetData返回的对象，key为美股代码
   *
   * 返回：
   *   格式化的文本字符串
   */
  formatWallstreetDataForLLM(wallstreetData) {
    if (!wallstreetData) return "无华尔街数据";

    let text = "";
    for (const [symbol, data] of Object.entries(wallstreetData)) {
      text += `\n### 🇺🇸 ${symbol} 华尔街分析师评级\n`;
      text += wallstreetDataService.formatForLLM(data);
    }

    return text || "无华尔街数据";
  }
}

function buildSignalPlanInput(context, ticker) {
  const query = String(context.userQuery || "");
  const signals = [];
  const addSignal = (signalId, name, category, importance, note) => {
    signals.push({
      signal_id: signalId,
      name,
      category,
      indicator_kind: "leading",
      current_state: "observing",
      importance,
      note,
      thresholds: {
        trigger: { requirement: "至少一条可追溯正式或高质量独立证据" },
        double_confirm_cond: { requirement: "第二条独立来源确认" },
        invalidate: { requirement: "正式披露否定、计划取消或关键节点超期" },
        frequency: "每周",
        expire_after: "90天",
      },
    });
  };
  if (/认证|送样|客户/.test(query)) {
    addSignal("customer_certification", "客户认证进度", "产品/认证", 0.95, "区分送样、测试、认证、供应商代码和批量订单");
  }
  if (/工厂|产线|产能|投产|爬坡/.test(query)) {
    addSignal("factory_ramp", "新工厂投产与爬坡", "工厂/产能", 0.9, "区分开业、设备进场、试产、良率、利用率和利润贡献");
  }
  if (/出货|订单|收入|节奏/.test(query)) {
    addSignal("shipment_cadence", "订单与出货节奏", "订单/出货", 0.95, "区分订单、排产、出货和收入确认");
  }
  if (signals.length === 0) {
    addSignal("formal_disclosure_update", "正式披露进展", "公司披露", 0.8, "仅在正式公告或公司 IR 明确披露后升级状态");
    addSignal("operating_leading_indicator", "经营领先指标", "经营指标", 0.75, "需在首次运行后按公司业务补齐具体指标");
  }
  return {
    ticker,
    name: context.data.stockEntity?.name || "",
    raw_signals: signals,
    axes: ["product", "factory", "upstream"],
    allow_network: false,
  };
}

const THEME_CANDIDATE_SEEDS = Object.freeze({
  supernode: [
    {
      ticker: "002396.SZ", name: "星网锐捷", industry: "通信设备",
      sub_sector: "企业网络与超节点映射", business_purity: 0.45,
      revenue_sensitivity: 0.5, tags: ["AI算力", "超节点", "网络设备"],
      note: "通过锐捷网络形成网络设备与算力基础设施映射；持股价值需单独复算",
    },
    {
      ticker: "301165.SZ", name: "锐捷网络", industry: "通信设备",
      sub_sector: "交换机与数据中心网络", business_purity: 0.8,
      revenue_sensitivity: 0.75, tags: ["AI算力", "超节点", "交换机"],
      note: "主题业务暴露较直接，仍需用正式披露核验 AI 相关收入占比",
    },
    {
      ticker: "000938.SZ", name: "紫光股份", industry: "计算机设备",
      sub_sector: "ICT基础设施与交换机", business_purity: 0.55,
      revenue_sensitivity: 0.55, tags: ["AI算力", "超节点", "ICT基础设施"],
      note: "业务覆盖面较广，主题纯度低于单一网络设备公司",
    },
    {
      ticker: "688629.SH", name: "华丰科技", industry: "电子元件",
      sub_sector: "高速连接器", business_purity: 0.5,
      revenue_sensitivity: 0.7, tags: ["AI算力", "超节点", "高速互连"],
      note: "位于高速互连环节，收入兑现依赖认证、订单与产能进度",
    },
  ],
});

function themeSeedCandidates(query) {
  const text = String(query || "");
  if (/超节点|AI\s*算力|算力基础设施/i.test(text)) {
    return THEME_CANDIDATE_SEEDS.supernode.map((item) => ({ ...item }));
  }
  return [];
}

function buildCausalExplainerInput(context) {
  const question = String(context.userQuery || "");
  const theme = String(context.data.routingEnvelope?.topic || (/DCI|数通/i.test(question) ? "DCI 数通光模块" : "产业主题"));
  const labels = {
    1: "终端需求是否真实",
    2: "需求位于产业链哪个节点",
    3: "A股是否存在纯正资产映射",
    4: "市场注意力是否被其他叙事占用",
    5: "订单如何传导到收入和利润",
    6: "传导需要多长时间",
    7: "哪些催化会改变市场定价",
    8: "哪些证据会证伪当前解释",
  };
  const conclusions = {
    1: "需要用云厂商资本开支、设备采购或公司正式披露确认终端需求，单条新闻不足以定论。",
    2: "先区分光芯片、光器件、模块、交换机与系统集成环节，需求不能跨节点直接映射到利润。",
    3: "A股映射必须同时检查业务纯度、收入敏感度和可交易性，概念相关不等于利润相关。",
    4: "估值与股价还受同期主线、拥挤度、业绩预期和资金偏好影响，产业需求不是唯一解释变量。",
    5: "需求需依次经过认证、订单、排产、出货和收入确认，任一环节缺证都不能跳步。",
    6: "兑现时滞取决于认证周期、交付节奏和收入确认口径，当前证据不足时只给观察区间，不给伪精确日期。",
    7: "可验证催化包括正式认证、批量订单、产能爬坡和财务报表中的收入/利润兑现。",
    8: "若资本开支、订单、出货或毛利率没有同向验证，或正式披露否定需求映射，则当前解释失效。",
  };
  const causalNodes = {};
  for (let step = 1; step <= 8; step += 1) {
    causalNodes[String(step)] = {
      title: labels[step],
      conclusion: conclusions[step],
      detail: "该节点为研究框架结论；进入事实判断前必须补充可追溯证据。",
      evidences: [],
      confidence: 0.35,
      alternative_findings: step === 4
        ? ["基本面未变但估值压缩", "需求存在但A股资产映射不纯", "订单兑现时间晚于市场窗口"]
        : [],
    };
  }
  const edges = Array.from({ length: 7 }, (_, index) => ({
    from_step: index + 1,
    to_step: index + 2,
    edge_kind: "inferred",
    explanation: "待一手材料补证的研究推断，不作为已确认事实。",
    evidence_id: "",
  }));
  return {
    theme,
    question,
    causal_nodes_input: causalNodes,
    causal_edges_input: edges,
    alternatives_input: [
      {
        title: "估值压缩解释",
        plausibility: 0.5,
        how_to_falsify: "比较当前估值分位、盈利预测变化和行业相对收益。",
        current_evidence_against: "当前未完成估值与盈利预测的同口径核验。",
      },
      {
        title: "资产映射解释",
        plausibility: 0.6,
        how_to_falsify: "核验相关公司的主题收入占比、订单和毛利贡献。",
        current_evidence_against: "当前缺少正式披露的主题收入拆分。",
      },
    ],
    allow_network: false,
  };
}

function buildClaimCorrectionInput(context, ticker) {
  const envelope = context.data.routingEnvelope || {};
  const target = envelope.correctionTarget || {};
  const fieldAliases = {
    "市值": "market_cap",
    "收入": "revenue",
    "营收": "revenue",
    "利润": "net_income",
    "净利润": "net_income",
    "EPS": "eps",
    "PE": "pe_ttm",
    "PB": "pb",
  };
  const claimId = fieldAliases[target.field] || String(target.field || "").toLowerCase();
  if (!claimId || claimId === "unknown") {
    throw new TypeError("没有识别出需要纠正的指标，请明确说明市值、营收、净利润、EPS、PE 或 PB");
  }

  const instrument = context.data.instrumentData || {};
  const authoritativeByField = {
    market_cap: instrument.valuation?.marketCap,
    revenue: instrument.fundamentals?.revenue,
    net_income: instrument.fundamentals?.netIncome,
    eps: instrument.fundamentals?.eps,
    pe_ttm: instrument.valuation?.pe,
    pb: instrument.valuation?.pb,
  };
  let authoritativeValue = Number(authoritativeByField[claimId]);
  if (!Number.isFinite(authoritativeValue)) {
    throw new TypeError(`重新取数后仍缺少 ${claimId} 的可验证数值，纠错保持 disputed，不覆盖旧事实`);
  }

  const previousFacts = [
    ...(Array.isArray(envelope.confirmedFacts) ? envelope.confirmedFacts : []),
    ...(Array.isArray(context.sessionState?.confirmedFacts) ? context.sessionState.confirmedFacts : []),
  ];
  const prior = previousFacts.find((fact) => {
    const normalized = fieldAliases[fact?.field] || String(fact?.field || "").toLowerCase();
    return normalized === claimId && (!fact?.ticker || fact.ticker === ticker);
  });
  let oldValue = Number(prior?.value ?? target.previousValue);
  const priorUnit = String(prior?.unit || "");
  const unitByField = {
    market_cap: "人民币元",
    revenue: "人民币元",
    net_income: "人民币元",
    eps: "元/股",
    pe_ttm: "倍",
    pb: "倍",
  };
  if (claimId === "market_cap" && /亿元/.test(priorUnit || String(context.userQuery || ""))) {
    oldValue *= 100_000_000;
  }
  if (!Number.isFinite(oldValue)) {
    throw new TypeError("会话中没有找到被争议指标的旧值，无法生成可审计的 before/after diff");
  }

  const evidence = [...(context.data.evidenceCatalog || [])]
    .reverse()
    .find((item) => item.tool_id === "get_stock_data");
  if (!evidence?.evidence_id) {
    throw new TypeError("重新取数没有形成证据快照，纠错保持 disputed");
  }
  const source = instrument.source_url
    || instrument.source
    || `本地行情与财务快照（${instrument.fetched_at || instrument.latestDate || "时点未标注"}）`;

  const hasClaimedValue = target.claimedValue !== null
    && target.claimedValue !== undefined
    && String(target.claimedValue).trim() !== "";
  const claimedValue = hasClaimedValue ? Number(target.claimedValue) : Number.NaN;
  if (hasClaimedValue && Number.isFinite(claimedValue)) {
    const normalizedClaimed = claimId === "market_cap" && /亿/.test(String(context.userQuery || ""))
      ? claimedValue * 100_000_000
      : claimedValue;
    const tolerance = Math.max(1, Math.abs(authoritativeValue) * 0.02);
    if (Math.abs(normalizedClaimed - authoritativeValue) > tolerance) {
      throw new TypeError(
        `用户声称值与重新取得的权威快照仍冲突（用户 ${normalizedClaimed}，快照 ${authoritativeValue}），`
        + "纠错保持 disputed，不强行覆盖",
      );
    }
  }

  const claims = [{
    claim_id: claimId,
    claim_type: "fact",
    metric: claimId,
    value: oldValue,
    unit: unitByField[claimId] || "",
    evidence_id: prior?.evidenceId || prior?.evidence_id || "previous_session_fact",
    upstream_claim_ids: [],
  }];
  if (claimId === "market_cap") {
    const netIncome = Number(instrument.fundamentals?.netIncome);
    if (Number.isFinite(netIncome) && netIncome > 0) {
      claims.push(
        {
          claim_id: "net_income",
          claim_type: "fact",
          metric: "net_income",
          value: netIncome,
          unit: "人民币元",
          evidence_id: evidence.evidence_id,
          upstream_claim_ids: [],
        },
        {
          claim_id: "pe_ttm_recomputed",
          claim_type: "output",
          metric: "pe_ttm",
          value: oldValue / netIncome,
          unit: "倍",
          upstream_claim_ids: ["market_cap", "net_income"],
          formula: "market_cap / net_income",
        },
      );
    }
  }
  return {
    entity_key: ticker,
    allow_network: false,
    claims,
    correction: {
      claim_id: claimId,
      new_value: authoritativeValue,
      source: String(source),
      evidence_id: evidence.evidence_id,
      user_claimed_value: hasClaimedValue && Number.isFinite(claimedValue) ? claimedValue : null,
    },
  };
}

export function buildGovernedWorkflowInput(taskType, context) {
  const explicitInput = context.currentInput?.workflowInput || context.input?.workflowInput;
  if (explicitInput && typeof explicitInput === "object" && !Array.isArray(explicitInput)) {
    return { ...explicitInput };
  }
  const routedEntities = context.data.routingEnvelope?.entities || context.data.entities || [];
  const routedTickers = routedEntities.map((item) => item?.ticker).filter(Boolean);
  const tickers = context.data.multiStockTickers?.length
    ? context.data.multiStockTickers
    : (routedTickers.length ? routedTickers : resolveMultipleTickers(context.userQuery || ""));
  const ticker = String(
    context.data.currentTicker || context.data.stockEntity?.tsCode || tickers[0] || ""
  ).trim().toUpperCase();

  switch (taskType) {
    case "operating_driver_valuation":
      if (!ticker) throw new TypeError("经营驱动估值缺少股票代码");
      return {
        ticker,
        model_template: ticker === "688041.SH"
          ? "hygon_info_2026_2028"
          : "generic_semiconductor_3yr",
        allow_network: false,
      };
    case "pair_switch_decision":
      if (tickers.length < 2) throw new TypeError("双标的换仓需要两个股票代码");
      return {
        from_ticker: tickers[0],
        to_ticker: tickers[1],
        from_name: routedEntities[0]?.name || "",
        to_name: routedEntities[1]?.name || "",
        allow_network: false,
      };
    case "company_signal_plan":
      if (!ticker) throw new TypeError("公司信号计划缺少股票代码");
      return buildSignalPlanInput(context, ticker);
    case "theme_expectation_gap":
      {
        const seeded = routedEntities.length > 0
          ? routedEntities.map((entity) => ({
              ticker: entity.ticker,
              name: entity.name || entity.ticker,
              inclusion_reason: "用户在当前任务中明确指定",
              business_purity: 0.2,
              revenue_sensitivity: 0.2,
              tags: ["用户指定"],
            }))
          : themeSeedCandidates(context.data.routingEnvelope?.topic || context.userQuery);
        if (seeded.length === 0) {
        throw new TypeError("主题筛选尚未获得候选全集，不能用空候选生成排名");
        }
        return {
          theme_name: String(context.data.routingEnvelope?.topic || context.userQuery || "主题研究"),
          raw_candidates: seeded,
          keyword_hint_list: ["AI算力", "超节点", "高速互连"],
          allow_network: false,
        };
      }
    case "industry_causal_explainer":
      return buildCausalExplainerInput(context);
    case "claim_correction":
      if (!ticker) throw new TypeError("事实纠错缺少股票代码");
      return buildClaimCorrectionInput(context, ticker);
    default:
      throw new TypeError(`工作流 ${taskType} 尚未定义自然语言输入适配器`);
  }
}

export const AGENT_TOOLS = {
  resolve_entity: {
    toolId: "resolve_entity",
    name: "解析金融实体",
    description: "识别股票代码、名称、行业等信息，支持多标解析",
    inputSchema: { type: "object", properties: { entity: { type: "string" } } },
    execute: async (context) => {
      const entity = context.currentInput?.entity || context.userQuery;
      if (!entity) return { success: false, message: "缺少实体参数" };
      
      // 尝试解析多个股票
      const tickers = resolveMultipleTickers(entity);
      
      if (tickers.length === 0) {
        // 没有匹配到任何股票，尝试单标解析
        const ticker = resolveTicker(entity);
        const dataService = new MarketDataService();
        try {
          const stockInfo = dataService.resolveEntity(ticker);
          context.data.stockEntity = stockInfo;
          context.data.currentTicker = stockInfo.tsCode || ticker;
          context.data.multiStockEntities = null;
          return { success: true, data: stockInfo, message: `已解析：${stockInfo.name}（${stockInfo.tsCode}），所属 ${stockInfo.sector || "未知行业"}` };
        } finally { dataService.close(); }
      }
      
      if (tickers.length === 1) {
        // 只匹配到一个股票，单标模式
        const dataService = new MarketDataService();
        try {
          const stockInfo = dataService.resolveEntity(tickers[0]);
          context.data.stockEntity = stockInfo;
          context.data.currentTicker = stockInfo.tsCode || tickers[0];
          context.data.multiStockEntities = null;
          return { success: true, data: stockInfo, message: `已解析：${stockInfo.name}（${stockInfo.tsCode}），所属 ${stockInfo.sector || "未知行业"}` };
        } finally { dataService.close(); }
      }
      
      // 多标模式
      const dataService = new MarketDataService();
      try {
        const stockEntities = [];
        for (const ticker of tickers) {
          try {
            const stockInfo = dataService.resolveEntity(ticker);
            stockEntities.push(stockInfo);
          } catch (e) {
            stockEntities.push({ tsCode: ticker, name: ticker, sector: "未知" });
          }
        }
        
        context.data.stockEntity = stockEntities[0]; // 主标
        context.data.currentTicker = stockEntities[0].tsCode;
        context.data.multiStockEntities = stockEntities; // 多标列表
        context.data.multiStockTickers = tickers;
        
        const names = stockEntities.map(s => `${s.name}(${s.tsCode})`).join("、");
        return { success: true, data: stockEntities, message: `已解析 ${tickers.length} 只股票：${names}` };
      } finally { dataService.close(); }
    },
  },

  run_governed_stock_deep_dive: {
    toolId: "run_governed_stock_deep_dive",
    name: "运行个股深度研究 V3",
    description: "调用受治理研究内核，完成证据收集、确定性分析、长文综合与质量审查",
    inputSchema: { type: "object", properties: { ticker: { type: "string" } } },
    execute: async (context) => {
      const runner = context.governedWorkflowRunner;
      if (!runner || typeof runner.runStockDeepDive !== "function") {
        return { success: false, message: "受治理个股深研运行器未配置", skipEvidenceCapture: true };
      }
      const ticker = String(
        context.data.currentTicker || context.data.stockEntity?.tsCode || context.currentInput?.ticker || ""
      ).trim().toUpperCase();
      if (!ticker) {
        return { success: false, message: "缺少已解析的股票代码", skipEvidenceCapture: true };
      }
      const governedInput = {
        ticker,
        acquisitionMode: "refresh_if_stale",
      };
      if (typeof context.onResearchProgress === "function") {
        governedInput.onProgress = context.onResearchProgress;
      }
      const governed = await runner.runStockDeepDive(governedInput);
      const packet = governed.packet || {};
      const quality = packet.quality || {};
      const evidenceItems = packet.datasets?.evidence?.items || [];
      const usableIds = new Set(quality.usable_evidence_ids || []);
      const evidenceCatalog = evidenceItems
        .filter((item) => usableIds.has(item.evidence_id))
        .map((item) => ({
          evidence_id: item.evidence_id,
          tool_id: "run_governed_stock_deep_dive",
          source_name: item.source_key || item.source_type || "受治理研究证据",
          source_urls: item.url_or_doc_id ? [item.url_or_doc_id] : [],
          as_of: item.published_at || null,
          freshness: item.status === "valid" ? "fresh" : "unknown",
          item_count: 1,
          quality_score: item.quality_score ?? null,
        }));
      const researchCorpus = packet.research_v3?.context?.corpus || {};
      const catalogById = new Map(evidenceCatalog.map((item) => [item.evidence_id, item]));
      for (const [collection, fallbackName] of [
        [researchCorpus.chunks || [], "正式披露文档片段"],
        [researchCorpus.news || [], "外部新闻背景"],
        [researchCorpus.events || [], "市场事件记录"],
        [researchCorpus.broker_reports || [], "券商二级研究"],
      ]) {
        for (const item of collection) {
          if (!item?.evidence_id || catalogById.has(String(item.evidence_id))) continue;
          catalogById.set(String(item.evidence_id), {
            evidence_id: String(item.evidence_id),
            tool_id: "run_governed_stock_deep_dive",
            source_name: item.source_name || item.source_key || fallbackName,
            source_urls: item.url ? [item.url] : [],
            as_of: item.published_at || item.event_date || null,
            freshness: ["context_only", "secondary_context_only"].includes(item.allowed_usage)
              ? "context_only"
              : "unknown",
            item_count: 1,
            quality_score: item.retrieval_score ?? null,
          });
        }
      }
      const completeEvidenceCatalog = [...catalogById.values()];
      const reportGate = quality.report_gate || {};
      const reportValidation = quality.report_validation || {};
      const synthesisValidation = governed.synthesis?.validation || null;
      const finalValidation = synthesisValidation || reportValidation;
      const citationValidation = {
        status: finalValidation.status === "passed" ? "passed" : "warning",
        coverage: reportGate.citation_coverage ?? (completeEvidenceCatalog.length > 0 ? 1 : 0),
        auditable_claim_count: packet.claims?.length || 0,
        cited_claim_count: packet.claims?.length || 0,
        cited_evidence_ids: finalValidation.cited_evidence_ids || quality.usable_evidence_ids || [],
        unknown_citation_ids: finalValidation.unknown_citation_ids || [],
        missing_citation_claims: [],
        current_claim_violations: [],
        authority: packet.workflow_version === "3.0" ? "stock_deep_dive_v3" : "stock_deep_dive_v2",
      };
      context.data.finalResponse = governed.report;
      context.data.evidenceCatalog = completeEvidenceCatalog;
      context.data.evidenceIds = completeEvidenceCatalog.map((item) => item.evidence_id);
      const eligibility = finalValidation.eligibility
        || packet.research_v3?.report_quality?.eligibility
        || null;
      const researchReportReady = finalValidation.status === "passed"
        && eligibility?.eligible !== false
        && (packet.claims?.length || 0) > 0;
      const currentMarketReady = researchReportReady
        && reportGate.report_status === "research_ready";
      context.data.dataHealth = {
        status: researchReportReady ? (currentMarketReady ? "healthy" : "warning") : "blocked",
        can_claim_current: currentMarketReady,
        research_report_ready: researchReportReady,
        current_market_ready: currentMarketReady,
        total_evidence: completeEvidenceCatalog.length,
        fresh_current_evidence: completeEvidenceCatalog.filter((item) => item.freshness === "fresh").length,
        authority: packet.workflow_version === "3.0" ? "stock_deep_dive_v3" : "stock_deep_dive_v2",
      };
      context.data.citationValidation = citationValidation;
      context.data.reportQualityGate = {
        passed: researchReportReady,
        source: packet.workflow_version === "3.0" ? "stock_deep_dive_v3" : "stock_deep_dive_v2",
        report_status: reportGate.report_status || "cannot_conclude",
        eligibility,
        citation_coverage: reportGate.citation_coverage ?? null,
        synthesis_mode: governed.synthesis?.mode || "governed_draft",
        characters: finalValidation.characters ?? governed.report.length,
        section_count: finalValidation.section_count ?? null,
      };
      context.data.extractedMemories = [];
      context.data.governedWorkflow = {
        run_id: governed.run_id,
        workflow_id: governed.workflow_id,
        status: governed.status,
        summary: governed.summary,
        artifacts: governed.artifacts,
        citationValidation,
        synthesis: governed.synthesis || null,
        events: governed.events || [],
        researchExecution: governed.researchExecution || null,
      };
      context.data.researchExecution = governed.researchExecution || null;
      return {
        success: true,
        data: {
          run_id: governed.run_id,
          report_status: reportGate.report_status || "cannot_conclude",
          artifact_ids: governed.artifacts.map((item) => item.artifact_id),
        },
        message: `个股深度研究 ${packet.workflow_version === "3.0" ? "V3" : "V2"} 已完成：${governed.run_id}`,
        skipEvidenceCapture: true,
      };
    },
  },

  run_governed_workflow: {
    toolId: "run_governed_workflow",
    name: "运行受治理研究工作流",
    description: "把自然语言任务适配为已注册的 Python 工作流输入，并返回真实运行与制品",
    inputSchema: { type: "object", properties: {} },
    execute: async (context) => {
      const runner = context.governedWorkflowRunner;
      if (!runner || typeof runner.runWorkflow !== "function") {
        return { success: false, message: "受治理工作流运行器未配置", skipEvidenceCapture: true };
      }
      const workflowId = String(context.currentTaskType || "").trim();
      try {
        const input = buildGovernedWorkflowInput(workflowId, context);
        const governed = await runner.runWorkflow({ workflowId, input });
        context.data.governedWorkflow = {
          run_id: governed.run_id,
          workflow_id: governed.workflow_id,
          status: governed.status,
          summary: governed.summary,
          artifacts: governed.artifacts,
          events: governed.events || [],
          researchExecution: governed.researchExecution || null,
        };
        context.data.researchExecution = governed.researchExecution || null;
        if (workflowId === "claim_correction" && governed.summary?.approved && context.sessionState) {
          const correction = governed.summary.correction || input.correction || {};
          const targetChange = (governed.summary.changes || [])
            .find((change) => change.claim_id === correction.claim_id);
          if (targetChange) {
            context.sessionState.addConfirmedFact({
              field: targetChange.metric || targetChange.claim_id,
              value: targetChange.new_value,
              unit: targetChange.unit || "",
              ticker: input.entity_key || null,
              source: correction.source,
              evidenceId: correction.evidence_id,
              asOf: new Date().toISOString(),
            });
            context.sessionState.addUserCorrection({
              field: targetChange.metric || targetChange.claim_id,
              oldValue: targetChange.old_value,
              newValue: targetChange.new_value,
              entity: input.entity_key || null,
              reason: "权威数据重新取数与依赖重算已通过",
              status: "revalidated",
              evidenceId: correction.evidence_id,
            });
          }
        }
        if (governed.primaryArtifactContent) {
          const mimeType = governed.primaryArtifact?.mime_type;
          context.data.finalResponse = mimeType === "application/json"
            ? `# ${governed.primaryArtifact?.title || "研究制品"}\n\n\`\`\`json\n${governed.primaryArtifactContent}\n\`\`\``
            : governed.primaryArtifactContent;
        }
        return {
          success: true,
          data: {
            run_id: governed.run_id,
            workflow_id: governed.workflow_id,
            status: governed.status,
            artifact_ids: governed.artifacts.map((item) => item.artifact_id),
          },
          message: `${workflowId} 已完成：${governed.run_id}`,
          skipEvidenceCapture: true,
        };
      } catch (error) {
        return {
          success: false,
          message: error instanceof Error ? error.message : String(error),
          skipEvidenceCapture: true,
        };
      }
    },
  },

  get_stock_data: {
    toolId: "get_stock_data",
    name: "获取股票全景数据",
    description: "获取股票的完整数据，包括行情、估值、基本面、技术面，支持多标",
    inputSchema: { type: "object", properties: { ticker: { type: "string" } } },
    execute: async (context) => {
      // 检查是否是多标模式
      const multiTickers = context.data.multiStockTickers;
      
      if (multiTickers && multiTickers.length > 1) {
        // 多标模式：获取所有股票数据
        const dataService = new MarketDataService();
        try {
          const multiStockData = [];
          
          for (const ticker of multiTickers) {
            try {
              const dailyBars = dataService.getDailyBars(ticker, 20);
              const valuation = dataService.getValuation(ticker);
              const fundamentals = dataService.getFundamentals(ticker);
              const factors = dataService.getFactors(ticker);
              const riskAlerts = dataService.getRiskAlerts(ticker, 5);
              
              let momentum5d = null, momentum20d = null;
              if (dailyBars.length >= 2) {
                const latest = dailyBars[0];
                const fiveDaysAgo = dailyBars[Math.min(4, dailyBars.length - 1)];
                const twentyDaysAgo = dailyBars[Math.min(19, dailyBars.length - 1)];
                if (latest?.close && fiveDaysAgo?.close) momentum5d = ((latest.close - fiveDaysAgo.close) / fiveDaysAgo.close) * 100;
                if (latest?.close && twentyDaysAgo?.close) momentum20d = ((latest.close - twentyDaysAgo.close) / twentyDaysAgo.close) * 100;
              }
              
              multiStockData.push({
                ticker,
                name: context.data.multiStockEntities?.find(e => e.tsCode === ticker)?.name || ticker,
                sector: context.data.multiStockEntities?.find(e => e.tsCode === ticker)?.sector || "未知",
                dailyBars: dailyBars.slice(0, 5).map((b) => ({ date: b.trade_date, open: b.open, close: b.close, high: b.high, low: b.low, volume: b.vol, pctChg: b.pct_chg })),
                latestPrice: dailyBars[0]?.close || valuation?.current_price || null,
                latestDate: dailyBars[0]?.trade_date || null,
                valuation: valuation ? { pe: valuation.pe_ttm, pb: valuation.pb, ps: valuation.ps_ttm, marketCap: valuation.market_cap, historicalPercentile: valuation.historical_percentile } : null,
                fundamentals: fundamentals ? { period: fundamentals.period, createdAt: fundamentals.created_at, freshnessStatus: fundamentals.freshness_status, revenue: fundamentals.revenue, netIncome: fundamentals.net_income, roe: fundamentals.roe, grossMargin: fundamentals.gross_margin } : null,
                technical: { rsi14: factors.rsi_14 ?? null, macdDif: factors.macd_dif ?? null, ma20: factors.ma_20 ?? null, tradeDate: factors._tradeDate ?? null },
                momentum: { m5d: momentum5d, m20d: momentum20d },
                riskAlerts: riskAlerts.map((a) => ({ time: a.alert_time, type: a.alert_type, severity: a.severity, message: a.message })),
              });
            } catch (e) {
              multiStockData.push({ ticker, name: ticker, error: e.message });
            }
          }
          
          // 批量获取实时行情数据（腾讯财经 API），补充 PB/PS/市值/换手率等
          try {
            const realtimeDataMap = await fetchRealtimeData(multiTickers);
            for (const stock of multiStockData) {
              const rt = realtimeDataMap[stock.ticker];
              if (rt) {
                if (rt.latest_price != null) stock.latestPrice = rt.latest_price;
                if (rt.trade_date) stock.latestDate = rt.trade_date;
                stock.source = rt.source;
                stock.source_url = rt.source_url;
                stock.fetched_at = rt.fetched_at;
                stock.marketSessionStatus = rt.market_session_status;
                if (rt.change_percent != null) stock.changePercent = rt.change_percent;
                if (!stock.valuation) stock.valuation = {};
                if (rt.pe_ttm != null) stock.valuation.pe = rt.pe_ttm;
                if (rt.pb != null) stock.valuation.pb = rt.pb;
                if (rt.ps_ttm != null) stock.valuation.ps = rt.ps_ttm;
                if (rt.market_cap != null) stock.valuation.marketCap = rt.market_cap;
                if (!stock.technical) stock.technical = {};
                if (rt.turnover_rate != null) stock.technical.turnoverRate = rt.turnover_rate;
              }
            }
          } catch (err) {
            console.warn("[get_stock_data] 实时数据补充失败:", err.message);
          }

          context.data.multiStockData = multiStockData;
          context.data.instrumentData = multiStockData[0]; // 兼容单标模式
          context.data.currentTicker = multiTickers[0];
          
          const names = multiStockData.map(s => s.name).join("、");
          return { success: true, data: multiStockData, message: `获取到 ${multiTickers.length} 只股票数据：${names}` };
        } finally { dataService.close(); }
      }
      
      // 单标模式（原有逻辑）
      const ticker = resolveTicker(context.currentInput?.ticker || context.input?.ticker || context.data.currentTicker);
      if (!ticker) return { success: false, message: "缺少 ticker 参数" };
      
      const dataService = new MarketDataService();
      try {
        const dailyBars = dataService.getDailyBars(ticker, 20);
        const valuation = dataService.getValuation(ticker);
        const fundamentals = dataService.getFundamentals(ticker);
        const factors = dataService.getFactors(ticker);
        const riskAlerts = dataService.getRiskAlerts(ticker, 5);
        
        let momentum5d = null, momentum20d = null;
        if (dailyBars.length >= 2) {
          const latest = dailyBars[0];
          const fiveDaysAgo = dailyBars[Math.min(4, dailyBars.length - 1)];
          const twentyDaysAgo = dailyBars[Math.min(19, dailyBars.length - 1)];
          if (latest?.close && fiveDaysAgo?.close) momentum5d = ((latest.close - fiveDaysAgo.close) / fiveDaysAgo.close) * 100;
          if (latest?.close && twentyDaysAgo?.close) momentum20d = ((latest.close - twentyDaysAgo.close) / twentyDaysAgo.close) * 100;
        }
        
        const instrumentData = {
          dailyBars: dailyBars.slice(0, 5).map((b) => ({ date: b.trade_date, open: b.open, close: b.close, high: b.high, low: b.low, volume: b.vol, pctChg: b.pct_chg })),
          latestPrice: dailyBars[0]?.close || valuation?.current_price || null,
          latestDate: dailyBars[0]?.trade_date || null,
          valuation: valuation ? { pe: valuation.pe_ttm, pb: valuation.pb, ps: valuation.ps_ttm, marketCap: valuation.market_cap, historicalPercentile: valuation.historical_percentile } : null,
          fundamentals: fundamentals ? { period: fundamentals.period, createdAt: fundamentals.created_at, freshnessStatus: fundamentals.freshness_status, revenue: fundamentals.revenue, netIncome: fundamentals.net_income, roe: fundamentals.roe, grossMargin: fundamentals.gross_margin } : null,
          technical: { rsi14: factors.rsi_14 ?? null, macdDif: factors.macd_dif ?? null, ma20: factors.ma_20 ?? null, tradeDate: factors._tradeDate ?? null },
          momentum: { m5d: momentum5d, m20d: momentum20d },
          riskAlerts: riskAlerts.map((a) => ({ time: a.alert_time, type: a.alert_type, severity: a.severity, message: a.message })),
        };

        // 补充实时行情数据（腾讯财经 API）
        try {
          const rt = await fetchRealtimeData(ticker);
          if (rt) {
            if (rt.latest_price != null) instrumentData.latestPrice = rt.latest_price;
            if (rt.trade_date) instrumentData.latestDate = rt.trade_date;
            instrumentData.source = rt.source;
            instrumentData.source_url = rt.source_url;
            instrumentData.fetched_at = rt.fetched_at;
            instrumentData.marketSessionStatus = rt.market_session_status;
            if (rt.change_percent != null) instrumentData.changePercent = rt.change_percent;
            if (!instrumentData.valuation) instrumentData.valuation = {};
            if (rt.pe_ttm != null) instrumentData.valuation.pe = rt.pe_ttm;
            if (rt.pb != null) instrumentData.valuation.pb = rt.pb;
            if (rt.ps_ttm != null) instrumentData.valuation.ps = rt.ps_ttm;
            if (rt.market_cap != null) instrumentData.valuation.marketCap = rt.market_cap;
            if (!instrumentData.technical) instrumentData.technical = {};
            if (rt.turnover_rate != null) instrumentData.technical.turnoverRate = rt.turnover_rate;
          }
        } catch (err) {
          console.warn("[get_stock_data] 实时数据补充失败:", err.message);
        }

        // 补充东方财富增强数据（资金流向+龙虎榜+财务历史+券商研报）
        try {
          const enhancedData = await eastmoneyDataService.getAllEnhancedData(ticker);
          context.data.eastmoneyData = enhancedData;
          const emStats = `资金流向${enhancedData.fundFlow?.length || 0}天/龙虎榜${enhancedData.dragonTiger?.length || 0}条/财务历史${enhancedData.financialHistory?.length || 0}期/券商研报${enhancedData.researchReports?.length || 0}篇`;
          console.log(`[get_stock_data] 东方财富增强数据: ${emStats}`);
        } catch (emErr) {
          console.warn("[get_stock_data] 东方财富增强数据获取失败:", emErr.message);
          context.data.eastmoneyData = null;
        }

        context.data.instrumentData = instrumentData;
        context.data.currentTicker = ticker;
        return {
          success: true,
          data: { instrumentData, eastmoneyData: context.data.eastmoneyData || null },
          message: `获取到 ${ticker} 的全景数据`,
        };
      } finally { dataService.close(); }
    },
  },

  get_news: {
    toolId: "get_news",
    name: "获取股票新闻",
    description: "获取指定股票的最新新闻和公告，支持多标。自动接入财联社、格隆汇、中国基金报、华尔街见闻、Yahoo Finance、Business Insider 7 个源 + Tavily 按需搜索",
    inputSchema: { type: "object", properties: { ticker: { type: "string" }, limit: { type: "number", default: 10 } } },
    execute: async (context) => {
      const dataService = new MarketDataService();
      let cnService = null;
      try {
        cnService = new ChineseNewsService();
      } catch (_) { /* fail-soft */ }

      try {
        // 多标模式
        if (context.data.multiStockTickers && context.data.multiStockTickers.length > 1) {
          const allNews = [];
          const allEvents = [];

          for (const ticker of context.data.multiStockTickers) {
            try {
              const dbNews = dataService.getNews(ticker, context.currentInput?.limit || 5);
              const events = dataService.getMarketEvents(ticker, 3);

              // 抓取中文新闻并过滤
              let merged = dbNews || [];
              if (cnService) {
                try {
                  const allChineseNews = await cnService.fetchAll(5);

                  // 先对所有新闻补充正文（这样所有源都有机会被补充）
                  if (allChineseNews.length > 0) {
                    try {
                      await cnService.enrichWithFirecrawl(allChineseNews, { maxTotalScrape: 8 });
                    } catch (_) { /* ignore firecrawl errors */ }
                  }

                  const stockName = STOCK_NAME_MAP[ticker] || "";
                  const chineseNews = cnService.filterByStock(allChineseNews, ticker, stockName);

                  // Tavily 按需搜索
                  let tavilyNews = [];
                  try {
                    const codeOnly = ticker.replace(/\.(SZ|SH|BJ|HK)$/i, "");
                    const searchQuery = stockName 
                      ? `${stockName} ${codeOnly} 最新消息 财报`
                      : `${codeOnly} 股票 最新消息`;
                    tavilyNews = await cnService.fetchTavilySearch(searchQuery, 5);
                  } catch (_) { /* ignore */ }

                  // CNINFO 巨潮资讯
                  let cninfoNews = [];
                  try {
                    const codeOnly = ticker.replace(/\.(SZ|SH|BJ|HK)$/i, "");
                    cninfoNews = await cnService.fetchCninfoAnnouncements(codeOnly, 5);
                  } catch (_) { /* ignore */ }

                  merged = mergeNewsDedup([...cninfoNews, ...tavilyNews, ...chineseNews], dbNews || []);
                } catch (_) { /* ignore */ }
              }

              allNews.push(...merged.map(n => ({ ...n, ticker })));
              allEvents.push(...events.map(e => ({ ...e, ticker })));
            } catch (e) {
              // 忽略单个股票的错误
            }
          }

          context.data.news = allNews;
          context.data.events = allEvents;
          return { success: true, data: { news: allNews, events: allEvents }, message: `获取到 ${allNews.length} 条多标新闻（含中文源 + Tavily 搜索）` };
        }

        // 单标模式
        const ticker = resolveTicker(context.currentInput?.ticker || context.data.currentTicker);
        if (!ticker) return { success: false, message: "缺少 ticker 参数" };

        const dbNews = dataService.getNews(ticker, context.currentInput?.limit || 10);
        const events = dataService.getMarketEvents(ticker, 5);

        // 抓取中文新闻并过滤
        let merged = dbNews || [];
        if (cnService) {
          try {
            const allChineseNews = await cnService.fetchAll(5);

            // 先对所有新闻补充正文（这样所有源都有机会被补充）
            if (allChineseNews.length > 0) {
              try {
                await cnService.enrichWithFirecrawl(allChineseNews, { maxTotalScrape: 10 });
              } catch (_) { /* ignore firecrawl errors */ }
            }

            const stockName = STOCK_NAME_MAP[ticker] || "";
            const chineseNews = cnService.filterByStock(allChineseNews, ticker, stockName);

            // Tavily 按需搜索
            let tavilyNews = [];
            try {
              const codeOnly = ticker.replace(/\.(SZ|SH|BJ|HK)$/i, "");
              const searchQuery = stockName 
                ? `${stockName} ${codeOnly} 最新消息 财报`
                : `${codeOnly} 股票 最新消息`;
              tavilyNews = await cnService.fetchTavilySearch(searchQuery, 5);
            } catch (_) { /* ignore */ }

            // CNINFO 巨潮资讯
            let cninfoNews = [];
            try {
              const codeOnly = ticker.replace(/\.(SZ|SH|BJ|HK)$/i, "");
              cninfoNews = await cnService.fetchCninfoAnnouncements(codeOnly, 5);
            } catch (_) { /* ignore */ }

            merged = mergeNewsDedup([...cninfoNews, ...tavilyNews, ...chineseNews], dbNews || []);
          } catch (_) { /* ignore */ }
        }

        context.data.news = merged;
        context.data.events = events;

        const posKeys = ["增长", "买入", "领先", "优势", "突破", "超预期", "上调", "获批"];
        const negKeys = ["下降", "下调", "风险", "亏损", "下滑", "警示", "处罚"];
        let posCount = 0, negCount = 0;
        for (const n of merged) {
          const text = (n.title + " " + (n.body || "")).toLowerCase();
          if (posKeys.some((k) => text.includes(k))) posCount++;
          if (negKeys.some((k) => text.includes(k))) negCount++;
        }

        context.data.marketSummary = { newsCount: merged.length, eventCount: events.length,
          sentiment: posCount > negCount ? "positive" : negCount > posCount ? "negative" : "neutral",
          positiveCount: posCount, negativeCount: negCount };
        return { success: true, data: { news: merged, events }, message: `获取到 ${merged.length} 条新闻（含中文源）` };
      } finally { dataService.close(); }
    },
  },

  get_top_gainers: {
    toolId: "get_top_gainers",
    name: "获取涨幅榜",
    description: "获取最新交易日涨幅最大的股票",
    inputSchema: { type: "object", properties: { limit: { type: "number", default: 10 } } },
    execute: async (context) => {
      const limit = context.currentInput?.limit || 10;
      // 优先用实时数据（东方财富API）
      try {
        const realtimeData = await fetchTopGainers(limit);
        if (realtimeData.length > 0) {
          context.data.topGainers = realtimeData;
          // 把真实数据日期写入 context
          if (!context.data.instrumentData) context.data.instrumentData = {};
          context.data.instrumentData.latestDate = realtimeData[0].trade_date;
          return { success: true, data: realtimeData, message: `获取到实时涨幅榜 ${realtimeData.length} 只（东方财富）` };
        }
      } catch (err) {
        console.warn("[workflow] 实时涨幅榜获取失败，回退到本地数据库:", err.message);
      }
      // fallback：本地数据库
      const dataService = new MarketDataService();
      try {
        context.data.topGainers = dataService.getTopGainers(limit);
        if (context.data.topGainers.length > 0) {
          if (!context.data.instrumentData) context.data.instrumentData = {};
          context.data.instrumentData.latestDate = context.data.topGainers[0].trade_date;
        }
        return { success: true, data: context.data.topGainers, message: `获取到涨幅榜 ${context.data.topGainers.length} 只（本地数据库）` };
      } finally { dataService.close(); }
    },
  },

  get_top_losers: {
    toolId: "get_top_losers",
    name: "获取跌幅榜",
    description: "获取最新交易日跌幅最大的股票",
    inputSchema: { type: "object", properties: { limit: { type: "number", default: 10 } } },
    execute: async (context) => {
      const limit = context.currentInput?.limit || 10;
      // 优先用实时数据
      try {
        const realtimeData = await fetchTopLosers(limit);
        if (realtimeData.length > 0) {
          context.data.topLosers = realtimeData;
          return { success: true, data: realtimeData, message: `获取到实时跌幅榜 ${realtimeData.length} 只（东方财富）` };
        }
      } catch (err) {
        console.warn("[workflow] 实时跌幅榜获取失败，回退到本地数据库:", err.message);
      }
      // fallback：本地数据库
      const dataService = new MarketDataService();
      try {
        context.data.topLosers = dataService.getTopLosers(limit);
        return { success: true, data: context.data.topLosers, message: `获取到跌幅榜 ${context.data.topLosers.length} 只（本地数据库）` };
      } finally { dataService.close(); }
    },
  },

  get_volume_surge: {
    toolId: "get_volume_surge",
    name: "获取放量异动",
    description: "获取成交量异常放大的股票",
    inputSchema: { type: "object", properties: { limit: { type: "number", default: 10 }, volumeRatioThreshold: { type: "number", default: 1.5 } } },
    execute: async (context) => {
      const limit = context.currentInput?.limit || 10;
      const volumeRatioThreshold = context.currentInput?.volumeRatioThreshold || 1.5;
      // 优先用实时数据
      try {
        const realtimeData = await fetchVolumeSurge(limit, volumeRatioThreshold);
        if (realtimeData.length > 0) {
          context.data.volumeSurge = realtimeData;
          const isTrueVolumeRatio = realtimeData.some((item) => item.activity_signal === "volume_ratio");
          context.data.volumeSurgeMode = isTrueVolumeRatio ? "volume_ratio" : "turnover";
          return {
            success: true,
            data: realtimeData,
            message: isTrueVolumeRatio
              ? `获取到 ${realtimeData.length} 只实时放量异动股票`
              : `量比不可用，降级获取到 ${realtimeData.length} 只高换手异动股票`,
          };
        }
      } catch (err) {
        console.warn("[workflow] 实时放量异动获取失败，回退到本地数据库:", err.message);
      }
      // fallback：本地数据库
      const dataService = new MarketDataService();
      try {
        context.data.volumeSurge = dataService.getVolumeSurge(limit, volumeRatioThreshold);
        return { success: true, data: context.data.volumeSurge, message: `获取到 ${context.data.volumeSurge.length} 只放量异动股票（本地数据库）` };
      } finally { dataService.close(); }
    },
  },

  get_price_movement: {
    toolId: "get_price_movement",
    name: "获取价格异动",
    description: "获取涨跌幅超过阈值的股票",
    inputSchema: { type: "object", properties: { threshold: { type: "number", default: 3 }, limit: { type: "number", default: 10 } } },
    execute: async (context) => {
      const threshold = context.currentInput?.threshold || 3;
      const limit = context.currentInput?.limit || 10;
      // 优先用实时数据
      try {
        const realtimeData = await fetchPriceMovement(threshold, limit);
        if (realtimeData.length > 0) {
          context.data.priceMovement = realtimeData;
          return { success: true, data: realtimeData, message: `获取到 ${realtimeData.length} 只实时价格异动股票（东方财富）` };
        }
      } catch (err) {
        console.warn("[workflow] 实时价格异动获取失败，回退到本地数据库:", err.message);
      }
      // fallback：本地数据库
      const dataService = new MarketDataService();
      try {
        context.data.priceMovement = dataService.getPriceMovement(threshold, limit);
        return { success: true, data: context.data.priceMovement, message: `获取到 ${context.data.priceMovement.length} 只价格异动股票（本地数据库）` };
      } finally { dataService.close(); }
    },
  },

  get_valuation_extremes: {
    toolId: "get_valuation_extremes",
    name: "获取估值极端标的",
    description: "获取估值处于历史极端位置的股票",
    inputSchema: { type: "object", properties: { limit: { type: "number", default: 10 } } },
    execute: async (context) => {
      const dataService = new MarketDataService();
      try {
        context.data.valuationExtremes = dataService.getValuationExtremes(context.currentInput?.limit || 10);
        return { success: true, data: context.data.valuationExtremes, message: `获取到 ${context.data.valuationExtremes.length} 只估值极端标的` };
      } finally { dataService.close(); }
    },
  },

  get_market_indices: {
    toolId: "get_market_indices",
    name: "获取大盘指数",
    description: "获取A股主要大盘指数实时行情（上证指数、深证成指、创业板指、科创50、沪深300等）",
    inputSchema: { type: "object", properties: {} },
    execute: async (context) => {
      try {
        const { fetchMarketIndices } = await import("./realtime-data-service.js");
        const indices = await fetchMarketIndices();
        context.data.marketIndices = indices;
        return {
          success: indices.length > 0,
          data: indices,
          message: indices.length > 0 ? `获取到 ${indices.length} 个大盘指数` : "大盘指数源返回空结果",
        };
      } catch (err) {
        console.warn("[workflow] 获取大盘指数失败:", err.message);
        context.data.marketIndices = [];
        return { success: false, data: [], message: "获取大盘指数失败" };
      }
    },
  },

  get_latest_news: {
    toolId: "get_latest_news",
    name: "获取最新新闻",
    description: "获取最新发布的市场新闻",
    inputSchema: { type: "object", properties: { limit: { type: "number", default: 15 } } },
    execute: async (context) => {
      const dataService = new MarketDataService();
      try {
        const limit = context.currentInput?.limit || 15;
        const localNews = dataService.getLatestNews(limit);
        let liveNews = [];
        try {
          const cnService = new ChineseNewsService();
          const searchOptions = {
            topic: "news",
            days: 7,
            includeDomains: [
              "cls.cn",
              "stcn.com",
              "cnstock.com",
              "finance.sina.com.cn",
              "eastmoney.com",
            ],
          };
          const hotNameList = (context.data.topGainers || [])
            .filter(opportunityCandidate)
            .slice(0, 4)
            .map((item) => item.name)
            .filter(Boolean);
          const hotNames = hotNameList.join(" ");
          const searches = await Promise.allSettled([
            cnService.fetchTavilySearch(
              "A股 沪深股市 今日 最新 政策 行业 资金 市场",
              limit,
              searchOptions,
            ),
            hotNames
              ? cnService.fetchTavilySearch(`${hotNames} 最新 公告 催化`, Math.max(5, Math.ceil(limit / 2)), searchOptions)
              : Promise.resolve([]),
          ]);
          const genericNews = searches[0].status === "fulfilled"
            ? searches[0].value.map((item) => ({ ...item, search_scope: "market" }))
            : [];
          const hotStockNews = searches[1].status === "fulfilled"
            ? searches[1].value.map((item) => ({ ...item, search_scope: "hot_stock" }))
            : [];
          liveNews = [...hotStockNews, ...genericNews];
          // 无源站发布日期的搜索结果只能作为待核验线索，不能伪装成当期新闻。
          const newestAllowed = Date.now() + 6 * 60 * 60 * 1000;
          const oldestAllowed = Date.now() - 8 * 24 * 60 * 60 * 1000;
          liveNews = liveNews.filter((item) => {
            if (!item.published_at) return false;
            const publishedAt = new Date(item.published_at).getTime();
            if (!Number.isFinite(publishedAt) || publishedAt < oldestAllowed || publishedAt > newestAllowed) return false;
            if (/\/caifuhao\./i.test(item.url || "")) return false;
            const text = `${item.title || ""} ${item.body || ""}`;
            if (/股票行情|走势图|财经门户|机构调研详细|数据中心|行情中心|商业指数|上证\d+|首页/i.test(item.title || "")) return false;
            if ((item.body || "").trim().length < 40) return false;
            if (item.search_scope === "hot_stock" && !hotNameList.some((name) => text.includes(name))) return false;
            return /A股|沪深|上证|深证|创业板|科创板|北交所|人民币|央行|证监会|股票|上市公司|板块|行业/i.test(text);
          });
        } catch (error) {
          console.warn("[workflow] 实时市场新闻获取失败，回退本地新闻:", error.message);
        }
        const relevantLocalNews = localNews.filter((item) => {
          const publishedAt = new Date(item.published_at || 0).getTime();
          const text = `${item.title || ""} ${item.body || ""}`;
          return Number.isFinite(publishedAt)
            && publishedAt >= Date.now() - 8 * 24 * 60 * 60 * 1000
            && /A股|沪深|上证|深证|创业板|科创板|北交所|人民币|央行|证监会|上市公司/i.test(text);
        });
        context.data.latestNews = mergeNewsDedup(liveNews, relevantLocalNews, limit)
          .sort((a, b) => new Date(b.published_at || 0) - new Date(a.published_at || 0));
        return {
          success: context.data.latestNews.length > 0,
          data: context.data.latestNews,
          message: liveNews.length > 0
            ? `获取到 ${context.data.latestNews.length} 条市场新闻，其中 ${liveNews.length} 条来自实时搜索`
            : `实时新闻不可用，降级获取到 ${context.data.latestNews.length} 条本地新闻`,
        };
      } finally { dataService.close(); }
    },
  },

  get_movement_news: {
    toolId: "get_movement_news",
    name: "核对异动标的公告",
    description: "逐一查询涨跌幅榜标的的巨潮资讯公告，用于建立可验证的事件关联",
    inputSchema: { type: "object", properties: {} },
    execute: async (context) => {
      const stocks = [...(context.data.topGainers || []), ...(context.data.topLosers || [])]
        .filter((item, index, items) => item?.ts_code && items.findIndex((candidate) => candidate.ts_code === item.ts_code) === index)
        .slice(0, 20);
      if (stocks.length === 0) {
        context.data.movementNews = [];
        return { success: false, data: [], message: "涨跌幅榜为空，无法核对个股公告" };
      }

      const cnService = new ChineseNewsService();
      const collected = [];
      let failedQueries = 0;
      const batchSize = 5;
      for (let offset = 0; offset < stocks.length; offset += batchSize) {
        const batch = stocks.slice(offset, offset + batchSize);
        const results = await Promise.allSettled(batch.map((stock) => {
          const code = String(stock.ts_code).replace(/\.(SZ|SH|BJ)$/i, "");
          return cnService.fetchCninfoAnnouncements(code, 3);
        }));
        results.forEach((result, index) => {
          const stock = batch[index];
          if (result.status !== "fulfilled") {
            failedQueries += 1;
            return;
          }
          collected.push(...result.value.map((item) => ({
            ...item,
            ticker: stock.ts_code,
            stock_name: stock.name || STOCK_NAME_MAP[stock.ts_code] || stock.ts_code,
          })));
        });
      }
      context.data.movementNews = collected;
      return {
        success: collected.length > 0,
        data: collected,
        message: `核对 ${stocks.length} 只异动标的，取得 ${collected.length} 条巨潮公告，失败查询 ${failedQueries} 个`,
      };
    },
  },

  get_pool_snapshot: {
    toolId: "get_pool_snapshot",
    name: "获取股票池快照",
    description: "获取股票池标的的最新行情",
    inputSchema: {},
    execute: async (context) => {
      const dataService = new MarketDataService();
      try {
        context.data.poolSnapshot = dataService.getPoolSnapshot();
        return { success: true, data: context.data.poolSnapshot, message: `获取到 ${context.data.poolSnapshot.length} 只组合标的` };
      } finally { dataService.close(); }
    },
  },

  query_memory: {
    toolId: "query_memory",
    name: "查询记忆",
    description: "从记忆系统检索历史研究内容和相关上下文",
    inputSchema: { type: "object", properties: { query: { type: "string" }, ticker: { type: "string" } } },
    execute: async (context) => {
      const { query, ticker } = context.currentInput || {};
      const searchQuery = query || ticker || context.userQuery || "";
      
      const memService = new MemoryService();
      const vector = new VectorMemory();
      try {
        let stockMemories = [];
        if (ticker || context.data.currentTicker) stockMemories = memService.getMemoriesForTicker(resolveTicker(ticker || context.data.currentTicker), { limit: 10 });
        context.data.memoryResults = stockMemories;
        
        let vectorResults = [];
        if (searchQuery) vectorResults = await vector.searchSimilar(searchQuery, { limit: 5, threshold: 0.3 });
        context.data.vectorResults = vectorResults;
        
        context.data.memoryContextText = memService.formatMemoriesAsContext(stockMemories);
        return { success: true, data: { stockMemoryCount: stockMemories.length, vectorResultCount: vectorResults.length }, 
          message: `找到 ${stockMemories.length} 条股票记忆 + ${vectorResults.length} 条语义匹配` };
      } finally { memService.close(); vector.close(); }
    },
  },

  save_memory: {
    toolId: "save_memory",
    name: "保存记忆",
    description: "将分析结果保存为候选记忆",
    inputSchema: { type: "object", required: ["ticker", "content"], properties: { ticker: { type: "string" }, content: { type: "string" }, memoryType: { type: "string", default: "analysis" } } },
    execute: async (context) => {
      if (!isWriteToolAuthorized("save_memory", context)) {
        return { success: false, message: "候选记忆写入需要显式授权" };
      }
      const ticker = resolveTicker(context.currentInput?.ticker || context.data.currentTicker);
      if (!ticker) return { success: false, message: "缺少 ticker 参数" };
      
      const memService = new MemoryService();
      try {
        const content = context.currentInput?.content || context.data.llmAnalysis?.rawAnalysis || "";
        const memories = await memService.extractAndSaveMemories(ticker, content, context, null);
        context.data.savedMemories = memories;
        return { success: true, data: { memoryCount: memories.length }, message: `保存 ${memories.length} 条候选记忆` };
      } finally { memService.close(); }
    },
  },

  get_value_score: {
    toolId: "get_value_score",
    name: "获取价值评分",
    description: "计算股票的 VFM 价值评分",
    inputSchema: { type: "object", required: ["ticker"], properties: { ticker: { type: "string" } } },
    execute: async (context) => {
      const ticker = resolveTicker(context.currentInput?.ticker || context.data.currentTicker);
      if (!ticker) return { success: false, message: "缺少 ticker 参数" };
      
      const scores = buildValueScores();
      const stockScore = scores.scores.find((s) => s.tsCode === ticker);
      context.data.valueScore = stockScore;
      return { success: true, data: stockScore, message: stockScore ? `计算完成：${ticker} 评分 ${stockScore.score}分` : `${ticker} 暂无评分` };
    },
  },

  get_decisions: {
    toolId: "get_decisions",
    name: "获取决策记录",
    description: "获取投资决策历史记录",
    inputSchema: { type: "object", properties: { ticker: { type: "string" }, limit: { type: "number", default: 20 } } },
    execute: async (context) => {
      const decisionService = new DecisionService();
      try {
        const ticker = resolveTicker(context.currentInput?.ticker || context.data.currentTicker);
        context.data.decisions = decisionService.getDecisions({ ticker: ticker || null, limit: context.currentInput?.limit || 20 });
        return { success: true, data: context.data.decisions, message: `获取到 ${context.data.decisions.length} 条决策记录` };
      } finally { decisionService.close(); }
    },
  },

  create_decision: {
    toolId: "create_decision",
    name: "创建投资决策",
    description: "基于分析结果创建投资决策",
    inputSchema: { type: "object", required: ["ticker", "action", "thesisSummary"], properties: { ticker: { type: "string" }, action: { type: "string" }, thesisSummary: { type: "string" }, bearCaseSummary: { type: "string" }, referencePrice: { type: "number" }, killConditions: { type: "array" }, suggestedPositionPct: { type: "number" } } },
    execute: async (context) => {
      if (!isWriteToolAuthorized("create_decision", context)) {
        return { success: false, message: "正式决策写入需要人工审核授权" };
      }
      const ticker = resolveTicker(context.currentInput?.ticker || context.data.currentTicker);
      if (!ticker) return { success: false, message: "缺少 ticker 参数" };

      const thesisSummary = context.currentInput?.thesisSummary?.trim() || "";
      const bearCaseSummary = context.currentInput?.bearCaseSummary?.trim() || "";
      const killConditions = context.currentInput?.killConditions || [];
      const evidenceIds = context.currentInput?.evidenceIds || context.data.evidenceIds || [];
      if (!thesisSummary || !bearCaseSummary || killConditions.length === 0 || evidenceIds.length === 0) {
        return { success: false, message: "正式决策缺少论点、反方观点、失效条件或证据" };
      }
      
      const decisionService = new DecisionService();
      try {
        const record = decisionService.createDecision({
          ticker, action: context.currentInput?.action || "hold",
          thesisSummary,
          bearCaseSummary,
          referencePrice: context.currentInput?.referencePrice || context.data.instrumentData?.latestPrice || null,
          killConditions,
          suggestedPositionPct: context.currentInput?.suggestedPositionPct || null,
          evidenceIds, memoryIds: (context.data.savedMemories || []).map((m) => m.memory_id),
        });
        context.data.decisionRecord = record;
        return { success: true, data: record, message: `投资决策已记录：${record.action.toUpperCase()}` };
      } finally { decisionService.close(); }
    },
  },

  run_discovery: {
    toolId: "run_discovery",
    name: "运行发现管线",
    description: "运行新标的发现管线，筛选潜在投资标的",
    inputSchema: {},
    execute: async (context) => {
      context.data.discoveries = buildDiscoveries();
      return { success: true, data: context.data.discoveries, message: `发现 ${context.data.discoveries.length} 个新候选标的` };
    },
  },

  spawn_sub_agents: {
    toolId: "spawn_sub_agents",
    name: "生成子Agent并行分析",
    description: "为每只股票创建独立的子Agent进行并行深度分析",
    inputSchema: {},
    execute: async (context) => {
      const tickers = context.data.multiStockTickers || [context.data.currentTicker];
      if (!tickers || tickers.length === 0) {
        return { success: false, message: "没有可分析的标的" };
      }
      
      context.addLog?.("spawn_sub_agents", `准备为 ${tickers.length} 只股票创建子Agent`);
      
      // 并行执行所有子Agent
      const subAgentPromises = tickers.map(async (ticker) => {
        const subAgent = new SubAgent(ticker, context);
        return await subAgent.executeSingleStockAnalysis();
      });
      
      const results = await Promise.all(subAgentPromises);
      
      // 汇总结果
      const successfulResults = results.filter(r => r.success);
      const failedResults = results.filter(r => !r.success);
      
      context.data.subAgentResults = successfulResults;
      context.data.subAgentFailed = failedResults;
      
      // 将子Agent的执行历史汇总到主Agent
      for (const result of successfulResults) {
        if (result.executionHistory) {
          for (const log of result.executionHistory) {
            context.addLog?.(`${result.ticker}_${log.stepId}`, `[${result.ticker}] ${log.message}`, log.data);
          }
        }
      }
      
      const successCount = successfulResults.length;
      const failCount = failedResults.length;
      
      return {
        success: true,
        data: successfulResults,
        message: `子Agent分析完成：${successCount} 只成功${failCount > 0 ? `，${failCount} 只失败` : ""}`
      };
    },
  },

  analyze_with_llm: {
    toolId: "analyze_with_llm",
    name: "AI深度分析",
    description: "使用 LLM 对收集的数据进行深度分析",
    inputSchema: { type: "object", properties: { prompt: { type: "string" }, contextType: { type: "string", default: "general" } } },
    execute: async (context) => {
      if (!isModelAvailable()) return { success: false, message: "LLM 不可用" };
      
      const analysis = await generateAIAnalysis(context, context.currentInput?.prompt);
      context.data.llmAnalysis = analysis;
      return { success: true, data: analysis, message: "AI 深度分析完成" };
    },
  },

  get_us_data: {
    toolId: "get_us_data",
    name: "获取美股数据",
    description: "获取美股标的的行情、评级、新闻等数据",
    inputSchema: { type: "object", properties: { usTicker: { type: "string" } } },
    execute: async (context) => {
      const usTicker = context.currentInput?.usTicker || 
                       context.data.intent?.entities?.usTicker || 
                       context.userQuery?.match(/\b(NVDA|AMD|INTC|MSFT|GOOGL|AAPL|TSLA|META|AMZN|NFLX|BABA|TCEHY|JD|NIO)\b/i)?.[0];
      
      if (!usTicker) {
        return { success: false, message: "未找到美股标的" };
      }

      const wsData = await wallstreetDataService.getAllWallstreetData(usTicker.toUpperCase());
      context.data.usStockData = wsData;
      context.data.currentUsTicker = usTicker.toUpperCase();

      const rating = wsData.ratings;
      let message = `已获取 ${usTicker} 数据：`;
      if (rating && rating.totalAnalysts) {
        message += `分析师${rating.totalAnalysts}人，Buy ${rating.buy || 0}，Hold ${rating.hold || 0}，Sell ${rating.sell || 0}`;
      }
      if (wsData.news && wsData.news.length > 0) {
        message += `，新闻${wsData.news.length}条`;
      }

      return { success: true, data: wsData, message };
    },
  },

  find_us_mapping: {
    toolId: "find_us_mapping",
    name: "查找美股映射",
    description: "根据美股标的查找A股映射关系，包括映射维度和强度（三层查找：配置→行业→LLM）",
    inputSchema: { type: "object", properties: { usTicker: { type: "string" }, catalyst: { type: "string" } } },
    execute: async (context) => {
      const usTicker = context.currentUsTicker || 
                       context.currentInput?.usTicker ||
                       context.data.intent?.entities?.usTicker;
      
      if (!usTicker) {
        return { success: false, message: "未找到美股标的" };
      }

      const catalyst = context.data.usStockData?.news?.[0]?.headline || 
                      context.currentInput?.catalyst;
      const userQuery = context.userQuery;

      const mappingResult = await mappingAnalysisService.findMapping(usTicker, catalyst, userQuery);
      context.data.mappingResult = mappingResult;

      if (mappingResult.found) {
        return { 
          success: true, 
          data: mappingResult, 
          message: `找到映射：${mappingResult.aShareTargets.length}个A股标的，映射类型：${mappingResult.mappingTypeName}，强度：${(mappingResult.mappingStrength * 100).toFixed(0)}%` 
        };
      } else {
        return { success: false, data: mappingResult, message: mappingResult.reasoning };
      }
    },
  },

  analyze_mapping_impact: {
    toolId: "analyze_mapping_impact",
    name: "分析映射影响",
    description: "分析美股异动对A股映射标的的影响，生成投资建议",
    inputSchema: { type: "object", properties: { mappingResult: { type: "object" }, usAnalysis: { type: "object" } } },
    execute: async (context) => {
      const mappingResult = context.data.mappingResult;
      const usAnalysis = context.data.usStockData;

      if (!mappingResult || !mappingResult.found) {
        return { success: false, message: "未找到映射关系" };
      }

      const impactResult = await mappingAnalysisService.analyzeImpactFromMapping(mappingResult, usAnalysis);
      context.data.mappingImpact = impactResult;

      if (impactResult.success) {
        return { 
          success: true, 
          data: impactResult, 
          message: `影响分析完成：${impactResult.aShareImpact.length}个A股标的受影响，整体信号：${impactResult.overallSignal}` 
        };
      } else {
        return { success: false, message: impactResult.message };
      }
    },
  },
};

export const TASK_TYPES = {
  STOCK_DEEP_ANALYSIS: {
    id: "stock_deep_analysis",
    name: "股票深度分析",
    description: "对指定股票进行全面深度研究分析",
    requiresEntity: true,
    defaultFlow: ["resolve_entity", "run_governed_stock_deep_dive"],
    tools: ["resolve_entity", "run_governed_stock_deep_dive"],
  },
  VALUE_SCORE: {
    id: "value_score",
    name: "价值评分",
    description: "计算股票的 VFM 价值评分",
    requiresEntity: true,
    defaultFlow: ["resolve_entity", "get_stock_data", "get_value_score", "analyze_with_llm"],
    tools: ["resolve_entity", "get_stock_data", "get_value_score", "analyze_with_llm"],
  },
  OPPORTUNITY_SCAN: {
    id: "opportunity_scan",
    name: "机会扫描",
    description: "扫描市场中的投资机会",
    requiresEntity: false,
    defaultFlow: ["get_market_indices", "get_top_gainers", "get_top_losers", "get_volume_surge", "get_price_movement", "get_valuation_extremes", "get_latest_news", "get_pool_snapshot", "analyze_with_llm"],
    tools: ["get_top_gainers", "get_top_losers", "get_volume_surge", "get_price_movement", "get_valuation_extremes", "get_latest_news", "get_pool_snapshot", "analyze_with_llm"],
  },
  DISCOVERY: {
    id: "discovery",
    name: "新发现",
    description: "发现新的潜在投资标的",
    requiresEntity: false,
    defaultFlow: ["run_discovery", "get_stock_data", "get_value_score", "analyze_with_llm"],
    tools: ["run_discovery", "get_stock_data", "get_value_score", "analyze_with_llm"],
  },
  MARKET_NEWS: {
    id: "market_news",
    name: "市场新闻",
    description: "获取最新的市场新闻和公告",
    requiresEntity: false,
    defaultFlow: ["get_latest_news"],
    tools: ["get_latest_news", "get_news"],
  },
  MARKET_ATTRIBUTION: {
    id: "market_attribution",
    name: "涨跌幅归因分析",
    description: "核对涨跌幅榜与可验证新闻，只在存在同标的事件时给出关联线索",
    requiresEntity: false,
    defaultFlow: ["get_top_gainers", "get_top_losers", "get_movement_news"],
    tools: ["get_top_gainers", "get_top_losers", "get_movement_news"],
  },
  PORTFOLIO_REVIEW: {
    id: "portfolio_review",
    name: "组合回顾",
    description: "回顾当前组合的表现和风险状况",
    requiresEntity: false,
    defaultFlow: ["get_pool_snapshot", "get_decisions", "get_value_score", "analyze_with_llm"],
    tools: ["get_pool_snapshot", "get_decisions", "get_value_score", "analyze_with_llm"],
  },
  DAILY_BRIEF: {
    id: "daily_brief",
    name: "每日简报",
    description: "汇总当天的市场变化和研究更新",
    requiresEntity: false,
    defaultFlow: ["get_market_indices", "get_top_gainers", "get_top_losers", "get_volume_surge", "get_latest_news", "get_pool_snapshot", "get_decisions", "analyze_with_llm"],
    tools: ["get_market_indices", "get_top_gainers", "get_top_losers", "get_volume_surge", "get_latest_news", "get_pool_snapshot", "get_decisions", "analyze_with_llm"],
  },
  THESIS_UPDATE: {
    id: "thesis_update",
    name: "投资论更新",
    description: "更新或验证投资论点",
    requiresEntity: true,
    defaultFlow: ["resolve_entity", "query_memory", "get_news", "get_stock_data", "analyze_with_llm"],
    tools: ["resolve_entity", "query_memory", "get_news", "get_stock_data", "analyze_with_llm"],
  },
  RISK_ANALYSIS: {
    id: "risk_analysis",
    name: "风险分析",
    description: "分析股票或组合的风险状况",
    requiresEntity: true,
    defaultFlow: ["resolve_entity", "get_stock_data", "query_memory", "get_decisions", "analyze_with_llm"],
    tools: ["resolve_entity", "get_stock_data", "query_memory", "get_decisions", "analyze_with_llm"],
  },
  COMPETITOR_ANALYSIS: {
    id: "competitor_analysis",
    name: "竞争对手分析",
    description: "分析股票的竞争对手和行业格局",
    requiresEntity: true,
    defaultFlow: ["resolve_entity", "get_stock_data", "get_news", "get_value_score", "analyze_with_llm"],
    tools: ["resolve_entity", "get_stock_data", "get_news", "get_value_score", "analyze_with_llm"],
  },
  TREND_ANALYSIS: {
    id: "trend_analysis",
    name: "趋势分析",
    description: "分析股票的价格趋势和技术形态",
    requiresEntity: true,
    defaultFlow: ["resolve_entity", "get_stock_data", "get_price_movement", "analyze_with_llm"],
    tools: ["resolve_entity", "get_stock_data", "get_price_movement", "analyze_with_llm"],
  },
  MULTI_STOCK_COMPARISON: {
    id: "multi_stock_comparison",
    name: "多标对比",
    description: "对比分析多只股票，生成横向对比报告（使用子Agent并行分析）",
    requiresEntity: true,
    defaultFlow: ["resolve_entity", "spawn_sub_agents", "analyze_with_llm"],
    tools: ["resolve_entity", "spawn_sub_agents", "analyze_with_llm"],
  },
  CHAT: {
    id: "chat",
    name: "自由对话",
    description: "自由聊天，支持自然语言意图识别和动态流程组装",
    requiresEntity: false,
    isDynamic: true,
    defaultFlow: ["query_memory", "analyze_with_llm"],
    tools: ["query_memory", "analyze_with_llm", "get_us_data", "find_us_mapping", "analyze_mapping_impact", "get_stock_data", "get_news", "resolve_entity"],
  },
  US_MAPPING_ANALYSIS: {
    id: "us_mapping_analysis",
    name: "美股映射分析",
    description: "分析美股异动对A股的映射影响，包括映射维度、强度和投资机会",
    requiresEntity: true,
    isDynamic: true,
    defaultFlow: ["get_us_data", "find_us_mapping", "analyze_mapping_impact", "analyze_with_llm"],
    tools: ["get_us_data", "find_us_mapping", "analyze_mapping_impact", "get_stock_data", "get_news", "analyze_with_llm"],
  },
};

function formatMultiStockWallstreetData(wallstreetData) {
  if (!wallstreetData) return "无华尔街数据";

  let text = "";
  for (const [symbol, data] of Object.entries(wallstreetData)) {
    text += `\n### 🇺🇸 ${symbol} 华尔街分析师评级\n`;
    text += wallstreetDataService.formatForLLM(data);
  }

  return text || "无华尔街数据";
}

async function generateAIAnalysis(context, customPrompt = null) {
  const stock = context.data.stockEntity || {};
  const data = context.data.instrumentData || {};
  const news = context.data.news || context.data.latestNews || [];
  const events = context.data.events || [];
  const memoryContextText = context.data.memoryContextText || "无历史记忆";
  const userQuery = context.userQuery || "";
  const taskType = context.currentTaskType || "general";
  
  // 获取当前时间和数据日期
  const now = new Date();
  const currentDate = now.toLocaleDateString("zh-CN");
  const currentTime = now.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
  const dataDate = data.latestDate || currentDate;
  
  // 检查数据是否为空，构建数据完整性提示
  const dataWarnings = [];
  if (!data.latestPrice && !context.data.topGainers?.length && !context.data.topLosers?.length) {
    dataWarnings.push("⚠️ 当前未获取到实时行情数据，以下分析基于有限信息，请勿编造具体涨跌幅数据。");
  }
  if (data.latestDate) {
    const dataAgeDays = Math.floor((now - new Date(data.latestDate)) / (24 * 60 * 60 * 1000));
    if (dataAgeDays > 3) {
      dataWarnings.push(`⚠️ 数据库最新数据日期为 ${data.latestDate}，距今已 ${dataAgeDays} 天，非实时数据。报告中必须如实标注此日期，不得使用当前日期替代。`);
    }
  }
  const dataWarningText = dataWarnings.length > 0 
    ? `\n\n【数据真实性要求（最高优先级）】\n${dataWarnings.join("\n")}\n- 绝对禁止编造任何未提供的数据（涨跌幅、价格、成交量等）\n- 如果数据为空或缺失，必须明确写"数据缺失"，不得臆测\n- 报告头部的"核心数据报告期"必须使用真实数据日期 ${dataDate}，不得使用当前日期\n`
    : "";
  
  let systemPrompt = "";

  switch (taskType) {
    case "chat":
      // 小白讲解：chat类型是追问模式，不需要生成全新报告，而是基于对话历史继续回答
      systemPrompt = `你是专业的A股投研助手。用户正在基于之前的对话进行追问或继续讨论。

【关键规则】
1. 你必须参考对话历史中的内容，理解用户在追问什么
2. 如果用户说"继续输出"、"没说完"等，请接着之前的分析继续写，不要重新生成一份全新的报告
3. 如果用户追问某个细节，请基于之前提到的数据展开分析
4. 保持与之前回答一致的分析框架和风格
5. 使用中文回答
6. 不要重复已经说过的内容，直接从截断处或新问题开始
7. 如果对话历史中已有某些数据，不要再写"数据缺失"，而是直接使用这些数据

【输出要求】
- 直接继续之前的内容，不需要重新写标题或报告框架
- 如果之前的内容被截断了，从截断处继续写完
- 如果用户问了新问题，基于对话历史中的数据来回答
- 如果对话历史中没有某个数据，简要提及即可，不要大篇幅渲染"数据缺失"`;
      break;
    case "multi_stock_comparison":
      systemPrompt = `你是顶级买方基金经理，请基于各子Agent的独立分析结果，进行横向对比分析并生成综合投资报告。使用中文。

【核心方法论：不要描述数据，要分析逻辑】
描述 = 复述数据（"营收XX亿，增长XX%"）
分析 = 解释数据背后的逻辑（"营收增长主要来自XX产品放量，反映XX趋势，意味着XX"）

【报告元信息要求】
必须在报告开头写明以下信息（每行一个）：
- 数据截至：${currentDate} ${currentTime}
- 核心数据报告期：${dataDate}
- 观点有效期：30个自然日（至 ${new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000).toLocaleDateString("zh-CN")}）

【数据处理规则】
1. 对于缺失的财务数据必须明确标注缺失，禁止估算或补造具体数值
2. 异常数据（如PE>200倍、PE为负）需标注"⚠️"并说明原因
3. 如果子Agent分析中包含了Tavily搜索到的分析师目标价/评级，必须引用
4. 绝对禁止脱离市场预期凭空给出目标价——必须基于市场一致预期+预期差分析
5. 【东方财富数据横向对比规则】各子Agent提供了资金流向+龙虎榜+多季度财务趋势+券商研报：
   - 横向对比矩阵必须新增"主力资金净流向（5日）"、"营收同比最新vs上期"、"券商研报买入比例"三列
   - 在"市场共识分析"中，对每只标的的资金面给出明确判断（机构建仓/出货/分歧）
   - 在"预期差分析"中，对比"业绩趋势（加速/减速）"与"资金动向（流入/流出）"，识别背离信号
   - 多季度财务趋势加速的标的，若同时资金净流入，是高确定性看多信号
   - 业绩加速但资金流出的标的，需提示"基本面与资金面背离"风险
   - 券商研报买入比例高（>70%）且评级上调的标的，市场共识偏正面
   - 一致预期EPS/PE可作为横向估值对比的锚点

【输出结构要求】（严格按以下顺序输出）

## 一、横向对比矩阵
用表格形式对比所有标的的关键指标：
| 指标 | 标的A | 标的B | ... |
| PE(TTM) | | | |
| PB | | | |
| PS(TTM) | | | |
| 市值 | | | |
| 营收 | | | |
| 净利润 | | | |
| 毛利率 | | | |
| 净利率 | | | |
| ROE | | | |
| 5日涨跌 | | | |
| 20日涨跌 | | | |
| 历史估值分位 | | | |
| 主力资金5日净流向 | | | |  ← 来自东方财富
| 营收同比最新 | | | |  ← 来自东方财富
| 营收同比上期 | | | |  ← 来自东方财富
| 券商研报买入比例 | | | |  ← 来自东方财富
| 一致预期明年EPS | | | |  ← 来自东方财富
| 分析师目标价（如有）| | | |

## 二、各标的市场共识分析
对每只标的分别分析：
- 当前股价反映了什么预期？（用估值历史分位倒推：分位>80%=高预期，<20%=低预期）
- 市场主流观点是什么？（从子Agent的新闻/研报/评级信息提取）
- 分析师一致目标价是多少？（如果子Agent搜到了，必须引用）

## 三、预期差分析（核心！）
对每只标的分别分析：
- 我们与市场共识的分歧在哪？
- 哪些是高确定性的？哪些可能有偏差？
- 预期差方向（偏多/偏空）和幅度

## 四、投资逻辑对比
- 各标的的核心赌点是什么？（1-2个，如"赌AI算力capex超预期"）
- 哪些赌点当前已price in？哪些还没有？
- 在当前时点，哪个标的的性价比最高？为什么？

## 五、多情景分析
对每只标的给出三种情景：
- 乐观情景（概率XX%）：目标价XX，触发条件
- 中性情景（概率XX%）：目标价XX，触发条件
- 悲观情景（概率XX%）：目标价XX，触发条件
注意：目标价必须参考市场一致预期（如果搜到了分析师目标价）

## 六、风险提示
- 共同风险（行业性、宏观性）
- 各标的特有风险

## 七、综合投资建议
对每只标的分别给出：
- 当前建议：买入/持有/卖出/观望（明确一个）
- 建议仓位（如5-10%）
- 目标价区间（基于市场预期+预期差分析，标注当前价位置）
- 加仓触发条件（2-3个具体条件）
- 减仓/止损触发条件（2-3个）
- 关键观察指标（1-2个核心指标）

## 八、核心结论（3-5句话总结，必须回答：当前时点最该买谁/持有谁/卖出谁）`;
      break;
    case "stock_deep_analysis":
      systemPrompt = `你是专业股票研究分析师，请基于以下真实数据进行深度分析。使用中文，结论先行，输出格式清晰。

【报告元信息要求】
必须在报告开头写明以下信息（每行一个）：
- 数据截至：${currentDate} ${currentTime}
- 核心数据报告期：${dataDate}
- 观点有效期：30个自然日（至 ${new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000).toLocaleDateString("zh-CN")}）

【数据处理规则】
1. 对于缺失的财务数据必须明确标注缺失，禁止估算或补造具体数值
2. 异常数据（如PE>200倍、PE为负）需标注"⚠️"并说明原因
3. 【东方财富数据使用规则】资金流向+龙虎榜+财务趋势+券商研报是核心硬证据，必须在分析中引用：
   - 资金流向反映"聪明钱"动向：主力净流入连续为正=机构建仓，连续为负=机构出货
   - 龙虎榜机构席位净买入=机构看好，净卖出=机构撤退
   - 多季度财务趋势是判断"加速增长"还是"减速增长"的硬证据，必须引用最新一期和上期的同比对比
   - 券商研报反映"卖方共识"：买入/增持比例高=市场看好，评级集中上调=预期改善
   - 一致预期EPS/PE是估值锚点，必须与当前估值对比，判断高估/低估
   - 资金面与基本面背离时（如业绩加速但资金流出），必须明确提示背离信号

输出结构要求：
- 投资摘要（3-5句话总结核心结论）
- 核心观点（各维度评级：估值、基本面、技术面、催化剂）
- 详细分析（基于提供的数据，必须引用资金流向、财务趋势、券商研报）
- 风险提示
- 投资建议（必须包含以下内容）：
  * 当前建议：买入/持有/卖出（明确一个）
  * 加仓触发条件（2-3个具体条件，如"PE跌破XX倍"、"Q2利润增长超XX%"）
  * 减仓触发条件（2-3个具体条件）
  * 关键观察指标（需要持续跟踪的1-2个核心指标）`;
      break;
    case "opportunity_scan":
      systemPrompt = `你是专业投资机会扫描员，请基于以下市场数据扫描投资机会。使用中文，结论先行。

【报告元信息要求】
必须在报告开头写明以下信息（每行一个）：
- 数据截至：${currentDate} ${currentTime}
- 核心数据报告期：${dataDate}
- 观点有效期：5个交易日（至 ${new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000).toLocaleDateString("zh-CN")}）

输出结构要求：
- 市场概览（整体市场情绪）
- 机会清单（最多5只，按优先级排序；每只写清信号、反证、观察条件，不把单日涨停直接等同于机会）
- 风险提示
- 操作建议

【机会筛选硬约束】
1. 名称含 ST、*ST、退市或以“退”结尾的标的，只能列入风险观察，严禁列入可操作机会。
2. 量比缺失时，高换手只能描述为“成交活跃/高换手”，严禁表述为“放量”。
3. 估值或新闻证据过期时，只能作为历史背景，不得支撑当前买卖建议。
4. 对每个候选给出“为什么值得跟踪”和“什么条件下放弃”，不输出无依据的目标价。`;
      break;
    case "risk_analysis":
      systemPrompt = `你是专业风险分析师，请基于以下数据识别和评估风险。使用中文，结论先行。

【报告元信息要求】
必须在报告开头写明以下信息（每行一个）：
- 数据截至：${currentDate} ${currentTime}
- 核心数据报告期：${dataDate}
- 观点有效期：15个自然日（至 ${new Date(now.getTime() + 15 * 24 * 60 * 60 * 1000).toLocaleDateString("zh-CN")}）

输出结构要求：
- 风险概览（主要风险类型）
- 风险详情（每个风险的概率和影响）
- 风险评级
- 应对建议`;
      break;
    case "daily_brief":
      systemPrompt = `你是专业投资简报撰写员，请基于以下数据撰写每日简报。使用中文，简洁明了。

【报告元信息要求】
必须在报告开头写明以下信息（每行一个）：
- 数据截至：${currentDate} ${currentTime}
- 核心数据报告期：${dataDate}
- 观点有效期：当日有效

输出结构要求：
- 市场概览
- 涨幅榜/跌幅榜要点
- 重要新闻
- 组合表现
- 明日关注`;
      break;
    default:
      systemPrompt = `你是专业股票研究分析师，请基于以下真实数据进行分析。使用中文，结论先行，输出格式清晰。

【报告元信息要求】
必须在报告开头写明以下信息（每行一个）：
- 数据截至：${currentDate} ${currentTime}
- 核心数据报告期：${dataDate}
- 观点有效期：30个自然日（至 ${new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000).toLocaleDateString("zh-CN")}）

输出结构要求：
- 投资摘要（3-5句话总结核心结论）
- 核心观点（各维度评级）
- 详细分析（基于提供的数据）
- 风险提示
- 投资建议`;
  }
  
  // 注入数据真实性警告（如果有）
  if (dataWarningText) {
    systemPrompt += dataWarningText;
  }

  const evidenceCatalog = context.data.evidenceCatalog || [];
  const dataHealth = context.data.dataHealth || summarizeDataHealth(evidenceCatalog);
  if (evidenceCatalog.length > 0) {
    systemPrompt += `

【证据引用规则（最高优先级）】
1. 所有行情数字、涨跌幅、日期、新闻事实和估值判断，都必须在相关句末引用对应证据编号，例如 [E001]
2. 只允许引用下方证据目录中真实存在的编号，禁止虚构证据
3. freshness=stale、missing、undated 或 fetch_failed 的证据不得支撑“今天”“当前”“实时”等表述
4. 如果“是否允许声称当前/今日”为否，必须把结论降级为历史数据回顾或待核验线索，不得给出基于当期行情的操作建议
5. market_observation 代表盘中或收盘后的实时观察，不等于已完成日线；报告中要使用“抓取时观察到”措辞`;
  }
  
  let userPrompt = `## 用户问题
${userQuery}

## 分析数据`;

  // 多标对比模式（基于子Agent结果）
  if (taskType === "multi_stock_comparison" && context.data.subAgentResults) {
    const subResults = context.data.subAgentResults;
    userPrompt += `
### 子Agent独立分析结果（共 ${subResults.length} 只）`;
    
    for (const result of subResults) {
      const stockData = result.instrumentData || {};
      userPrompt += `

========== 【${result.stockEntity?.name || result.ticker}（${result.ticker}）】 ==========

【单标深度分析摘要】
${result.analysis ? result.analysis.substring(0, 4000) : "无分析结果"}${result.analysis && result.analysis.length > 4000 ? "\n...（后续内容省略）" : ""}

【关键数据】
行业：${result.stockEntity?.sector || stockData.sector || "未知"}
最新价：${stockData.latestPrice || "无数据"}
PE(TTM)：${stockData.valuation?.pe ?? "N/A"}
PB：${stockData.valuation?.pb ?? "N/A"}
PS(TTM)：${stockData.valuation?.ps ?? "N/A"}
市值：${stockData.valuation?.marketCap ?? "N/A"}
营收：${stockData.fundamentals?.revenue ?? "N/A"}
净利润：${stockData.fundamentals?.netIncome ?? "N/A"}
毛利率：${stockData.fundamentals?.grossMargin != null ? (stockData.fundamentals.grossMargin * 100).toFixed(2) + "%" : "N/A"}
净利率：${stockData.fundamentals?.netMargin != null ? (stockData.fundamentals.netMargin * 100).toFixed(2) + "%" : "N/A"}
ROE：${stockData.fundamentals?.roe != null ? (stockData.fundamentals.roe * 100).toFixed(2) + "%" : "N/A"}
5日涨跌：${stockData.momentum?.m5d != null ? stockData.momentum.m5d.toFixed(2) + "%" : "N/A"}
20日涨跌：${stockData.momentum?.m20d != null ? stockData.momentum.m20d.toFixed(2) + "%" : "N/A"}
RSI(14)：${stockData.technical?.rsi14 ?? "N/A"}
历史分位数(1年)：${stockData.valuation?.historicalPercentile1y ?? "N/A"}%
同业分位数：${stockData.valuation?.peerPercentile ?? "N/A"}%
同业标的：${stockData.peers?.join("、") || "无"}
海外对标：${stockData.usBenchmarks?.join("、") || "无"}

【东方财富增强数据】（资金动向+多季度财务趋势+券商研报）
${result.eastmoneyData ? eastmoneyDataService.formatForLLM(result.eastmoneyData) : "（无数据）"}

【华尔街数据】（海外对标分析师评级+目标价）
${result.wallstreetData ? formatMultiStockWallstreetData(result.wallstreetData) : "（无数据）"}`;
    }
  } else if (stock.name) {
    userPrompt += `
### 股票信息
名称：${stock.name}
代码：${stock.tsCode || context.data.currentTicker}
行业：${stock.sector || "未知"}`;
  }
  
  if (data.latestPrice && taskType !== "multi_stock_comparison") {
    userPrompt += `
### 最新行情
最新价：${data.latestPrice}
数据日期：${data.latestDate || "未知"}
5日涨跌：${data.momentum?.m5d != null ? data.momentum.m5d.toFixed(2) + "%" : "无数据"}
20日涨跌：${data.momentum?.m20d != null ? data.momentum.m20d.toFixed(2) + "%" : "无数据"}`;
  }
  
  if (data.valuation && taskType !== "multi_stock_comparison") {
    userPrompt += `
### 估值数据
${JSON.stringify(data.valuation, null, 2)}`;
  }
  
  if (data.fundamentals && taskType !== "multi_stock_comparison") {
    userPrompt += `
### 基本面数据
${JSON.stringify(data.fundamentals, null, 2)}`;
  }
  
  if (data.technical && taskType !== "multi_stock_comparison") {
    userPrompt += `
### 技术面数据
RSI(14): ${data.technical.rsi14 ?? "无数据"}
MACD DIF: ${data.technical.macdDif ?? "无数据"}
MA20: ${data.technical.ma20 ?? "无数据"}`;
  }

  // 东方财富增强数据（单标模式）
  if (context.data.eastmoneyData && taskType !== "multi_stock_comparison") {
    userPrompt += `

### 东方财富增强数据（资金动向+财务趋势+券商研报，高价值）
${eastmoneyDataService.formatForLLM(context.data.eastmoneyData)}`;
  }
  
  // 注入大盘指数数据（解决"大盘指数数据缺失"的问题）
  if (context.data.marketIndices?.length) {
    userPrompt += `

### 大盘指数（实时）
${context.data.marketIndices.map(idx => `- ${idx.name}：${idx.price}点，涨跌幅 ${idx.pct_chg >= 0 ? "+" : ""}${idx.pct_chg}%，成交额 ${idx.amount}亿元`).join("\n")}`;
  } else if (taskType === "opportunity_scan" || taskType === "daily_brief") {
    userPrompt += `

### 大盘指数
⚠️ 数据缺失：未获取到大盘指数数据`;
  }

  if (news.length > 0) {
    userPrompt += `
### 近期新闻（共 ${news.length} 条）
${news.slice(0, 5).map((n, i) => `${i+1}. [${n.published_at?.substring(0, 10)}] ${n.source_name}: ${n.title}`).join("\n")}`;
  }
  
  if (memoryContextText && memoryContextText !== "无历史记忆") {
    userPrompt += `
### 历史研究记忆
${memoryContextText}`;
  }
  
  if (context.data.topGainers?.length) {
    const investableGainers = context.data.topGainers.filter(opportunityCandidate);
    userPrompt += `
### 原始涨幅榜（仅用于市场观察，不等于投资建议；数据日期：${context.data.topGainers[0]?.trade_date || dataDate}）
${context.data.topGainers.slice(0, 10).map((s, i) => `${i+1}. ${s.name || STOCK_NAME_MAP[s.ts_code] || s.ts_code}(${s.ts_code}): ${s.pct_chg?.toFixed(2)}%${s.amount ? `，成交额${(s.amount/10000).toFixed(2)}亿` : ""}${s.turnover ? `，换手${s.turnover.toFixed(2)}%` : ""}`).join("\n")}`;
    if (taskType === "opportunity_scan") {
      userPrompt += `
### 初筛可跟踪候选（已排除 ST/退市整理股，仍需结合证据二次判断）
${investableGainers.slice(0, 8).map((s, i) => `${i+1}. ${s.name || s.ts_code}(${s.ts_code})：涨跌 ${s.pct_chg?.toFixed(2)}%，换手 ${s.turnover?.toFixed(2) || "N/A"}%`).join("\n") || "无"}`;
    }
  } else if (taskType === "opportunity_scan" || taskType === "daily_brief") {
    userPrompt += `
### 涨幅榜
⚠️ 数据缺失：未获取到涨幅榜数据（数据库可能无最新交易日数据）`;
  }

  if (context.data.topLosers?.length) {
    userPrompt += `
### 跌幅榜（数据日期：${context.data.topLosers[0]?.trade_date || dataDate}）
${context.data.topLosers.slice(0, 10).map((s, i) => `${i+1}. ${s.name || STOCK_NAME_MAP[s.ts_code] || s.ts_code}(${s.ts_code}): ${s.pct_chg?.toFixed(2)}%${s.amount ? `，成交额${(s.amount/10000).toFixed(2)}亿` : ""}${s.turnover ? `，换手${s.turnover.toFixed(2)}%` : ""}`).join("\n")}`;
  } else if (taskType === "opportunity_scan" || taskType === "daily_brief") {
    userPrompt += `
### 跌幅榜
⚠️ 数据缺失：未获取到跌幅榜数据`;
  }
  
  if (context.data.valuationExtremes?.length) {
    // 修复：过滤掉PE和分位数为null的无效数据，避免LLM编造数据
    // 小白讲解：如果估值数据里PE和分位数都是空的，说明没有有效数据，
    // 不能直接传给LLM，否则它会自己编造"腾讯PE 17.9"这种假数据
    const validValuations = context.data.valuationExtremes.filter(
      s => (s.pe_ttm != null && s.pe_ttm > 0) || s.historical_percentile != null
    );
    if (validValuations.length > 0) {
      // 修复：字段名用 ts_code（getValuationExtremes已重命名），
      // historical_percentile 是 0-1 的小数（如 0.0516 = 5.16%），需要乘以100显示
      userPrompt += `
### 估值极端标的
${validValuations.slice(0, 5).map((s, i) => {
  const name = STOCK_NAME_MAP[s.ts_code] || s.ts_code;
  const pe = s.pe_ttm != null ? s.pe_ttm.toFixed(2) : "N/A";
  // historical_percentile 是 0-1 小数，乘以100转成百分比
  const pctRaw = s.historical_percentile;
  const pct = pctRaw != null ? (pctRaw <= 1 ? (pctRaw * 100).toFixed(2) : pctRaw.toFixed(2)) : "N/A";
  const pb = s.pb != null ? s.pb.toFixed(2) : "N/A";
  const price = s.current_price != null ? s.current_price.toFixed(2) : "N/A";
  return `${i+1}. ${name}(${s.ts_code}): PE ${pe}, PB ${pb}, 历史分位 ${pct}%, 现价 ${price}`;
}).join("\n")}
⚠️ 注意：以上估值数据来自数据库历史快照（generated_at字段所示日期），可能不是当日实时数据。在报告中引用时请明确数据日期，不要编造任何未列出的估值数据。`;
    } else {
      userPrompt += `
### 估值极端标的
⚠️ 估值数据缺失：数据库中无有效的估值数据（PE、历史分位等均为空），请在报告中明确说明"估值数据缺失"，不得编造任何PE、PB或分位数数据。`;
    }
  }
  
  if (context.data.volumeSurge?.length) {
    const activityTitle = context.data.volumeSurgeMode === "turnover" ? "高换手异动（量比不可用，非放量结论）" : "放量异动";
    userPrompt += `
### ${activityTitle}（数据日期：${context.data.volumeSurge[0]?.trade_date || dataDate}）
${context.data.volumeSurge.slice(0, 5).map((s, i) => `${i+1}. ${s.name || STOCK_NAME_MAP[s.ts_code] || s.ts_code}(${s.ts_code}): ${s.activity_signal === "volume_ratio" ? `量比 ${s.volume_ratio?.toFixed(2)}` : `换手 ${s.turnover?.toFixed(2) || "N/A"}%`}，涨跌 ${s.pct_chg?.toFixed(2)}%`).join("\n")}`;
  }

  if (context.data.priceMovement?.length) {
    userPrompt += `
### 价格异动（数据日期：${context.data.priceMovement[0]?.trade_date || dataDate}）
${context.data.priceMovement.slice(0, 5).map((s, i) => `${i+1}. ${s.name || STOCK_NAME_MAP[s.ts_code] || s.ts_code}(${s.ts_code}): ${s.pct_chg?.toFixed(2)}%${s.amount ? `，成交额${(s.amount/10000).toFixed(2)}亿` : ""}`).join("\n")}`;
  }
  
  if (customPrompt) {
    userPrompt += `
### 分析指引
${customPrompt}`;
  }

  if (evidenceCatalog.length > 0) {
    userPrompt += `

### 数据健康与证据目录
${formatEvidenceCatalogForPrompt(evidenceCatalog, dataHealth)}`;
  }
  
  userPrompt += `
请基于以上真实数据进行深度分析。如果数据缺失，请如实说明，不要编造。`;

  // 构建消息列表，注入对话历史（让 LLM 知道之前聊了什么）
  // 小白讲解：就像跟人聊天时，先告诉他"我们之前聊了这些"，
  // 这样他才能理解你现在的追问是什么意思
  const llmMessages = [{ role: "system", content: systemPrompt }];

  // 注入对话历史（如果有）
  // 小白讲解：把之前的聊天记录告诉LLM，这样它才能理解你的追问
  const chatHistory = context.chatHistory || [];
  if (chatHistory.length > 0) {
    // 最多注入最近 6 条历史消息，避免 prompt 太长
    const recentHistory = chatHistory.slice(-6);
    for (const msg of recentHistory) {
      if (msg.role === "user" || msg.role === "assistant") {
        // 修复：用户消息保留 200 字，助手消息保留 1500 字
        // 之前 300 字太短，助手的长报告被裁剪后 LLM 无法理解上下文
        const maxLen = msg.role === "user" ? 200 : 1500;
        llmMessages.push({
          role: msg.role,
          content: msg.content.substring(0, maxLen),
        });
      }
    }
  }

  llmMessages.push({ role: "user", content: userPrompt });

  const result = await createChatCompletion(
    llmMessages,
    { maxTokens: 16000, temperature: 0.7, timeoutMs: 240000 }
  );
  
  let content = result.content || "";
  content = content.replace(/_x000A_/g, "\n");
  return { rawAnalysis: content, usage: result.usage };
}

async function planWorkflowByLLM(userQuery, availableTools, context) {
  if (!isModelAvailable()) return null;
  
  const toolsList = availableTools.map(t => 
    `{ toolId: "${t.toolId}", name: "${t.name}", description: "${t.description}" }`
  ).join("\n");
  
  const contextSummary = context.data.stockEntity 
    ? `当前上下文：已识别股票 ${context.data.stockEntity.name}(${context.data.stockEntity.tsCode})`
    : "当前上下文：无";
  
  const prompt = `## 用户问题
${userQuery}

## 当前上下文
${contextSummary}

## 可用工具
${toolsList}

请分析用户问题，确定需要调用哪些工具以及调用顺序。

输出格式（JSON）：
{
  "taskType": "任务类型ID",
  "flow": ["工具ID1", "工具ID2", ...],
  "reasoning": "你的分析和规划理由"
}

注意：
1. flow 中的工具必须按逻辑顺序排列
2. 如果需要多个工具，按依赖关系排序（先解析实体，再获取数据，最后分析）
3. 如果不需要工具，可以返回空数组
4. 工具ID必须从可用工具中选择`;
  
  const result = await createChatCompletion(
    [{ role: "system", content: "你是一个智能流程规划师，负责根据用户问题规划最佳执行流程。" }, { role: "user", content: prompt }],
    { maxTokens: 1000, temperature: 0.5 }
  );
  
  try {
    const jsonStr = result.content.match(/\{[\s\S]*\}/)?.[0];
    return jsonStr ? JSON.parse(jsonStr) : null;
  } catch (e) {
    return null;
  }
}

export class WorkflowEngine {
  constructor({
    onEvent = null,
    runId = null,
    governedWorkflowRunner = null,
    onResearchProgress = null,
    sessionId = null,
    sessionStateStore = null,
    taskRouterV2 = null,
  } = {}) {
    this.context = {
      data: {},
      history: [],
      workflowState: "idle",
      stepIndex: 0,
      currentTaskType: null,
      input: {},
      currentInput: {},
      governedWorkflowRunner,
      onResearchProgress: typeof onResearchProgress === "function" ? onResearchProgress : null,
    };
    this.executionHistory = [];
    this.currentFlow = [];
    this.executionStats = { totalSteps: 0, completedSteps: 0, failedSteps: 0, skippedSteps: 0 };
    this.maxReplans = Math.max(0, Number.parseInt(process.env.WORKFLOW_MAX_REPLANS || "0", 10) || 0);
    this.replanCount = 0;
    this.onEvent = typeof onEvent === "function" ? onEvent : null;
    this.runId = runId;
    this.evidenceSequence = 0;
    this.sessionId = sessionId;
    this.sessionStateStore = sessionStateStore;
    this.sessionState = null; // ResearchSessionState 实例，懒加载
    // === 任务图注册表与 V2 路由器 ===
    // 小白讲解：这是"菜单"和"翻译官"。
    // 菜单上列出了系统支持的所有研究任务，
    // 翻译官把用户说的话翻译成菜单上的一道菜。
    this.taskGraphRegistry = createDefaultRegistry();
    this.taskRouterV2 = taskRouterV2 || new ConversationTaskRouterV2({
      registry: this.taskGraphRegistry,
      llmRouter: createRegistryLlmRouter(this.taskGraphRegistry),
    });
  }

  async processUserQuery(userQuery, chatHistory = []) {
    this.context.userQuery = userQuery;
    this.context.workflowState = "analyzing";
    this.context.chatHistory = chatHistory; // 保存对话历史，供后续 LLM 调用使用
    this.executionHistory = [];
    this.currentFlow = [];
    this.replanCount = 0;
    this.evidenceSequence = 0;
    this.context.data.evidenceCatalog = [];
    this.context.data.evidenceIds = [];
    // 没有执行数据工具的自由对话不应被误标为“数据不足”。首次形成证据时再生成健康结论。
    this.context.data.dataHealth = null;
    Object.defineProperty(this.context.data, "evidenceSnapshots", {
      value: [], writable: true, configurable: true, enumerable: false,
    });
    
    // === 加载研究会话状态 ===
    // 小白讲解：每次处理用户查询前，先从"记忆笔记本"恢复上一轮的状态。
    // 这样"继续""那第二个呢"等追问才能继承上下文。
    await this._loadSessionState();
    this.context.sessionState = this.sessionState;

    this.addLog("system", `开始处理用户查询: "${userQuery}"`);

    const analysisResult = await this.analyzeAndPlan(userQuery);
    if (!analysisResult) {
      this.addLog("system", "无法分析用户意图，使用默认流程");
      const result = await this.executeDefaultFlow(userQuery);
      await this._saveSessionState(result);
      return result;
    }

    this.currentTaskType = analysisResult.taskType;
    this.context.currentTaskType = analysisResult.taskType;
    this.currentFlow = analysisResult.taskType === "stock_deep_analysis"
      ? [...TASK_TYPES.STOCK_DEEP_ANALYSIS.defaultFlow]
      : analysisResult.flow;

    this.addLog("system", `规划流程: ${this.currentFlow.join(" → ")}`);
    this.addLog("system", `规划理由: ${analysisResult.reasoning}`);

    const result = await this.executeFlow(this.currentFlow);
    await this._saveSessionState(result);
    return result;
  }

  async analyzeAndPlan(userQuery) {
    this.addLog("system", "开始意图分析与流程规划...");

    if (this.taskRouterV2) {
      try {
        const envelope = await this.taskRouterV2.route(userQuery, {
          sessionState: this.sessionState,
          chatHistory: this.context.chatHistory || [],
        });
        this.context.data.routingEnvelope = envelope;
        this.context.data.entities = envelope.entities || [];
        if (envelope.task_type !== "chat") {
          this.context.data.intent = {
            intent: envelope.task_type,
            intentName: envelope.name,
            entities: envelope.entities,
            requiredTools: envelope.flow,
            isDynamic: false,
            confidence: envelope.confidence,
            reasoning: envelope.reasoning,
            routingSource: envelope.routingTrace?.step || "router_v2",
          };
          this.addLog("system", `Router V2 命中任务图: ${envelope.task_type}`);
          return {
            taskType: envelope.task_type,
            flow: [...envelope.flow],
            reasoning: envelope.reasoning,
            intent: this.context.data.intent,
            relation: envelope.relation_to_previous,
            routingEnvelope: envelope,
          };
        }
      } catch (error) {
        this.addLog("system", `Router V2 失败，继续兼容路由: ${error.message}`);
      }
    }

    // === 关键修复：先检查是否是追问 ===
    // 小白讲解：如果用户说"继续"、"接着说"、"没输出完"等，
    // 说明是在追问上一轮对话的结果。
    // 修复前：直接把追问降级为 chat -> analyze_with_llm，丢失所有研究上下文。
    // 修复后：使用 resolveTaskRelation 解析追问关系，继承上一轮任务类型和实体。
    const chatHistory = this.context.chatHistory || [];
    if (isFollowUpQuestion(userQuery)) {
      this.addLog("system", "检测到追问，解析任务关系...");

      // 从会话状态中获取上一轮任务
      const previousTask = this.sessionState?.getCurrentTask() || null;

      if (previousTask) {
        const envelope = resolveTaskRelation(userQuery, previousTask);
        this.addLog("system", `追问关系: ${envelope.relation_to_previous}, 任务: ${envelope.task_type}`);

        // 根据关系类型决定流程
        if (envelope.relation_to_previous === "continue") {
          // 继续上一轮的研究任务
          const taskConfig = TASK_TYPES[envelope.task_type.toUpperCase()] ||
                           TASK_TYPES[envelope.task_type];
          if (taskConfig) {
            this.addLog("system", `继续研究任务: ${taskConfig.name}，继承实体: ${JSON.stringify(envelope.entities)}`);
            return {
              taskType: taskConfig.id,
              flow: [...taskConfig.defaultFlow],
              reasoning: envelope.reasoning || `继续上一轮${taskConfig.name}任务`,
              relation: "continue",
              previousTask,
            };
          }
        } else if (envelope.relation_to_previous === "derive") {
          // 从上一轮衍生出新任务
          const taskConfig = TASK_TYPES[envelope.task_type.toUpperCase()] ||
                           TASK_TYPES[envelope.task_type];
          if (taskConfig) {
            this.addLog("system", `派生新任务: ${taskConfig.name}，实体: ${JSON.stringify(envelope.entities)}`);
            return {
              taskType: taskConfig.id,
              flow: [...taskConfig.defaultFlow],
              reasoning: envelope.reasoning || `从上一轮任务派生`,
              relation: "derive",
              previousTask,
            };
          }
        } else if (envelope.relation_to_previous === "correct") {
          // 用户纠错，触发重新验证流程
          this.addLog("system", `用户纠错: ${JSON.stringify(envelope.correctionTarget)}`);
          return {
            taskType: "claim_correction",
            flow: ["resolve_entity", "get_stock_data", "run_governed_workflow"],
            reasoning: envelope.reasoning || "用户纠正上一轮数据，触发重新验证",
            relation: "correct",
            correctionTarget: envelope.correctionTarget,
            previousTask,
          };
        }
      }

      // 没有上轮任务或无法解析关系时，降级到通用聊天（但这是最后的回退）
      this.addLog("system", "追问但无上轮任务状态，回退到通用对话");
      return {
        taskType: "chat",
        flow: ["analyze_with_llm"],
        reasoning: "追问但无上轮任务上下文，回退到通用对话",
      };
    }

    // 产品首页的“涨跌幅归因分析”是高确定性入口。先于模型路由，避免被“今天”误分到每日简报。
    if (/(?:归因|原因)/.test(userQuery) && /涨/.test(userQuery) && /跌/.test(userQuery)) {
      const taskConfig = TASK_TYPES.MARKET_ATTRIBUTION;
      this.addLog("system", `高确定性规则匹配任务类型: ${taskConfig.name}`);
      return {
        taskType: taskConfig.id,
        flow: taskConfig.defaultFlow,
        reasoning: "用户明确要求涨跌榜归因，使用事实核对型确定性流程",
      };
    }

    if (isModelAvailable()) {
      try {
        initIntentEngine();
        this.addLog("system", "调用意图引擎进行自然语言理解...");
        // 修复：传入chatHistory让意图引擎理解上下文
        const intentResult = await intentEngine.parseIntent(userQuery, this.context, chatHistory);
        
        if (intentResult) {
          // The LLM is the semantic router, but it is not allowed to silently downgrade an
          // explicit, high-confidence product request to free chat.  The deterministic
          // detector acts as a route validator and availability fallback; this is internal
          // plumbing, not a command table the user has to learn.
          const validatedTaskKey = this.detectTaskType(userQuery);
          const validatedTask = validatedTaskKey === "CHAT" ? null : TASK_TYPES[validatedTaskKey];
          if (validatedTask && intentResult.intent !== validatedTask.id) {
            this.addLog(
              "system",
              `路由校验已纠偏: ${intentResult.intent || "unknown"} → ${validatedTask.id}`,
            );
            intentResult.intent = validatedTask.id;
            intentResult.intentName = validatedTask.name;
            intentResult.requiredTools = [...validatedTask.defaultFlow];
            intentResult.isDynamic = false;
            intentResult.routingSource = "llm_validated_by_deterministic_guard";
            intentResult.reasoning = `自然语言意图与高确定性入口校验后，匹配到任务类型: ${validatedTask.name}`;
          }
          this.context.data.intent = intentResult;
          this.addLog("system", `意图识别结果: ${intentResult.intentName}`);
          this.addLog("system", `识别实体: ${JSON.stringify(intentResult.entities)}`);
          
          if (intentResult.isDynamic && intentResult.requiredTools.length > 0) {
            this.addLog("system", `动态流程规划: ${intentResult.requiredTools.join(" → ")}`);
            if (intentResult.reasoning) this.addLog("system", `规划理由: ${intentResult.reasoning}`);
            
            return {
              taskType: intentResult.intent,
              flow: intentResult.requiredTools,
              reasoning: intentResult.reasoning,
              intent: intentResult,
            };
          }
          
          const taskConfig = TASK_TYPES[intentResult.intent.toUpperCase()] || 
                           TASK_TYPES[intentResult.intent];
          if (taskConfig) {
            this.addLog("system", `使用预设流程: ${taskConfig.defaultFlow.join(" → ")}`);
            return {
              taskType: taskConfig.id,
              flow: taskConfig.defaultFlow,
              reasoning: intentResult.reasoning || `匹配到任务类型: ${taskConfig.name}`,
              intent: intentResult,
            };
          }
        }
      } catch (error) {
        this.addLog("system", `意图引擎调用失败: ${error.message}，回退到规则匹配`);
      }
    }
    
    const detectedTask = this.detectTaskType(userQuery);
    const taskConfig = TASK_TYPES[detectedTask];
    
    if (taskConfig) {
      this.addLog("system", `规则匹配任务类型: ${taskConfig.name} (${detectedTask})`);
      this.addLog("system", `使用默认流程: ${taskConfig.defaultFlow.join(" → ")}`);
      return {
        taskType: taskConfig.id,
        flow: taskConfig.defaultFlow,
        reasoning: `根据规则匹配到任务类型: ${taskConfig.name}`,
      };
    }
    
    if (isModelAvailable()) {
      this.addLog("system", "未匹配到预设任务类型，调用 LLM 进行智能流程规划...");
      const availableTools = Object.values(AGENT_TOOLS);
      const plan = await planWorkflowByLLM(userQuery, availableTools, this.context);
      if (plan && plan.flow && plan.flow.length > 0) {
        this.addLog("system", `LLM 规划流程: ${plan.flow.join(" → ")}`);
        if (plan.reasoning) this.addLog("system", `规划理由: ${plan.reasoning}`);
        return plan;
      }
    }
    
    return null;
  }

  /**
   * 判断当前用户查询是否是追问
   *
   * 参数：
   *   userQuery: 用户当前输入
   *   chatHistory: 对话历史
   *
   * 返回：
   *   true=是追问, false=是新问题
   *
   * 小白讲解：
   *   这个函数就像一个"追问探测器"。
   *   当用户说"继续输出"、"接着说"、"没说完"、"补充一下"等，
   *   说明是在追问上一轮的对话结果，不需要重新走完整的数据收集流程，
   *   只需要让LLM基于上轮的上下文继续回答即可。
   *   这就是为什么之前第二轮对话完全不可用——系统把"继续输出"
   *   当成了全新的问题，重新走了完全不同的流程。
   */
  isFollowUpQuestion(userQuery, chatHistory) {
    // 小白讲解：现在追问检测委托给 research-task-contracts.js 中的函数。
    // 这个函数只判断"像不像追问"，不决定具体怎么处理。
    // 具体怎么处理（continue/derive/correct）由 analyzeAndPlan 中的 resolveTaskRelation 决定。
    // chatHistory 参数保留用于向后兼容，但不再作为必要条件
    // （追问检测现在基于关键词模式，不依赖历史长度）。
    return isFollowUpQuestion(userQuery);
  }

  // === 会话状态管理 ===

  /**
   * 加载研究会话状态
   *
   * 小白讲解：从数据库或内存中恢复上一轮的任务状态。
   * 如果没有 sessionId 或数据库，就创建一个空状态。
   */
  async _loadSessionState() {
    if (!this.sessionId) {
      this.sessionState = new ResearchSessionState("anonymous");
      return;
    }

    try {
      if (this.sessionStateStore) {
        const loaded = await this.sessionStateStore.load(this.sessionId);
        if (loaded) {
          this.sessionState = loaded;
          this.addLog("system", `已恢复会话状态: ${this.sessionId}`);
          return;
        }
      }

      // 没有持久化存储时，创建新状态
      this.sessionState = new ResearchSessionState(this.sessionId);
    } catch (error) {
      console.error("[WorkflowEngine] 加载会话状态失败:", error.message);
      this.sessionState = new ResearchSessionState(this.sessionId || "anonymous");
    }
  }

  /**
   * 保存研究会话状态
   *
   * 小白讲解：把当前任务的状态保存到数据库，
   * 这样下一轮对话时就能恢复上下文。
   * 只保存任务元数据，不保存临时假设。
   */
  async _saveSessionState(result) {
    if (!this.sessionState) return;

    try {
      // 从执行结果中提取任务信息
      const currentTask = {
        taskId: this.runId || `task_${Date.now()}`,
        taskType: this.currentTaskType || "chat",
        entities: this.context.data.entities || [],
        topic: this.context.userQuery || null,
        confirmedFacts: this.sessionState.confirmedFacts || [],
        modelAssumptions: this.sessionState.modelAssumptions || [],
        artifactRefs: this.sessionState.artifactRefs || [],
        pendingQuestions: this.sessionState.pendingQuestions || [],
      };

      this.sessionState.setCurrentTask(currentTask);

      // 如果有证据目录，提取确认事实
      const evidenceCatalog = this.context.data.evidenceCatalog || [];
      for (const evidence of evidenceCatalog) {
        if (evidence.snapshot_sha256 && evidence.tool_id) {
          this.sessionState.addConfirmedFact({
            field: evidence.tool_id,
            value: evidence.snapshot_sha256,
            source: evidence.tool_id,
            evidenceId: evidence.evidence_id,
          });
        }
      }

      // 保存到数据库
      if (this.sessionStateStore) {
        await this.sessionStateStore.save(this.sessionState);
        this.addLog("system", `已保存会话状态: ${this.sessionState.sessionId}`);
      }

      // 将任务状态放入 context，供后续追问使用
      this.context.previousTaskState = currentTask;
    } catch (error) {
      console.error("[WorkflowEngine] 保存会话状态失败:", error.message);
    }
  }

  detectTaskType(userQuery) {
    const q = userQuery.toLowerCase().trim();
    
    // 检测是否包含多只股票（用于多标对比）- 使用 resolveMultipleTickers 来支持代码和名称匹配
    const matchedTickers = resolveMultipleTickers(q);
    
    // 如果匹配到2只及以上股票，且意图是对比，返回多标对比
    if (matchedTickers.length >= 2) {
      const comparisonKeywords = ["对比", "比较", "vs", "versus", "哪个", "差别", "差异", "pk", "compare", "comparison", "全方位", "综合"];
      const hasComparisonIntent = comparisonKeywords.some(kw => q.includes(kw));
      if (hasComparisonIntent) {
        return "MULTI_STOCK_COMPARISON";
      }
    }
    
    for (const name of Object.values(STOCK_NAME_MAP)) {
      if (q.includes(name.toLowerCase())) {
        if (q.includes("分析") || q.includes("研究") || q.includes("怎么样") || q.includes("如何") || q.includes("analyze") || q.includes("research") || q.includes("how")) {
          return "STOCK_DEEP_ANALYSIS";
        }
        if (q.includes("评分") || q.includes("估值") || q.includes("vfm") || q.includes("价值") || q.includes("score") || q.includes("valuation") || q.includes("value")) {
          return "VALUE_SCORE";
        }
        if (q.includes("风险") || q.includes("risk")) {
          return "RISK_ANALYSIS";
        }
        if (q.includes("竞争对手") || q.includes("同业") || q.includes("对比") || q.includes("competitor") || q.includes("peer") || q.includes("compare")) {
          return "COMPETITOR_ANALYSIS";
        }
        if (q.includes("趋势") || q.includes("走势") || q.includes("技术") || q.includes("trend") || q.includes("technical")) {
          return "TREND_ANALYSIS";
        }
        if (q.includes("投资论") || q.includes("论点") || q.includes("更新") || q.includes("thesis")) {
          return "THESIS_UPDATE";
        }
        return "STOCK_DEEP_ANALYSIS";
      }
    }
    
    if ((q.includes("归因") || q.includes("原因")) && q.includes("涨") && q.includes("跌")) {
      return "MARKET_ATTRIBUTION";
    }
    if (q.includes("机会") || q.includes("雷达") || q.includes("推荐") || q.includes("选股") || q.includes("opportunity") || q.includes("scan") || q.includes("radar") || q.includes("recommend")) {
      return "OPPORTUNITY_SCAN";
    }
    if (q.includes("发现") || q.includes("新标的") || q.includes("候选") || q.includes("discover") || q.includes("new") || q.includes("candidate")) {
      return "DISCOVERY";
    }
    if (q.includes("新闻") || q.includes("消息") || q.includes("公告") || q.includes("news") || q.includes("announcement")) {
      return "MARKET_NEWS";
    }
    if (q.includes("组合") || q.includes("持仓") || q.includes("回顾") || q.includes("portfolio") || q.includes("review") || q.includes("position")) {
      return "PORTFOLIO_REVIEW";
    }
    if (q.includes("简报") || q.includes("日报") || q.includes("今日") || q.includes("brief") || q.includes("daily") || q.includes("today")) {
      return "DAILY_BRIEF";
    }
    if (q.includes("风险") || q.includes("分析风险") || q.includes("risk")) {
      return "RISK_ANALYSIS";
    }
    
    return "CHAT";
  }

  async executeDefaultFlow(userQuery) {
    this.addLog("system", "使用自由对话流程");
    return await this.executeFlow(["query_memory", "analyze_with_llm"]);
  }

  async executeFlow(flow) {
    this.context.workflowState = "executing";
    this.context.stepIndex = 0;

    const requestedFlow = Array.isArray(flow) ? [...flow] : [];
    const maxSteps = Math.max(1, Number.parseInt(process.env.WORKFLOW_MAX_STEPS || "12", 10) || 12);
    let currentFlow = [];
    let skippedSteps = 0;

    for (const toolId of requestedFlow) {
      if (WRITE_TOOL_IDS.has(toolId) && !isWriteToolAuthorized(toolId, this.context)) {
        skippedSteps += 1;
        this.addLog("system", `已跳过未授权写入工具: ${toolId}`);
        continue;
      }
      if (currentFlow.length >= maxSteps) {
        skippedSteps += requestedFlow.length - currentFlow.length - skippedSteps;
        this.addLog("system", `流程超过 ${maxSteps} 步上限，剩余步骤已跳过`);
        break;
      }
      currentFlow.push(toolId);
    }

    this.currentFlow = currentFlow;
    let completedSteps = 0;
    let failedSteps = 0;
    
    for (let i = 0; i < currentFlow.length; i++) {
      const toolId = currentFlow[i];
      this.context.stepIndex = i;
      
      const tool = AGENT_TOOLS[toolId];
      if (!tool) {
        this.addLog(toolId, `⚠️ 工具不存在: ${toolId}`);
        failedSteps += 1;
        continue;
      }
      
      this.addLog(toolId, `正在执行 [${i + 1}/${currentFlow.length}]: ${tool.name}...`);
      
      try {
        const result = await tool.execute(this.context);
        if (!result.skipEvidenceCapture) this.captureEvidence(toolId, result);
        
        if (result.success) {
          completedSteps += 1;
          this.addLog(toolId, `✓ ${tool.name} 完成`, result.data);
          
          if (
            this.context.data.intent?.isDynamic &&
            isModelAvailable() &&
            this.replanCount < this.maxReplans &&
            i < currentFlow.length - 1
          ) {
            try {
              initIntentEngine();
              const remainingTools = currentFlow.slice(i + 1);
              this.addLog("system", `动态规划中，检查是否需要调整剩余流程...`);
              
              this.replanCount += 1;
              const proposedTools = await intentEngine.replanFlow(toolId, this.context.data, remainingTools);
              const newRemainingTools = proposedTools
                .filter((candidateId) => AGENT_TOOLS[candidateId])
                .filter((candidateId) => !WRITE_TOOL_IDS.has(candidateId) || isWriteToolAuthorized(candidateId, this.context))
                .filter((candidateId, index, all) => all.indexOf(candidateId) === index)
                .slice(0, Math.max(0, maxSteps - i - 1));
              
              if (newRemainingTools.length !== remainingTools.length || 
                  newRemainingTools.some((t, idx) => t !== remainingTools[idx])) {
                this.addLog("system", `流程调整: ${remainingTools.join(" → ")} → ${newRemainingTools.join(" → ")}`);
                currentFlow = [...currentFlow.slice(0, i + 1), ...newRemainingTools];
              }
            } catch (replanError) {
              this.addLog("system", `动态规划调整失败，继续原流程: ${replanError.message}`);
            }
          }
        } else {
          failedSteps += 1;
          this.addLog(toolId, `✗ ${tool.name} 失败: ${result.message}`);
          if (toolId === "run_governed_stock_deep_dive") {
            this.context.data.finalResponse = `# 个股深度研究 V3 执行失败\n\n- ${result.message || "受治理研究内核未能完成。"}\n- 本次不使用旧研究逻辑生成替代结论，请修复数据或运行环境后重试。\n`;
            this.context.data.reportQualityGate = { passed: false, source: "stock_deep_dive_v3" };
          }
        }
      } catch (error) {
        failedSteps += 1;
        if (toolId !== "run_governed_stock_deep_dive") {
          this.captureEvidence(toolId, { success: false, data: null, message: error.message });
        } else {
          this.context.data.finalResponse = `# 个股深度研究 V3 执行失败\n\n- ${error.message}\n- 本次不使用旧研究逻辑生成替代结论，请修复数据或运行环境后重试。\n`;
          this.context.data.reportQualityGate = { passed: false, source: "stock_deep_dive_v3" };
        }
        this.addLog(toolId, `✗ ${tool.name} 异常: ${error.message}`);
      }
    }

    this.executionStats = {
      totalSteps: requestedFlow.length,
      completedSteps,
      failedSteps,
      skippedSteps,
    };
    if (currentFlow.length === 0 && skippedSteps > 0) {
      this.context.workflowState = "waiting_review";
    } else if (failedSteps === 0) {
      this.context.workflowState = "completed";
    } else if (completedSteps > 0) {
      this.context.workflowState = "partial";
    } else {
      this.context.workflowState = "failed";
    }
    return this.buildResult();
  }

  captureEvidence(toolId, result, capturedAt = new Date()) {
    const nextEvidenceId = `E${String(this.evidenceSequence + 1).padStart(3, "0")}`;
    const evidence = createEvidenceEnvelope({
      evidenceId: nextEvidenceId,
      toolId,
      result,
      capturedAt,
    });
    if (!evidence) return null;
    this.evidenceSequence += 1;
    if (!Array.isArray(this.context.data.evidenceSnapshots)) {
      Object.defineProperty(this.context.data, "evidenceSnapshots", {
        value: [], writable: true, configurable: true, enumerable: false,
      });
    }
    const snapshot = createEvidenceSnapshot({ evidence, result });
    evidence.snapshot_sha256 = snapshot.snapshot_sha256;
    this.context.data.evidenceSnapshots.push(snapshot);
    if (!Array.isArray(this.context.data.evidenceCatalog)) this.context.data.evidenceCatalog = [];
    this.context.data.evidenceCatalog.push(evidence);
    this.context.data.evidenceIds = this.context.data.evidenceCatalog.map((item) => item.evidence_id);
    this.context.data.dataHealth = summarizeDataHealth(this.context.data.evidenceCatalog);
    return evidence;
  }

  buildResult() {
    const data = this.context.data;
    
    let response = "";
    if (data.llmAnalysis?.rawAnalysis) {
      response = data.llmAnalysis.rawAnalysis;
    } else if (data.finalResponse) {
      response = data.finalResponse;
    } else {
      response = this.generateFallbackResponse();
    }
    
    // 修复Unicode换行符问题（_x000A_）
    response = response.replace(/_x000A_/g, "\n");
    data.citationValidation = data.governedWorkflow?.citationValidation || validateEvidenceCitations(
      response,
      data.evidenceCatalog || [],
      data.dataHealth || null,
    );
    if (this.currentTaskType === "opportunity_scan" && data.llmAnalysis?.rawAnalysis) {
      const currentViolations = data.citationValidation.current_claim_violations?.length || 0;
      const passed = response.length >= 800
        && data.citationValidation.coverage >= 0.75
        && currentViolations === 0;
      data.reportQualityGate = {
        passed,
        source: passed ? "llm" : "deterministic_fallback",
        minimum_characters: 800,
        minimum_citation_coverage: 0.75,
        llm_characters: response.length,
        llm_citation_coverage: data.citationValidation.coverage,
        llm_current_claim_violations: currentViolations,
      };
      if (!passed) {
        response = this.generateOpportunityFallbackResponse();
        data.citationValidation = validateEvidenceCitations(
          response,
          data.evidenceCatalog || [],
          data.dataHealth || null,
        );
      }
    } else if (this.currentTaskType === "opportunity_scan") {
      data.reportQualityGate = {
        passed: false,
        source: "deterministic_fallback",
        minimum_characters: 800,
        minimum_citation_coverage: 0.75,
      };
    } else if (this.currentTaskType === "daily_brief" && data.llmAnalysis?.rawAnalysis) {
      const currentViolations = data.citationValidation.current_claim_violations?.length || 0;
      const passed = response.length >= 900
        && data.citationValidation.coverage >= 0.75
        && currentViolations === 0;
      data.reportQualityGate = {
        passed,
        source: passed ? "llm" : "deterministic_fallback",
        minimum_characters: 900,
        minimum_citation_coverage: 0.75,
        llm_characters: response.length,
        llm_citation_coverage: data.citationValidation.coverage,
        llm_current_claim_violations: currentViolations,
      };
      if (!passed) {
        response = this.generateDailyBriefFallbackResponse();
        data.citationValidation = validateEvidenceCitations(
          response,
          data.evidenceCatalog || [],
          data.dataHealth || null,
        );
      }
    } else if (
      ["stock_analysis", "stock_deep_analysis"].includes(this.currentTaskType)
      && data.llmAnalysis?.rawAnalysis
      && !data.governedWorkflow
    ) {
      const currentViolations = data.citationValidation.current_claim_violations?.length || 0;
      const passed = response.length >= 1_000
        && data.citationValidation.coverage >= 0.75
        && currentViolations === 0;
      data.reportQualityGate = {
        passed,
        source: passed ? "llm" : "deterministic_fallback",
        minimum_characters: 1_000,
        minimum_citation_coverage: 0.75,
        llm_characters: response.length,
        llm_citation_coverage: data.citationValidation.coverage,
        llm_current_claim_violations: currentViolations,
      };
      if (!passed) {
        response = this.generateStockResearchFallbackResponse();
        data.citationValidation = validateEvidenceCitations(
          response,
          data.evidenceCatalog || [],
          data.dataHealth || null,
        );
      }
    }
    
    // Memories must come from the response that actually passed the report gate.
    // Never persist facts from a rejected model draft.
    let extractedMemories = data.extractedMemories || [];
    if (response && extractedMemories.length === 0 && !data.governedWorkflow) {
      extractedMemories = this.extractStructuredMemories(response);
      data.extractedMemories = extractedMemories;
    }
    
    return {
      taskType: this.currentTaskType,
      status: this.context.workflowState,
      executionHistory: this.executionHistory,
      response,
      extractedMemories,
      data: this.context.data,
      workflowSummary: this.generateWorkflowSummary(),
    };
  }

  /**
   * 从分析报告中提取结构化记忆
   *
   * 功能：把大段的分析报告拆分成一条条有分类的记忆卡片，
   *       方便后续搜索和复用。
   *
   * 参数：
   *   analysis: 完整的分析报告文本（Markdown 格式）
   *
   * 返回：
   *   记忆数组，每条包含 title / content / category / confidence
   *
   * 小白讲解：
   *   这个方法就像一个"图书管理员"，把一整篇报告
   *   按照不同的主题（市场分析、机会发现、风险提示、投资建议等）
   *   拆分成一张张卡片，分门别类地放好。
   *
   *   之前的版本有两个大问题：
   *   1. 前面的精确匹配规则太严格（要求"投资建议："这种格式），
   *      实际报告里几乎碰不到，导致全走 fallback
   *   2. fallback 只匹配5种固定标题，其他的全归为"分析结论"，
   *      所以用户看到的记忆全是"分析结论"分类
   *
   *   现在的改进：
   *   1. 先按 Markdown 标题（## ###）把报告切成章节
   *   2. 用一张"分类关键词表"智能判断每个章节属于哪一类
   *   3. 分类覆盖更广（14 种分类），不再只有 5 种
   *   4. 每个章节里的要点还可以进一步拆分成多条记忆
   *   5. 内容太短的（<30字）不提取，避免噪声
   */
  extractStructuredMemories(analysis) {
    if (!analysis || typeof analysis !== "string") return [];

    const memories = [];

    // ========== 分类关键词表 ==========
    // 小白讲解：这张表告诉程序，看到什么关键词就归到哪一类。
    // 匹配顺序很重要，越靠前的优先级越高（比如"核心结论"比"市场分析"优先级高）
    const categoryRules = [
      {
        category: "核心观点",
        keywords: ["核心观点", "核心结论", "投资摘要", "核心判断", "主要结论", "总结", "结论与建议"],
        confidence: 0.9,
      },
      {
        category: "投资建议",
        keywords: ["投资建议", "操作建议", "配置建议", "当前建议", "交易策略", "操作策略", "仓位建议"],
        confidence: 0.9,
      },
      {
        category: "风险提示",
        keywords: ["风险提示", "风险分析", "主要风险", "风险概览", "风险因素", "潜在风险", "风险点"],
        confidence: 0.85,
      },
      {
        category: "机会发现",
        keywords: ["机会清单", "机会扫描", "投资机会", "机会雷达", "重点关注", "潜力标的", "机会分析"],
        confidence: 0.85,
      },
      {
        category: "涨跌幅分析",
        keywords: ["涨幅榜", "跌幅榜", "涨跌幅", "领涨", "领跌", "涨停", "跌停"],
        confidence: 0.8,
      },
      {
        category: "估值分析",
        keywords: ["估值", "估值分析", "估值极端", "估值锚定", "估值判断", "PE", "PB", "历史分位", "估值水平"],
        confidence: 0.8,
      },
      {
        category: "量价分析",
        keywords: ["放量", "成交量", "成交额", "量价", "量比", "换手率", "资金流向"],
        confidence: 0.8,
      },
      {
        category: "市场分析",
        keywords: ["市场概览", "大盘分析", "市场分析", "市场综述", "盘面分析", "大盘综述", "行情综述", "今日市场"],
        confidence: 0.75,
      },
      {
        category: "板块分析",
        keywords: ["板块", "行业分析", "板块分析", "行业轮动", "板块轮动", "赛道", "产业链"],
        confidence: 0.75,
      },
      {
        category: "映射分析",
        keywords: ["映射", "映射分析", "映射逻辑", "映射强度", "对标", "美股映射"],
        confidence: 0.75,
      },
      {
        category: "操作建议",
        keywords: ["加仓", "减仓", "止损", "止盈", "触发条件", "关键观察", "观察指标"],
        confidence: 0.8,
      },
      {
        category: "新闻事件",
        keywords: ["新闻", "消息", "事件", "公告", "政策", "要闻", "资讯"],
        confidence: 0.7,
      },
      {
        category: "个股分析",
        keywords: ["个股", "公司分析", "基本面", "财务分析", "业绩分析"],
        confidence: 0.7,
      },
    ];

    /**
     * 根据标题和内容判断分类
     *
     * @param {string} title - 章节标题
     * @param {string} content - 章节内容
     * @returns {{category: string, confidence: number}} 分类和置信度
     */
    function classifySection(title, content) {
      const text = (title + " " + content).toLowerCase();

      for (const rule of categoryRules) {
        for (const kw of rule.keywords) {
          if (text.includes(kw.toLowerCase())) {
            return { category: rule.category, confidence: rule.confidence };
          }
        }
      }

      // 如果标题里包含"执行信息"、"可沉淀记忆"等技术性标题，跳过
      if (title.includes("执行信息") || title.includes("可沉淀记忆") ||
          title.includes("数据截至") || title.includes("观点有效期")) {
        return { category: null, confidence: 0 };
      }

      return { category: "分析结论", confidence: 0.6 };
    }

    // ========== 第一步：按 Markdown 标题切分章节 ==========
    // 匹配 ## 或 ### 开头的标题行
    const sectionRegex = /\n(?=#{1,3}\s+)/g;
    const sections = analysis.split(sectionRegex);

    for (const section of sections) {
      const trimmed = section.trim();
      if (!trimmed) continue;

      // 提取标题行
      const firstLineMatch = trimmed.match(/^(#{1,3})\s+(.+)/);
      if (!firstLineMatch) continue;

      const title = firstLineMatch[2].trim();
      const content = trimmed.substring(firstLineMatch[0].length).trim();

      // 跳过太短或明显是技术性的标题
      if (title.length < 2 || title.length > 50) continue;
      if (title.includes("执行信息") || title.includes("可沉淀记忆") ||
          title.includes("数据截至") || title.includes("报告期") ||
          title.includes("观点有效期") || title.includes("📋") || title.includes("🧠")) {
        continue;
      }

      // 内容太短的跳过（没信息量）
      if (content.length < 30) continue;

      // 智能分类
      const { category, confidence } = classifySection(title, content);
      if (!category) continue;

      // ========== 第二步：从章节中提取多条要点 ==========
      // 小白讲解：一个章节里可能有好几个要点，
      // 比如"风险提示"里可能有3条不同的风险，
      // 我们把它们拆成独立的记忆卡片，方便后续检索
      const bulletPoints = content
        .split(/\n/)
        .map(l => l.trim())
        .filter(l => /^[-*]\s+/.test(l) || /^\d+\.\s+/.test(l)) // - xxx 或 1. xxx
        .map(l => l.replace(/^[-*]\s+/, "").replace(/^\d+\.\s+/, "").trim())
        .filter(l => l.length >= 20 && l.length <= 300); // 每条 20-300 字比较合适

      if (bulletPoints.length >= 2) {
        // 如果有多个要点，拆分成多条记忆
        for (let i = 0; i < bulletPoints.length && memories.length < 5; i++) {
          const point = bulletPoints[i];
          // 要点的标题用"分类: 要点摘要"形式
          const shortTitle = point.length > 30 ? point.substring(0, 30) + "..." : point;
          memories.push({
            title: shortTitle,
            content: point,
            category,
            confidence: Math.round((confidence - 0.05) * 100) / 100,
          });
        }
      } else {
        // 只有一个段落或没有要点，整段作为一条记忆
        // 但内容太长的话截取前200字作为摘要
        const shortTitle = title.length > 30 ? title.substring(0, 30) + "..." : title;
        memories.push({
          title: shortTitle,
          content: content.length > 500 ? content.substring(0, 500) + "..." : content,
          category,
          confidence: Math.round(confidence * 100) / 100,
        });
      }

      if (memories.length >= 5) break; // 最多5条
    }

    // ========== 第三步：兜底（如果上面啥也没提取到）==========
    if (memories.length === 0) {
      // 取报告前300字作为一条整体记忆
      const snippet = analysis.substring(0, 300).trim();
      if (snippet.length >= 50) {
        memories.push({
          title: "分析摘要",
          content: snippet + (analysis.length > 300 ? "..." : ""),
          category: "分析结论",
          confidence: 0.5,
        });
      }
    }

    return memories.slice(0, 5);
  }

  generateWorkflowSummary() {
    const completedSteps = this.executionHistory.filter(h => h.message.includes("完成"));
    
    return {
      ...this.executionStats,
      stepDetails: completedSteps.map(h => ({
        stepId: h.stepId,
        message: h.message.replace("✓ ", ""),
        timestamp: h.timestamp,
      })),
    };
  }

  generateFallbackResponse() {
    const data = this.context.data;
    const query = this.context.userQuery;

    if (this.currentTaskType === "opportunity_scan") {
      return this.generateOpportunityFallbackResponse();
    }
    if (this.currentTaskType === "daily_brief") {
      return this.generateDailyBriefFallbackResponse();
    }
    if (this.currentTaskType === "market_news") {
      return this.generateMarketNewsResponse();
    }
    if (this.currentTaskType === "market_attribution") {
      return this.generateMarketAttributionResponse();
    }
    if (["stock_analysis", "stock_deep_analysis"].includes(this.currentTaskType)) {
      return this.generateStockResearchFallbackResponse();
    }

    if (data.topGainers || data.topLosers) {
      let response = "📊 **市场扫描结果**\n\n";
      if (data.topGainers?.length) {
        response += "## 涨幅榜\n";
        data.topGainers.slice(0, 5).forEach((s, i) => {
          response += `${i+1}. ${s.name || STOCK_NAME_MAP[s.ts_code] || s.ts_code}: ${s.pct_chg?.toFixed(2)}%\n`;
        });
      }
      if (data.topLosers?.length) {
        response += "\n## 跌幅榜\n";
        data.topLosers.slice(0, 5).forEach((s, i) => {
          response += `${i+1}. ${s.name || STOCK_NAME_MAP[s.ts_code] || s.ts_code}: ${s.pct_chg?.toFixed(2)}%\n`;
        });
      }
      return response;
    }
    
    if (data.instrumentData) {
      const stock = data.stockEntity || {};
      return `已获取 **${stock.name || data.currentTicker}** 的数据：
- 最新价: ${data.instrumentData.latestPrice}
- 估值: PE ${data.instrumentData.valuation?.pe || "-"}
- 基本面: ROE ${data.instrumentData.fundamentals?.roe || "-"}%`;
    }
    
    if (data.news?.length) {
      return `获取到 ${data.news.length} 条新闻。如需详细分析，请告诉我。`;
    }
    
    return `已处理您的问题: "${query}"。由于 AI 模型不可用，无法生成详细分析报告。`;
  }

  generateOpportunityFallbackResponse() {
    const data = this.context.data;
    const catalog = data.evidenceCatalog || [];
    const evidenceId = (toolId, fallback) => catalog.find((item) => item.tool_id === toolId)?.evidence_id || fallback;
    const indexEvidence = evidenceId("get_market_indices", "E001");
    const gainerEvidence = evidenceId("get_top_gainers", "E002");
    const loserEvidence = evidenceId("get_top_losers", "E003");
    const activityEvidence = evidenceId("get_volume_surge", "E004");
    const valuationEvidence = evidenceId("get_valuation_extremes", "E006");
    const newsEvidence = evidenceId("get_latest_news", "E007");
    const poolEvidence = evidenceId("get_pool_snapshot", "E008");
    const asOf = data.topGainers?.[0]?.trade_date || catalog.find((item) => item.tool_id === "get_top_gainers")?.as_of?.slice(0, 10) || "未知";

    const activityCodes = new Set((data.volumeSurge || []).map((item) => item.ts_code));
    const candidates = (data.topGainers || [])
      .filter(opportunityCandidate)
      .map((item) => {
        const pe = Number(item.pe_ttm);
        const turnover = Number(item.turnover);
        const marketCap = Number(item.total_mv);
        let priority = 0;
        if (Number.isFinite(pe) && pe > 0 && pe <= 80) priority += 3;
        else if (Number.isFinite(pe) && pe > 0 && pe <= 150) priority += 1;
        else priority -= 2;
        if (Number.isFinite(turnover) && turnover >= 3 && turnover <= 20) priority += 2;
        if (Number.isFinite(marketCap) && marketCap >= 5_000_000_000) priority += 1;
        if (activityCodes.has(item.ts_code)) priority += 1;
        if (Number(item.pct_chg) > 15) priority -= 1;
        return { ...item, priority };
      })
      .sort((a, b) => b.priority - a.priority)
      .slice(0, 5);

    const indexLines = (data.marketIndices || []).slice(0, 4).map((item) => {
      const pct = Number(item.pct_chg);
      return `- ${item.name}：${item.price} 点，涨跌幅 ${pct >= 0 ? "+" : ""}${pct.toFixed(2)}%。[${indexEvidence}]`;
    });
    const candidateLines = candidates.map((item, index) => {
      const citations = activityCodes.has(item.ts_code)
        ? `[${gainerEvidence}][${activityEvidence}]`
        : `[${gainerEvidence}]`;
      const pe = Number.isFinite(Number(item.pe_ttm)) ? Number(item.pe_ttm).toFixed(1) : "缺失";
      const turnover = Number.isFinite(Number(item.turnover)) ? `${Number(item.turnover).toFixed(2)}%` : "缺失";
      const low = Number.isFinite(Number(item.low)) ? Number(item.low).toFixed(2) : "异动日低点";
      return `${index + 1}. **${item.name || item.ts_code}（${item.ts_code}）—仅列入观察** ${citations}
   - 已确认信号：收盘 ${Number(item.close).toFixed(2)} 元，单日涨跌 ${Number(item.pct_chg).toFixed(2)}%，换手 ${turnover}，PE(TTM) ${pe}。${citations}
   - 为什么跟踪：在剔除 ST/退市整理股后，价格强度、交易活跃度与基础估值的组合相对更可解释；这仍是短线异动线索，不是基本面买入结论。${citations}
   - 确认条件：后续交易日不出现高开低走，且行业或公司催化能由独立新闻/公告验证。${citations}[${newsEvidence}]
   - 放弃条件：跌破异动日低点 ${low} 元，或只有换手升高而缺乏新增基本面证据。${citations}`;
    });
    const newsLines = (data.latestNews || []).slice(0, 5).map((item) =>
      `- ${String(item.published_at || "").slice(0, 10)}｜${item.title}。[${newsEvidence}]`
    );
    const loserLines = (data.topLosers || []).slice(0, 3).map((item) =>
      `- ${item.name || item.ts_code}（${item.ts_code}）${Number(item.pct_chg).toFixed(2)}%，列入风险观察而非抄底候选。[${loserEvidence}]`
    );

    return `# A股机会扫描（确定性降级报告）

- 核心行情截至：${asOf}；当前为非交易时段，以下是最近已完成交易日的收盘观察。[${indexEvidence}]
- 数据健康：${data.dataHealth?.status === "healthy" ? "健康" : "存在降级项"}。实时行情与新闻可用，但估值快照和本地股票池已过期，不用于当前买卖判断。[${valuationEvidence}][${poolEvidence}]
- 生成说明：AI 深度综合未通过时限或质量门，本报告由确定性规则生成，优先保证可审计与不编造。

## 结论先行

当前只能形成“跟踪清单”，不能形成直接买入清单。涨幅榜反映短期资金强度，高换手反映成交活跃，二者都不能单独证明基本面改善；名称含 ST、*ST、退市或以“退”结尾的标的已从候选中剔除。若没有公告、业绩或产业催化的二次验证，建议保持观察而不是追涨。[${gainerEvidence}][${activityEvidence}][${newsEvidence}]

## 市场概览

${indexLines.join("\n") || `- 大盘指数缺失，无法判断整体风险偏好。[${indexEvidence}]`}

## 跟踪优先级

${candidateLines.join("\n\n") || `没有通过基础风险过滤的候选，暂不行动。[${gainerEvidence}][${activityEvidence}]`}

## 近期可核验催化

${newsLines.join("\n") || `- 近 8 天没有通过来源与日期过滤的 A 股新闻，新闻维度降级。[${newsEvidence}]`}

新闻只用于解释市场背景，不自动归因到上述个股；个股催化仍需公司公告或权威来源二次确认。[${newsEvidence}]

## 风险观察

${loserLines.join("\n") || `- 跌幅榜数据缺失。[${loserEvidence}]`}
- 估值证据截至 ${catalog.find((item) => item.tool_id === "get_valuation_extremes")?.as_of?.slice(0, 10) || "未知"}，已超过新鲜度阈值，不能据此声称当前低估。[${valuationEvidence}]
- 本地股票池行情截至 ${catalog.find((item) => item.tool_id === "get_pool_snapshot")?.as_of?.slice(0, 10) || "未知"}，落后最近交易日，不用于候选排序。[${poolEvidence}]
- 当前成交活跃榜的量比字段不可用时，系统只称“高换手异动”，不称“放量”。[${activityEvidence}]

## 操作纪律

1. 先观察，不在单日大涨后追价；候选必须经过下一交易日价格行为确认。[${gainerEvidence}]
2. 只有公司公告、业绩变化或产业数据与行情信号相互印证时，才进入单股深度研究。[${gainerEvidence}][${newsEvidence}]
3. 任何候选在跌破异动日低点、催化被证伪或流动性快速退潮时，从清单移除。[${gainerEvidence}][${activityEvidence}]
4. 本报告不构成投资建议，未给出目标价或仓位，是因为当前证据不足以支持这些结论。[${valuationEvidence}][${newsEvidence}]`;
  }

  generateDailyBriefFallbackResponse() {
    const data = this.context.data;
    const catalog = data.evidenceCatalog || [];
    const evidenceId = (toolId, fallback) => catalog.find((item) => item.tool_id === toolId)?.evidence_id || fallback;
    const indexEvidence = evidenceId("get_market_indices", "E001");
    const gainerEvidence = evidenceId("get_top_gainers", "E002");
    const loserEvidence = evidenceId("get_top_losers", "E003");
    const activityEvidence = evidenceId("get_volume_surge", "E004");
    const newsEvidence = evidenceId("get_latest_news", "E005");
    const poolEvidence = evidenceId("get_pool_snapshot", "E006");
    const asOf = data.topGainers?.[0]?.trade_date
      || catalog.find((item) => item.tool_id === "get_market_indices")?.as_of?.slice(0, 10)
      || "未知";

    const indices = (data.marketIndices || []).slice(0, 6).map((item) => {
      const pct = Number(item.pct_chg);
      return `- ${item.name}：${Number(item.price).toFixed(2)} 点，涨跌幅 ${pct >= 0 ? "+" : ""}${pct.toFixed(2)}%。[${indexEvidence}]`;
    });
    const gainers = (data.topGainers || []).filter(opportunityCandidate).slice(0, 5).map((item) =>
      `- ${item.name || item.ts_code}（${item.ts_code}）：收盘 ${Number(item.close).toFixed(2)} 元，涨跌幅 ${Number(item.pct_chg).toFixed(2)}%，换手 ${Number(item.turnover).toFixed(2)}%。[${gainerEvidence}]`
    );
    const highRisk = (data.topGainers || []).filter((item) => !opportunityCandidate(item)).slice(0, 3).map((item) =>
      `- ${item.name || item.ts_code}（${item.ts_code}）涨跌幅 ${Number(item.pct_chg).toFixed(2)}%，因名称触发 ST/退市风险规则，仅作风险记录，不进入关注清单。[${gainerEvidence}]`
    );
    const losers = (data.topLosers || []).slice(0, 3).map((item) =>
      `- ${item.name || item.ts_code}（${item.ts_code}）：涨跌幅 ${Number(item.pct_chg).toFixed(2)}%，换手 ${Number(item.turnover).toFixed(2)}%，列入波动风险观察。[${loserEvidence}]`
    );
    const activity = (data.volumeSurge || []).filter(opportunityCandidate).slice(0, 5).map((item) =>
      `- ${item.name || item.ts_code}（${item.ts_code}）：换手 ${Number(item.turnover).toFixed(2)}%，涨跌幅 ${Number(item.pct_chg).toFixed(2)}%；量比不可用时只称“高换手异动”。[${activityEvidence}]`
    );
    const news = (data.latestNews || []).slice(0, 5).map((item) =>
      `- ${String(item.published_at || "").slice(0, 10)}｜${item.title}。[${newsEvidence}]`
    );
    const newsLine = news.length > 0
      ? news.join("\n")
      : `- 最近 8 天没有通过来源、日期与正文过滤的新闻；新闻维度本次降级，不做事件归因。[${newsEvidence}]`;
    const poolAsOf = catalog.find((item) => item.tool_id === "get_pool_snapshot")?.as_of?.slice(0, 10) || "未知";

    return `# A股每日复盘（确定性报告）

- 核心行情截至：${asOf}；当前为非交易时段，以下使用最近已完成交易日的收盘数据。[${indexEvidence}]
- 生成说明：模型原稿未通过引用质量门，本报告由确定性规则生成，不提供目标价、仓位或未经证据支持的行业归因。

## 指数表现

${indices.join("\n") || `- 指数数据缺失，无法判断市场整体表现。[${indexEvidence}]`}

## 强势观察

以下只是当日价格与成交活跃度记录，不等于买入建议。[${gainerEvidence}]

${gainers.join("\n") || `- 没有通过 ST/退市风险过滤的强势标的。[${gainerEvidence}]`}

## 高换手观察

${activity.join("\n") || `- 高换手数据缺失。[${activityEvidence}]`}

## 风险观察

${[...highRisk, ...losers].join("\n") || `- 跌幅与高风险名称数据缺失。[${gainerEvidence}][${loserEvidence}]`}

## 可核验新闻

${newsLine}

新闻只用于说明市场背景，不能自动归因到上述个股；个股事件仍需公告或权威来源二次确认。[${newsEvidence}]

## 数据边界与下一交易日检查

- 本地股票池行情截至 ${poolAsOf}，若落后于 ${asOf}，不用于本次强弱排序。[${poolEvidence}]
- 下一交易日只检查三件事：指数是否延续弱势、强势股是否高开低走、高换手是否伴随新增公告；在确认前不把单日异动解释为趋势。[${indexEvidence}][${gainerEvidence}][${activityEvidence}]
- 本报告是事实复盘与跟踪清单，不构成投资建议。[${indexEvidence}][${gainerEvidence}]`;
  }

  generateMarketNewsResponse() {
    const data = this.context.data;
    const catalog = data.evidenceCatalog || [];
    const evidence = catalog.find((item) => item.tool_id === "get_latest_news");
    const evidenceId = evidence?.evidence_id || "E001";
    const news = (data.latestNews || []).slice(0, 12);
    const datedNews = news.filter((item) => item.published_at);
    const newestDate = datedNews
      .map((item) => String(item.published_at).slice(0, 10))
      .sort()
      .at(-1) || evidence?.as_of?.slice(0, 10) || "未知";

    const items = news.map((item, index) => {
      const date = String(item.published_at || "日期缺失").slice(0, 10);
      const source = item.source_name || item.source_id || "来源未标注";
      const title = String(item.title || "无标题").replace(/\s+/g, " ").trim();
      const url = item.url ? `｜[原文](${item.url})` : "";
      return `${index + 1}. ${date}｜${source}｜${title}${url}。[${evidenceId}]`;
    });

    return `# A股市场新闻清单

- 新闻截至：${newestDate}；仅保留有明确发布日期、正文与受信来源的最近结果。[${evidenceId}]
- 输出说明：这是检索清单，不对市场方向、板块强弱或个股影响作自动推断。[${evidenceId}]

## 已核验条目

${items.join("\n") || `本次新闻抓取没有得到通过质量过滤的结果；请稍后重试，当前不做事件判断。[${evidenceId}]`}

## 使用边界

- 同一条市场新闻不能自动归因到某只股票；个股催化必须再核对公司公告或交易所披露。[${evidenceId}]
- 标题只代表来源页面的公开表述，系统未补写资金意图、政策含义、目标价或操作建议。[${evidenceId}]`;
  }

  generateMarketAttributionResponse() {
    const data = this.context.data;
    const catalog = data.evidenceCatalog || [];
    const evidenceId = (toolId, fallback) => catalog.find((item) => item.tool_id === toolId)?.evidence_id || fallback;
    const gainerEvidence = evidenceId("get_top_gainers", "E001");
    const loserEvidence = evidenceId("get_top_losers", "E002");
    const newsEvidence = evidenceId("get_movement_news", "E003");
    const gainers = (data.topGainers || []).slice(0, 10);
    const losers = (data.topLosers || []).slice(0, 10);
    const news = (data.movementNews || []).filter((item) => item?.title);
    const asOf = gainers[0]?.trade_date || losers[0]?.trade_date
      || catalog.find((item) => item.tool_id === "get_top_gainers")?.as_of?.slice(0, 10)
      || "未知";

    const relatedNews = (stock) => {
      const code = String(stock.ts_code || stock.symbol || "").replace(/\.(SZ|SH|BJ)$/i, "");
      const name = String(stock.name || STOCK_NAME_MAP[stock.ts_code] || "").replace(/^\*?ST/i, "").trim();
      if (!code && !name) return [];
      const asOfTime = new Date(`${asOf}T23:59:59+08:00`).getTime();
      const oldestTime = asOfTime - 8 * 24 * 60 * 60 * 1000;
      return news.filter((item) => {
        const title = String(item.title || "");
        const publishedAt = new Date(item.published_at || 0).getTime();
        const sameTicker = item.ticker === stock.ts_code;
        const sameNameOrCode = (name.length >= 2 && title.includes(name)) || (code.length === 6 && title.includes(code));
        return (sameTicker || sameNameOrCode)
          && Number.isFinite(publishedAt)
          && publishedAt >= oldestTime
          && publishedAt <= asOfTime;
      }).slice(0, 2);
    };
    const row = (stock, rank, rankingEvidence) => {
      const name = stock.name || STOCK_NAME_MAP[stock.ts_code] || stock.ts_code || "名称缺失";
      const ticker = stock.ts_code || stock.symbol || "代码缺失";
      const pct = Number(stock.pct_chg ?? stock.change_percent);
      const close = Number(stock.close ?? stock.latest_price);
      const links = relatedNews(stock);
      const quote = `${rank}. **${name}（${ticker}）**：${Number.isFinite(pct) ? `${pct >= 0 ? "+" : ""}${pct.toFixed(2)}%` : "涨跌幅缺失"}${Number.isFinite(close) ? `，收盘 ${close.toFixed(2)} 元` : ""}。[${rankingEvidence}]`;
      if (links.length === 0) {
        return `${quote}\n   - 归因状态：未在异动日前 8 天的巨潮公告中找到可用事件，**原因未确认**；不得用题材、资金或情绪标签代替证据。[${rankingEvidence}][${newsEvidence}]`;
      }
      const eventText = links.map((item) => `${String(item.published_at || item.date || "日期缺失").slice(0, 10)}《${item.title}》`).join("；");
      return `${quote}\n   - 可核验关联公告：${eventText}。[${newsEvidence}]\n   - 归因边界：这里只确认异动日前 8 天内存在同标的公告，不证明该公告就是涨跌的唯一原因。[${rankingEvidence}][${newsEvidence}]`;
    };
    const gainerLines = gainers.map((stock, index) => row(stock, index + 1, gainerEvidence));
    const loserLines = losers.map((stock, index) => row(stock, index + 1, loserEvidence));
    const matchedCount = [...gainers, ...losers].filter((stock) => relatedNews(stock).length > 0).length;

    return `# A股涨跌幅归因核对表

- 榜单行情截至：${asOf}；涨幅榜 ${gainers.length} 只、跌幅榜 ${losers.length} 只。[${gainerEvidence}][${loserEvidence}]
- 本轮共核对 ${gainers.length + losers.length} 只标的，其中 ${matchedCount} 只找到异动日前 8 天内的同标的公告，其余均标记“原因未确认”。[${gainerEvidence}][${loserEvidence}][${newsEvidence}]
- 方法说明：榜单是事实层，巨潮公告是事件层；只有代码直接对应且发布时间处于异动日前 8 天才列为“关联公告”，不把市场背景新闻强行归因到个股。[${newsEvidence}]

## 涨幅前十

${gainerLines.join("\n\n") || `- 涨幅榜数据缺失，无法归因。[${gainerEvidence}]`}

## 跌幅前十

${loserLines.join("\n\n") || `- 跌幅榜数据缺失，无法归因。[${loserEvidence}]`}

## 使用边界

- “找到关联公告”只表示时间与标的相关，不等于完成因果识别；确认因果仍需核对公告正文、盘中时间线与成交结构。[${gainerEvidence}][${loserEvidence}][${newsEvidence}]
- “原因未确认”不是没有原因，而是本轮证据不足。报告不生成“主力拉升”“机构出货”“题材炒作”等不可验证叙事。[${newsEvidence}]
- 本表用于研究排查，不构成投资建议。[${gainerEvidence}][${loserEvidence}]`;
  }

  generateStockResearchFallbackResponse() {
    const data = this.context.data;
    const catalog = data.evidenceCatalog || [];
    const stockEvidence = catalog.find((item) => item.tool_id === "get_stock_data")?.evidence_id || "E001";
    const newsEvidence = catalog.find((item) => item.tool_id === "get_news")?.evidence_id || "E002";
    const stock = data.stockEntity || {};
    const instrument = data.instrumentData || {};
    const valuation = instrument.valuation || {};
    const fundamentals = instrument.fundamentals || {};
    const technical = instrument.technical || {};
    const enhanced = data.eastmoneyData || {};
    const ticker = stock.tsCode || data.currentTicker || "未知代码";
    const name = (stock.name && stock.name !== ticker ? stock.name : null) || STOCK_NAME_MAP[ticker] || ticker;
    const asOf = instrument.latestDate || catalog.find((item) => item.tool_id === "get_stock_data")?.as_of?.slice(0, 10) || "未知";
    const number = (value, digits = 2) => Number.isFinite(Number(value)) ? Number(value).toFixed(digits) : "缺失";
    const percent = (value) => Number.isFinite(Number(value)) ? `${Number(value).toFixed(2)}%` : "缺失";
    const yi = (value) => Number.isFinite(Number(value)) ? `${(Number(value) / 100_000_000).toFixed(2)} 亿元` : "缺失";

    const quoteLines = [
      `- 最近行情日期：${asOf}；收盘/观察价 ${number(instrument.latestPrice)} 元，涨跌幅 ${percent(instrument.changePercent)}。[${stockEvidence}]`,
      `- 近 5 日变化 ${percent(instrument.momentum?.m5d)}，近 20 日变化 ${percent(instrument.momentum?.m20d)}；两项来自本地历史行情计算。[${stockEvidence}]`,
      `- 技术因子日期：${technical.tradeDate || "缺失"}；RSI(14) ${number(technical.rsi14)}，MACD DIF ${number(technical.macdDif, 4)}，MA20 ${number(technical.ma20)}。[${stockEvidence}]`,
    ];

    const valuationLines = [];
    const pe = Number(valuation.pe);
    const pb = Number(valuation.pb);
    const ps = Number(valuation.ps);
    if (Number.isFinite(pe) && pe > 0 && pe <= 300) valuationLines.push(`- PE(TTM)：${pe.toFixed(2)} 倍。[${stockEvidence}]`);
    else valuationLines.push(`- PE(TTM) 字段缺失或异常，本报告不使用该指标作结论。[${stockEvidence}]`);
    if (Number.isFinite(pb) && pb > 0 && pb <= 100) valuationLines.push(`- PB：${pb.toFixed(2)} 倍。[${stockEvidence}]`);
    else valuationLines.push(`- PB 字段缺失或异常，本报告不使用该指标作结论。[${stockEvidence}]`);
    if (Number.isFinite(ps) && ps > 0 && ps <= 100) valuationLines.push(`- PS(TTM)：${ps.toFixed(2)} 倍。[${stockEvidence}]`);
    else valuationLines.push(`- PS(TTM) 字段值 ${number(valuation.ps)} 超出基础合理性检查或缺失，已从分析中剔除。[${stockEvidence}]`);

    const localGrossMargin = Number(fundamentals.grossMargin);
    const latestEnhancedGrossMargin = Number(enhanced.financialHistory?.[0]?.grossMargin);
    const localSnapshotUsable = Boolean(fundamentals.period)
      && Number.isFinite(Number(fundamentals.revenue))
      && Number(fundamentals.revenue) > 0
      && Number.isFinite(Number(fundamentals.netIncome))
      && Math.abs(Number(fundamentals.netIncome)) <= Number(fundamentals.revenue)
      && Number.isFinite(localGrossMargin)
      && localGrossMargin >= 0
      && localGrossMargin <= 100
      && (!Number.isFinite(latestEnhancedGrossMargin) || Math.abs(localGrossMargin - latestEnhancedGrossMargin) <= 20);
    const fundamentalLines = localSnapshotUsable
      ? [
          `- 财务快照报告期：${fundamentals.period}；数据状态：${fundamentals.freshnessStatus || "未标注"}。[${stockEvidence}]`,
          `- 营业收入 ${yi(fundamentals.revenue)}，净利润 ${yi(fundamentals.netIncome)}，毛利率 ${percent(fundamentals.grossMargin)}，ROE ${percent(fundamentals.roe)}。[${stockEvidence}]`,
        ]
      : [
          `- 本地财务快照缺少报告期或未通过跨字段一致性检查，已整体隔离，不展示其中的收入、利润、毛利率和 ROE。[${stockEvidence}]`,
          `- 下方仅保留带明确报告期的多期财务原始字段；绝对金额需回到定期报告原文复核。[${stockEvidence}]`,
        ];

    const financialLines = (enhanced.financialHistory || []).slice(0, 4).map((item) =>
      `- ${item.reportName || item.reportDate || "报告期缺失"}：营收同比 ${percent(item.revenueYoy)}，净利润同比 ${percent(item.netProfitYoy)}，毛利率 ${percent(item.grossMargin)}，ROE ${percent(item.roe)}。[${stockEvidence}]`
    );
    const fundFlowLines = (enhanced.fundFlow || []).slice(0, 5).map((item) =>
      `- ${item.date || "日期缺失"}：主力净额 ${number(Number(item.mainNet) / 10_000, 0)} 万元，占比 ${percent(item.mainNetPct)}，当日涨跌 ${percent(item.changePct)}；只记录源字段，不推断机构意图。[${stockEvidence}]`
    );
    const researchLines = (enhanced.researchReports || []).slice(0, 5).map((item) =>
      `- ${item.publishDate || "日期缺失"}｜${item.orgName || "机构未标注"}｜评级 ${item.rating || "未标注"}｜${item.title || "标题缺失"}。[${stockEvidence}]`
    );
    const newsLines = (data.news || []).filter((item) => item.published_at || item.date).slice(0, 6).map((item) =>
      `- ${String(item.published_at || item.date).slice(0, 10)}｜${item.source_name || item.source || "来源未标注"}｜${item.title || "无标题"}。[${newsEvidence}]`
    );

    return `# ${name}（${ticker}）可审计研究摘要

- 核心行情截至：${asOf}；不同模块可能存在日期差，以下不把历史因子或研报当作实时信号。[${stockEvidence}]
- 生成说明：模型原稿未通过引用质量门，本报告只陈列可追溯字段，不给目标价、仓位或直接买卖结论。

## 行情与技术快照

${quoteLines.join("\n")}

技术指标只描述源数据，不自动解释为超买、超卖、支撑位或反转信号。[${stockEvidence}]

## 估值字段检查

${valuationLines.join("\n")}

不同估值字段可能来自不同口径，异常字段已显式剔除，不能据此判断高估或低估。[${stockEvidence}]

## 财务快照

${fundamentalLines.join("\n")}

### 多期财务原始变化

${financialLines.join("\n") || `- 未取得可用的多期财务历史，不做增长趋势判断。[${stockEvidence}]`}

## 资金流原始记录

${fundFlowLines.join("\n") || `- 未取得可用的近期资金流记录，不判断主力或机构方向。[${stockEvidence}]`}

## 券商研报清单

${researchLines.join("\n") || `- 未取得可用的近期券商研报。[${stockEvidence}]`}

研报评级是第三方观点，不等于事实，也不据此计算一致目标价。[${stockEvidence}]

## 新闻与公告

${newsLines.join("\n") || `- 未取得带明确日期的个股新闻或公告，不做催化判断。[${newsEvidence}]`}

新闻标题不能自动证明对公司构成利好或利空，涉及重大事项时应回到交易所公告正文核验。[${newsEvidence}]

## 当前结论与下一步

- 当前证据可用于建立研究清单，但不足以直接形成买入、卖出、目标价或仓位建议。[${stockEvidence}][${newsEvidence}]
- 下一步应核对最新定期报告原文、最近交易日价格口径、异常估值字段和公告正文，再决定是否进入人工审阅。[${stockEvidence}][${newsEvidence}]
- 本摘要不构成投资建议。[${stockEvidence}]`;
  }

  addLog(stepId, message, data = null) {
    const entry = {
      timestamp: new Date().toISOString(),
      stepId,
      message,
      data,
    };
    this.executionHistory.push(entry);
    if (this.onEvent) {
      try {
        this.onEvent(entry);
      } catch (error) {
        console.warn("工作流审计事件写入失败:", error.message);
      }
    }
  }

  getStatus() {
    return {
      workflowState: this.context.workflowState,
      stepIndex: this.context.stepIndex,
      currentFlow: this.currentFlow,
      currentTaskType: this.currentTaskType,
      executionHistory: this.executionHistory,
      dataSummary: {
        hasInstrumentData: !!this.context.data.instrumentData,
        hasNews: !!(this.context.data.news?.length),
        hasMemory: !!(this.context.data.memoryResults?.length),
        hasLLMAnalysis: !!this.context.data.llmAnalysis,
      },
    };
  }

  setInput(input) {
    this.context.input = input;
  }

  setCurrentInput(currentInput) {
    this.context.currentInput = currentInput;
  }
}

export async function runWorkflow(query) {
  const engine = new WorkflowEngine();
  return await engine.processUserQuery(query);
}
