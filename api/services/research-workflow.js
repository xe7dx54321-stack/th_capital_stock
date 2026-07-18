/**
 * 多步骤研究工作流服务（真实数据版）
 *
 * 功能：
 *   1. 定义股票研究的完整工作流步骤（模仿 knevo 的 sequential workflow）
 *   2. 按顺序执行每个步骤，每步都从真实数据库获取数据
 *   3. 跟踪每步执行状态（类似 knevo 的 "正在执行..." → "✓" 日志）
 *   4. 汇总所有真实数据，用 LLM 生成深度研究报告
 *
 * 数据来源：
 *   th_capital_stock/01_data/db/smr.db（298MB 真实金融数据库）
 *   通过 MarketDataService 访问，不再使用 Math.random() 或 Mock 数据
 *
 * 小白讲解：
 *   这个服务就像一个"研究向导"——它知道研究一只股票需要哪些步骤，
 *   会一步一步执行（查新闻→解析实体→拉取数据→汇总分析），
 *   每一步都从数据库拿真实数据，最后用 AI 生成完整的研究报告。
 */

import express from "express";
import { createChatCompletion, isModelAvailable } from "./llm-service.js";
import { VectorMemory } from "./vector-memory.js";
import { MarketDataService } from "./market-data-service.js";
import { MemoryService } from "./memory-service.js";
import { DecisionService } from "./decision-service.js";

/**
 * 工作流步骤定义
 *
 * 每个步骤包含：
 *   - stepId: 唯一标识
 *   - name: 显示名称
 *   - description: 描述
 *   - execute: 执行函数，接收 context 对象，返回 { success, data, message }
 */
const WORKFLOW_STEPS = [
  {
    stepId: "load_skills",
    name: "加载研究技能",
    description: "加载投研方法论和分析框架",
    execute: async (context) => {
      context.skillsLoaded = true;
      return {
        success: true,
        data: { loaded: ["投资研究框架", "硬证据验证", "估值分析方法", "技术面分析", "风险评估"] },
      };
    },
  },
  {
    stepId: "provider_status",
    name: "检查数据提供商状态",
    description: "验证各数据源是否可用",
    execute: async (context) => {
      const providerStatus = {
        localDB: context.dataService?.db ? "available" : "unavailable",
        vectorDB: "available",
        llm: isModelAvailable() ? "available" : "unavailable",
      };
      context.providerStatus = providerStatus;
      return {
        success: true,
        data: providerStatus,
        message: `本地数据库: ${providerStatus.localDB} | 向量数据库: ${providerStatus.vectorDB} | LLM: ${providerStatus.llm}`,
      };
    },
  },
  {
    stepId: "memory_query",
    name: "检索投研记忆",
    description: "从记忆数据库检索历史研究内容",
    execute: async (context) => {
      const memService = new MemoryService();
      try {
        // 1. 查该股票的历史记忆（所有状态）
        const stockMemories = memService.getMemoriesForTicker(context.ticker, { limit: 10 });
        context.memoryResults = stockMemories;

        // 2. 查同行业已批准的记忆（如果已知同业列表）
        let peerMemories = [];
        // 同业列表在 entity_resolve 步骤后才可用，这里先查向量库做语义检索
        const vector = new VectorMemory();
        try {
          const vectorResults = await vector.searchSimilar(context.ticker, { limit: 5, threshold: 0.3 });
          context.vectorResults = vectorResults;
        } catch (e) {
          context.vectorResults = [];
        } finally {
          vector.close();
        }

        // 3. 把记忆格式化为 LLM 上下文
        const memoryText = memService.formatMemoriesAsContext(stockMemories);
        context.memoryContextText = memoryText;

        return {
          success: true,
          data: {
            stockMemoryCount: stockMemories.length,
            vectorResultCount: context.vectorResults.length,
            summaries: stockMemories.map((m) => `[${m.memory_type}] ${m.content?.slice(0, 80)}`),
          },
          message: `找到 ${stockMemories.length} 条股票记忆 + ${context.vectorResults.length} 条语义匹配`,
        };
      } catch (e) {
        context.memoryResults = [];
        context.vectorResults = [];
        return { success: false, error: e.message, message: "记忆检索失败，跳过此步骤" };
      } finally {
        memService.close();
      }
    },
  },
  {
    stepId: "entity_resolve",
    name: "解析金融实体",
    description: "识别股票代码、名称、行业等信息",
    execute: async (context) => {
      const stockInfo = context.dataService.resolveEntity(context.ticker);
      context.stockEntity = stockInfo;
      return {
        success: true,
        data: stockInfo,
        message: `已解析：${stockInfo.name}（${stockInfo.tsCode}），所属 ${stockInfo.sector || "未知行业"}`,
      };
    },
  },
  {
    stepId: "fetch_news",
    name: "检索金融新闻",
    description: "获取最新的市场新闻和公告",
    execute: async (context) => {
      // 从 news_items 表查真实新闻
      const news = context.dataService.getNews(context.ticker, 10);
      // 从 market_event 表查真实公告事件
      const events = context.dataService.getMarketEvents(context.ticker, 5);
      context.news = news;
      context.events = events;
      return {
        success: true,
        data: {
          newsCount: news.length,
          eventCount: events.length,
          headlines: news.slice(0, 5).map((n) => n.title),
        },
        message: `获取到 ${news.length} 条新闻、${events.length} 条公告事件`,
      };
    },
  },
  {
    stepId: "market_summary",
    name: "汇总市场消息",
    description: "整理市场情绪和关键事件",
    execute: async (context) => {
      const news = context.news || [];
      const events = context.events || [];

      // 基于真实新闻和公告做简单情绪分析
      const positiveKeywords = ["增长", "买入", "领先", "优势", "突破", "超预期", "上调", "获批"];
      const negativeKeywords = ["下降", "下调", "风险", "亏损", "下滑", "警示", "处罚"];

      let positiveCount = 0;
      let negativeCount = 0;
      for (const n of news) {
        const text = (n.title + " " + (n.body || "")).toLowerCase();
        if (positiveKeywords.some((k) => text.includes(k))) positiveCount++;
        if (negativeKeywords.some((k) => text.includes(k))) negativeCount++;
      }

      // 提取关键事件
      const keyEvents = [
        ...news.slice(0, 3).map((n) => `[${n.published_at?.substring(0, 10)}] ${n.title}`),
        ...events.slice(0, 3).map((e) => `[${e.event_date}] ${e.title}`),
      ];

      const summary = {
        newsCount: news.length,
        eventCount: events.length,
        sentiment:
          positiveCount > negativeCount ? "positive" : negativeCount > positiveCount ? "negative" : "neutral",
        positiveCount,
        negativeCount,
        keyEvents,
      };
      context.marketSummary = summary;
      return {
        success: true,
        data: summary,
        message: `市场消息汇总完成（正面 ${positiveCount} / 负面 ${negativeCount}）`,
      };
    },
  },
  {
    stepId: "graph_context",
    name: "读取金融图谱",
    description: "获取关联公司、行业关系等图谱数据",
    execute: async (context) => {
      const stock = context.stockEntity || {};
      const graph = {
        sector: stock.sector || "未知",
        sectorKey: stock.sectorKey,
        peers: stock.peers || [],
        usBenchmarks: stock.usBenchmarks || [],
        poolType: stock.poolType,
        poolStatus: stock.poolStatus,
      };
      context.graphContext = graph;
      return {
        success: true,
        data: graph,
        message: `金融图谱读取完成（同业 ${graph.peers.length} 家，美股对标 ${graph.usBenchmarks.length} 家）`,
      };
    },
  },
  {
    stepId: "instrument_data",
    name: "拉取标的全景",
    description: "获取股票的完整数据（行情、估值、基本面、技术面）",
    execute: async (context) => {
      // 从真实数据库查四个维度的数据
      const dailyBars = context.dataService.getDailyBars(context.ticker, 20);
      const valuation = context.dataService.getValuation(context.ticker);
      const fundamentals = context.dataService.getFundamentals(context.ticker);
      const factors = context.dataService.getFactors(context.ticker);
      const riskAlerts = context.dataService.getRiskAlerts(context.ticker, 5);

      // 计算近期涨跌（基于真实日线）
      let momentum5d = null;
      let momentum20d = null;
      if (dailyBars.length >= 2) {
        const latest = dailyBars[0]; // 最新一天
        const fiveDaysAgo = dailyBars[Math.min(4, dailyBars.length - 1)];
        const twentyDaysAgo = dailyBars[Math.min(19, dailyBars.length - 1)];
        if (latest?.close && fiveDaysAgo?.close) {
          momentum5d = ((latest.close - fiveDaysAgo.close) / fiveDaysAgo.close) * 100;
        }
        if (latest?.close && twentyDaysAgo?.close) {
          momentum20d = ((latest.close - twentyDaysAgo.close) / twentyDaysAgo.close) * 100;
        }
      }

      const instrument = {
        // 真实日线行情
        dailyBars: dailyBars.slice(0, 5).map((b) => ({
          date: b.trade_date,
          open: b.open,
          close: b.close,
          high: b.high,
          low: b.low,
          volume: b.vol,
          pctChg: b.pct_chg,
        })),
        latestPrice: dailyBars[0]?.close || valuation?.current_price || null,
        latestDate: dailyBars[0]?.trade_date || null,

        // 真实估值数据
        valuation: valuation
          ? {
              pe: valuation.pe_ttm,
              pb: valuation.pb,
              ps: valuation.ps_ttm,
              evEbitda: valuation.ev_ebitda_ttm,
              marketCap: valuation.market_cap,
              currentPrice: valuation.current_price,
              historicalPercentile: valuation.historical_percentile,
              historicalPercentile1y: valuation.historical_percentile_1y,
              historicalPercentile3y: valuation.historical_percentile_3y,
              historicalPercentile5y: valuation.historical_percentile_5y,
              peerPercentile: valuation.peer_percentile,
              brokerTargetPrice: valuation.broker_target_price,
              valuationStatus: valuation.valuation_status,
              valuationConfidence: valuation.valuation_confidence,
              snapshotDate: valuation.generated_at,
            }
          : null,

        // 真实基本面数据
        fundamentals: fundamentals
          ? {
              revenue: fundamentals.revenue,
              grossProfit: fundamentals.gross_profit,
              operatingIncome: fundamentals.operating_income,
              netIncome: fundamentals.net_income,
              eps: fundamentals.eps_basic,
              freeCashFlow: fundamentals.free_cash_flow,
              operatingCashFlow: fundamentals.operating_cash_flow,
              grossMargin: fundamentals.gross_margin,
              operatingMargin: fundamentals.operating_margin,
              netMargin: fundamentals.net_margin,
              roe: fundamentals.roe,
              roic: fundamentals.roic,
              totalDebt: fundamentals.total_debt,
              shareholdersEquity: fundamentals.shareholders_equity,
              period: fundamentals.period,
              confidence: fundamentals.confidence,
            }
          : null,

        // 真实技术因子（从 factor_daily 转置而来）
        technical: {
          rsi14: factors.rsi_14 ?? null,
          trendStrength: factors.trend_strength ?? null,
          macdDif: factors.macd_dif ?? null,
          macdDea: factors.macd_dea ?? null,
          macdHist: factors.macd_hist ?? null,
          ma20: factors.ma_20 ?? null,
          ma60: factors.ma_60 ?? null,
          volatility20: factors.volatility_20 ?? null,
          peTtm: factors.pe_ttm ?? null,
          pb: factors.pb ?? null,
          peDynamic: factors.pe_dynamic ?? null,
          grossMargin: factors.gross_margin ?? null,
          netMargin: factors.net_margin ?? null,
          netProfit: factors.net_profit ?? null,
          netProfitYoy: factors.net_profit_yoy ?? null,
          revenue: factors.revenue ?? null,
          revenueYoy: factors.revenue_yoy ?? null,
          roeReported: factors.roe_reported ?? null,
          debtAssetRatio: factors.debt_asset_ratio ?? null,
          currentRatio: factors.current_ratio ?? null,
          quickRatio: factors.quick_ratio ?? null,
          tradeDate: factors._tradeDate ?? null,
        },

        // 近期涨跌幅（基于真实日线计算）
        momentum: {
          m5d: momentum5d,
          m20d: momentum20d,
        },

        // 真实风险告警
        riskAlerts: riskAlerts.map((a) => ({
          time: a.alert_time,
          type: a.alert_type,
          severity: a.severity,
          message: a.message,
        })),
      };

      context.instrumentData = instrument;
      return {
        success: true,
        data: {
          hasDailyBars: dailyBars.length > 0,
          hasValuation: !!valuation,
          hasFundamentals: !!fundamentals,
          hasTechnical: Object.keys(factors).length > 1,
          hasRiskAlerts: riskAlerts.length > 0,
          latestPrice: instrument.latestPrice,
          latestDate: instrument.latestDate,
        },
        message: `标的全景拉取完成（行情${dailyBars.length}天 | 估值${valuation ? "✓" : "✗"} | 基本面${fundamentals ? "✓" : "✗"} | 技术面${Object.keys(factors).length > 1 ? "✓" : "✗"}）`,
      };
    },
  },
  {
    stepId: "data_summary",
    name: "汇总个股数据",
    description: "整合所有数据维度",
    execute: async (context) => {
      const data = context.instrumentData || {};
      const news = context.news || [];
      const events = context.events || [];

      const summary = {
        hasDailyBars: !!data.dailyBars?.length,
        hasValuation: !!data.valuation,
        hasFundamentals: !!data.fundamentals,
        hasTechnical: !!data.technical?.rsi14,
        hasNews: news.length > 0,
        hasEvents: events.length > 0,
        hasMemory: (context.memoryResults || []).length > 0,
        hasRiskAlerts: !!data.riskAlerts?.length,
        latestPrice: data.latestPrice,
        latestDate: data.latestDate,
        newsCount: news.length,
        eventCount: events.length,
        totalDataPoints:
          (data.valuation ? 1 : 0) +
          (data.fundamentals ? 1 : 0) +
          (data.technical ? 1 : 0) +
          (data.dailyBars?.length > 0 ? 1 : 0) +
          (news.length > 0 ? 1 : 0) +
          (events.length > 0 ? 1 : 0),
      };
      context.dataSummary = summary;
      return {
        success: true,
        data: summary,
        message: `个股数据汇总完成（${summary.totalDataPoints} 个数据维度）`,
      };
    },
  },
  {
    stepId: "llm_analysis",
    name: "AI 深度分析",
    description: "使用 LLM 进行综合分析和报告生成",
    execute: async (context) => {
      if (!isModelAvailable()) {
        return { success: false, message: "LLM 不可用，跳过 AI 分析步骤" };
      }
      const analysis = await generateAIAnalysis(context);
      context.llmAnalysis = analysis;
      return {
        success: true,
        data: analysis,
        message: "AI 深度分析完成",
      };
    },
  },
  {
    stepId: "generate_report",
    name: "生成研究报告",
    description: "组装最终的研究报告",
    execute: async (context) => {
      const report = assembleReport(context);
      context.finalReport = report;
      return {
        success: true,
        data: { reportGenerated: true },
        message: "研究报告生成完成",
      };
    },
  },
  {
    stepId: "save_memory",
    name: "保存研究记忆",
    description: "从分析结果中提取关键事实，存为候选记忆",
    execute: async (context) => {
      const memService = new MemoryService();
      try {
        const aiAnalysis = context.llmAnalysis?.rawAnalysis || "";
        const memories = await memService.extractAndSaveMemories(
          context.ticker,
          aiAnalysis,
          context,
          null
        );
        context.savedMemories = memories;
        return {
          success: true,
          data: {
            memoryCount: memories.length,
            types: memories.reduce((acc, m) => {
              acc[m.memory_type] = (acc[m.memory_type] || 0) + 1;
              return acc;
            }, {}),
          },
          message: `保存 ${memories.length} 条候选记忆（待审核）`,
        };
      } catch (e) {
        return { success: false, error: e.message, message: `记忆保存失败: ${e.message}` };
      } finally {
        memService.close();
      }
    },
  },
  {
    stepId: "create_decision",
    name: "生成投资决策",
    description: "LLM 基于分析结果生成结构化投资建议并记录为决策",
    execute: async (context) => {
      const decisionService = new DecisionService();
      try {
        const aiAnalysis = context.llmAnalysis?.rawAnalysis || "";
        const stock = context.stockEntity || {};
        const data = context.instrumentData || {};
        const memories = context.savedMemories || [];

        // LLM 生成决策建议
        const decision = await decisionService.generateDecisionFromAnalysis(
          context.ticker,
          aiAnalysis,
          context
        );

        // 存入决策台账
        const record = decisionService.createDecision({
          ticker: stock.tsCode || context.ticker,
          action: decision.action,
          thesisSummary: decision.thesis_summary,
          bearCaseSummary: decision.bear_case_summary,
          referencePrice: data.latestPrice || null,
          killConditions: decision.kill_conditions || [],
          suggestedPositionPct: decision.suggested_position_pct || null,
          evidenceIds: [],
          memoryIds: memories.map((m) => m.memory_id),
        });

        context.decisionRecord = record;
        context.decisionSuggestion = decision;

        // 同步更新已生成的报告中的 decision 字段
        // （因为 generate_report 步骤在 create_decision 之前执行，
        //   所以 assembleReport 时 decisionSuggestion 还没设置，需要在这里补上）
        if (context.finalReport) {
          context.finalReport.decision = {
            decisionId: record.decision_id,
            action: decision.action,
            confidence: decision.confidence,
            thesis: decision.thesis_summary,
            bearCase: decision.bear_case_summary,
            killConditions: decision.kill_conditions,
            suggestedPositionPct: decision.suggested_position_pct,
            timeHorizon: decision.time_horizon,
            keyRisks: decision.key_risks,
          };
        }

        return {
          success: true,
          data: {
            decisionId: record.decision_id,
            action: decision.action,
            confidence: decision.confidence,
            thesis: decision.thesis_summary,
          },
          message: `投资决策已记录：${decision.action.toUpperCase()}（置信度 ${(decision.confidence * 100).toFixed(0)}%）`,
        };
      } catch (e) {
        return { success: false, error: e.message, message: `决策生成失败: ${e.message}` };
      } finally {
        decisionService.close();
      }
    },
  },
];

/**
 * 使用 LLM 生成深度分析
 *
 * 功能：把所有真实数据组装成 prompt，发给 MiniMax LLM 生成分析报告
 *
 * @param {object} context - 工作流上下文，包含所有步骤收集的真实数据
 * @returns {object} { rawAnalysis, usage }
 */
async function generateAIAnalysis(context) {
  const stock = context.stockEntity || {};
  const data = context.instrumentData || {};
  const news = context.news || [];
  const events = context.events || [];
  const graph = context.graphContext || {};
  const marketSummary = context.marketSummary || {};
  const memoryResults = context.memoryResults || [];
  const memoryContextText = context.memoryContextText || "无历史记忆";

  // 构建系统提示词
  const systemPrompt = `你是一位专业的股票研究分析师。请基于以下真实数据，对股票进行深度分析。

分析要求：
1. 使用中文，结论先行
2. 输出格式清晰，使用 Markdown
3. 保持客观谨慎的研究态度
4. 数据中如有 null 或缺失，请明确指出
5. 注意数据的时间口径，标注数据截止日期

输出结构：
- 投资摘要（3-5句话总结核心结论）
- 核心观点（用表格展示各维度评级）
- 估值分析（基于真实 PE/PB 数据）
- 基本面分析（基于真实财务数据）
- 技术面分析（基于真实 RSI/MACD/均线数据）
- 近期动态（基于真实新闻和公告）
- 风险提示
- 投资建议`;

  // 构建用户提示词——把真实数据喂给 LLM
  const userPrompt = `## 股票信息
名称：${stock.name || "未知"}
代码：${stock.tsCode || context.ticker}
行业：${stock.sector || "未知"}
市场：${stock.market || "未知"}

## 最新行情
最新价：${data.latestPrice || "无数据"}
数据日期：${data.latestDate || "无数据"}
5日涨跌：${data.momentum?.m5d != null ? data.momentum.m5d.toFixed(2) + "%" : "无数据"}
20日涨跌：${data.momentum?.m20d != null ? data.momentum.m20d.toFixed(2) + "%" : "无数据"}

## 估值数据（来自 valuation_snapshot）
${data.valuation ? JSON.stringify(data.valuation, null, 2) : "无数据"}

## 基本面数据（来自 fundamentals_snapshot）
${data.fundamentals ? JSON.stringify(data.fundamentals, null, 2) : "无数据"}

## 技术面数据（来自 factor_daily，日期 ${data.technical?.tradeDate || "未知"}）
RSI(14): ${data.technical?.rsi14 ?? "无数据"}
MACD: DIF=${data.technical?.macdDif ?? "无"}, DEA=${data.technical?.macdDea ?? "无"}, HIST=${data.technical?.macdHist ?? "无"}
MA20: ${data.technical?.ma20 ?? "无数据"}
MA60: ${data.technical?.ma60 ?? "无数据"}
20日波动率: ${data.technical?.volatility20 ?? "无数据"}
趋势强度: ${data.technical?.trendStrength ?? "无数据"}
资产负债率: ${data.technical?.debtAssetRatio ?? "无数据"}%
流动比率: ${data.technical?.currentRatio ?? "无数据"}
速动比率: ${data.technical?.quickRatio ?? "无数据"}
毛利率: ${data.technical?.grossMargin ?? "无数据"}%
净利率: ${data.technical?.netMargin ?? "无数据"}%
ROE(报告): ${data.technical?.roeReported ?? "无数据"}%
营收同比: ${data.technical?.revenueYoy ?? "无数据"}%
净利同比: ${data.technical?.netProfitYoy ?? "无数据"}%

## 近期新闻（来自 news_items，共 ${news.length} 条）
${news.slice(0, 5).map((n, i) => `${i + 1}. [${n.published_at?.substring(0, 10)}] ${n.source_name}: ${n.title}`).join("\n")}

## 近期公告/事件（来自 market_event，共 ${events.length} 条）
${events.slice(0, 3).map((e, i) => `${i + 1}. [${e.event_date}] ${e.title} (重要性: ${e.importance})`).join("\n")}

## 同业对比（来自 sector_config）
同业: ${graph.peers?.join(", ") || "无"}
美股对标: ${graph.usBenchmarks?.join(", ") || "无"}

## 市场情绪
${marketSummary.sentiment || "中性"}（正面 ${marketSummary.positiveCount || 0} / 负面 ${marketSummary.negativeCount || 0}）

## 历史研究记忆（来自记忆系统，共 ${memoryResults.length} 条）
${memoryContextText}

请基于以上真实数据进行深度分析。如果历史记忆存在，请对比当前数据和历史记忆，指出变化趋势。`;

  const result = await createChatCompletion(
    [
      { role: "system", content: systemPrompt },
      { role: "user", content: userPrompt },
    ],
    { maxTokens: 3000, temperature: 0.6 }
  );

  return {
    rawAnalysis: result.content,
    usage: result.usage,
  };
}

/**
 * 组装最终研究报告
 *
 * 功能：把所有步骤收集的真实数据和 LLM 分析结果组装成完整的报告 JSON
 *
 * @param {object} context - 工作流上下文
 * @returns {object} 完整的研究报告
 */
function assembleReport(context) {
  const stock = context.stockEntity || {};
  const data = context.instrumentData || {};
  const news = context.news || [];
  const events = context.events || [];
  const llmAnalysis = context.llmAnalysis?.rawAnalysis || "";
  const marketSummary = context.marketSummary || {};
  const graphContext = context.graphContext || {};
  const dataSummary = context.dataSummary || {};
  const decisions = context.dataService.getDecisions(context.ticker, 3);

  return {
    metadata: {
      ticker: stock.tsCode || context.ticker,
      name: stock.name || context.ticker,
      sector: stock.sector,
      sectorKey: stock.sectorKey,
      market: stock.market,
      poolType: stock.poolType,
      poolStatus: stock.poolStatus,
      generatedAt: new Date().toISOString(),
      workflowVersion: "2.0",
      dataSource: "th_capital_stock/01_data/db/smr.db (real data)",
    },
    dataQuality: {
      hasDailyBars: dataSummary.hasDailyBars,
      hasValuation: dataSummary.hasValuation,
      hasFundamentals: dataSummary.hasFundamentals,
      hasTechnical: dataSummary.hasTechnical,
      hasNews: dataSummary.hasNews,
      hasEvents: dataSummary.hasEvents,
      hasMemory: dataSummary.hasMemory,
      hasRiskAlerts: dataSummary.hasRiskAlerts,
      totalDataPoints: dataSummary.totalDataPoints,
      latestPrice: dataSummary.latestPrice,
      latestDate: dataSummary.latestDate,
    },
    marketContext: {
      sentiment: marketSummary.sentiment,
      positiveCount: marketSummary.positiveCount,
      negativeCount: marketSummary.negativeCount,
      keyEvents: marketSummary.keyEvents,
    },
    industryContext: {
      sector: graphContext.sector,
      peers: graphContext.peers,
      usBenchmarks: graphContext.usBenchmarks,
    },
    structuredData: {
      dailyBars: data.dailyBars,
      valuation: data.valuation,
      fundamentals: data.fundamentals,
      technical: data.technical,
      momentum: data.momentum,
      riskAlerts: data.riskAlerts,
    },
    newsAndEvents: {
      news: news.slice(0, 5).map((n) => ({
        date: n.published_at,
        source: n.source_name,
        title: n.title,
        body: n.body?.substring(0, 300),
      })),
      events: events.slice(0, 3).map((e) => ({
        date: e.event_date,
        type: e.event_type,
        title: e.title,
        importance: e.importance,
      })),
    },
    decisionHistory: decisions.map((d) => ({
      decisionId: d.decision_id,
      action: d.action,
      status: d.status,
      decisionTime: d.decision_time,
      thesisSummary: d.thesis_summary,
      outcomeStatus: d.outcome_status,
    })),
    aiAnalysis: llmAnalysis,
    decision: context.decisionSuggestion
      ? {
          decisionId: context.decisionRecord?.decision_id,
          action: context.decisionSuggestion.action,
          confidence: context.decisionSuggestion.confidence,
          thesis: context.decisionSuggestion.thesis_summary,
          bearCase: context.decisionSuggestion.bear_case_summary,
          killConditions: context.decisionSuggestion.kill_conditions,
          suggestedPositionPct: context.decisionSuggestion.suggested_position_pct,
          timeHorizon: context.decisionSuggestion.time_horizon,
          keyRisks: context.decisionSuggestion.key_risks,
          referencePrice: context.instrumentData?.latestPrice,
        }
      : null,
    disclaimer: "本报告基于真实数据库数据生成，数据截止日期见各数据项。仅供研究参考，不构成投资建议。",
  };
}

/**
 * 研究工作流服务类
 *
 * 用法：
 *   const workflow = new ResearchWorkflow("300308.SZ");
 *   await workflow.execute();
 *   const report = workflow.getReport();
 */
export class ResearchWorkflow {
  /**
   * 构造函数
   * @param {string} ticker - 股票代码
   */
  constructor(ticker) {
    this.ticker = ticker;
    this.context = { ticker };
    this.executionHistory = [];
    this.status = "pending";
    this.startTime = null;
    this.endTime = null;
    // 创建市场数据服务实例，连接大数据库
    this.dataService = new MarketDataService();
    this.context.dataService = this.dataService;
  }

  /**
   * 获取当前状态
   * @returns {object} 状态对象
   */
  getStatus() {
    return {
      ticker: this.ticker,
      status: this.status,
      startTime: this.startTime,
      endTime: this.endTime,
      stepCount: WORKFLOW_STEPS.length,
      completedSteps: this.executionHistory.filter((s) => s.status === "completed").length,
      executionHistory: this.executionHistory,
    };
  }

  /**
   * 添加日志记录
   * @param {string} stepId - 步骤ID
   * @param {string} message - 日志消息
   * @param {object} data - 附加数据
   */
  addLog(stepId, message, data = null) {
    this.executionHistory.push({
      timestamp: new Date().toISOString(),
      stepId,
      message,
      data,
    });
  }

  /**
   * 按顺序执行所有步骤
   * @returns {object} 最终状态
   */
  async execute() {
    this.status = "running";
    this.startTime = new Date().toISOString();

    for (const step of WORKFLOW_STEPS) {
      this.addLog(step.stepId, `正在执行：${step.name}...`);

      try {
        const result = await step.execute(this.context);

        if (result.success) {
          this.addLog(step.stepId, `✓ ${step.name} 完成`, result.data);
        } else {
          this.addLog(step.stepId, `✗ ${step.name} 失败: ${result.error || result.message}`);
        }
      } catch (error) {
        this.addLog(step.stepId, `✗ ${step.name} 异常: ${error.message}`);
      }
    }

    this.status = "completed";
    this.endTime = new Date().toISOString();

    // 关闭数据库连接
    this.dataService.close();

    return this.getStatus();
  }

  /**
   * 获取最终报告
   * @returns {object|null} 研究报告
   */
  getReport() {
    return this.context.finalReport || null;
  }
}

/**
 * 创建工作流并执行（便捷函数）
 * @param {string} ticker - 股票代码
 * @returns {Promise<ResearchWorkflow>} 工作流实例
 */
export async function runResearchWorkflow(ticker) {
  const workflow = new ResearchWorkflow(ticker);
  await workflow.execute();
  return workflow;
}

/**
 * 创建工作流服务路由
 * @returns {express.Router} Express 路由
 */
export function createResearchWorkflowRouter() {
  const router = express.Router();

  // POST /api/research/workflow/start
  // 启动研究工作流，传入 ticker 参数
  router.post("/api/research/workflow/start", async (req, res) => {
    try {
      const { ticker } = req.body;
      if (!ticker || typeof ticker !== "string") {
        return res.status(400).json({ error: "请提供 ticker 参数" });
      }

      const workflow = new ResearchWorkflow(ticker);
      const status = await workflow.execute();

      res.json({
        success: true,
        ticker,
        status,
        report: workflow.getReport(),
      });
    } catch (error) {
      console.error("Research workflow error:", error);
      res.status(500).json({ error: error.message });
    }
  });

  // GET /api/research/stocks
  // 返回所有有数据的股票列表
  router.get("/api/research/stocks", (req, res) => {
    try {
      const service = new MarketDataService();
      const stocks = service.getAllStocksWithData();
      service.close();
      res.json({ success: true, count: stocks.length, stocks });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  // ========================================
  // 记忆管理 API
  // ========================================

  // GET /api/research/memories
  // 查询记忆列表，支持按 ticker / status 筛选
  router.get("/api/research/memories", (req, res) => {
    try {
      const { ticker, status, memoryType, limit } = req.query;
      const memService = new MemoryService();
      let memories;
      if (ticker) {
        memories = memService.getMemoriesForTicker(ticker, {
          status: status || null,
          memoryType: memoryType || null,
          limit: parseInt(limit) || 20,
        });
      } else {
        // 无 ticker 时返回所有（或按状态筛选）
        let sql = `SELECT * FROM memory_items`;
        const params = [];
        if (status) {
          sql += ` WHERE status = ?`;
          params.push(status);
        }
        sql += ` ORDER BY created_at DESC LIMIT ?`;
        params.push(parseInt(limit) || 50);
        memories = memService.db.prepare(sql).all(...params);
      }
      memService.close();
      res.json({ success: true, count: memories.length, memories });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  // GET /api/research/memories/stats
  // 返回记忆统计信息
  router.get("/api/research/memories/stats", (req, res) => {
    try {
      const memService = new MemoryService();
      const stats = memService.getMemoryStats();
      memService.close();
      res.json({ success: true, stats });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  // GET /api/research/memories/pending
  // 返回待审核的记忆候选
  router.get("/api/research/memories/pending", (req, res) => {
    try {
      const memService = new MemoryService();
      const pending = memService.getPendingMemories(parseInt(req.query.limit) || 50);
      memService.close();
      res.json({ success: true, count: pending.length, memories: pending });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  // POST /api/research/memories/:memoryId/review
  // 审核一条记忆
  router.post("/api/research/memories/:memoryId/review", (req, res) => {
    try {
      const { memoryId } = req.params;
      const { action, reviewer, reason } = req.body;
      if (!action || !["approve", "reject", "archive", "supersede"].includes(action)) {
        return res.status(400).json({ error: "action 必须是 approve/reject/archive/supersede" });
      }
      const memService = new MemoryService();
      const updated = memService.reviewMemory(memoryId, action, reviewer || "user", reason || "");
      memService.close();
      res.json({ success: true, memory: updated });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  // POST /api/research/memories/review-batch
  // 批量审核记忆
  router.post("/api/research/memories/review-batch", (req, res) => {
    try {
      const { memoryIds, action, reviewer, reason } = req.body;
      if (!Array.isArray(memoryIds) || !memoryIds.length) {
        return res.status(400).json({ error: "memoryIds 必须是非空数组" });
      }
      if (!action || !["approve", "reject", "archive"].includes(action)) {
        return res.status(400).json({ error: "action 必须是 approve/reject/archive" });
      }
      const memService = new MemoryService();
      const results = [];
      for (const id of memoryIds) {
        try {
          const updated = memService.reviewMemory(id, action, reviewer || "user", reason || "");
          results.push({ memoryId: id, success: true, status: updated.status });
        } catch (e) {
          results.push({ memoryId: id, success: false, error: e.message });
        }
      }
      memService.close();
      res.json({ success: true, count: results.length, results });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  // ========================================
  // 决策管理 API（决策反馈闭环）
  // ========================================
  // 端点说明：
  //   GET  /api/research/decisions              - 查询决策列表（支持 ticker/status/action 筛选）
  //   GET  /api/research/decisions/stats        - 决策统计（总数/已确认/已失败/胜率）
  //   GET  /api/research/decisions/pending-reviews - 待复盘决策列表
  //   GET  /api/research/decisions/:id          - 获取决策详情
  //   POST /api/research/decisions/:id/review   - 人工复盘（确认/否定论点）
  //   POST /api/research/decisions/:id/update-outcome - 自动回填价格结果
  //   POST /api/research/decisions/batch-update-outcomes - 批量回填所有待更新决策

  /**
   * 查询决策列表
   * 支持 query 参数：ticker, status, action, limit
   */
  router.get("/api/research/decisions", (req, res) => {
    try {
      const { ticker, status, action, limit } = req.query;
      const decisionService = new DecisionService();
      const decisions = decisionService.getDecisions({
        ticker: ticker || null,
        status: status || null,
        action: action || null,
        limit: parseInt(limit) || 20,
      });
      decisionService.close();
      res.json({ success: true, count: decisions.length, decisions });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  /**
   * 决策统计
   * 返回：total, open, confirmed, failed, expired, confirmedRate
   */
  router.get("/api/research/decisions/stats", (req, res) => {
    try {
      const decisionService = new DecisionService();
      const stats = decisionService.getStats();
      decisionService.close();
      res.json({ success: true, stats });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  /**
   * 待复盘决策列表
   * 返回到期但未复盘的决策
   */
  router.get("/api/research/decisions/pending-reviews", (req, res) => {
    try {
      const decisionService = new DecisionService();
      const pending = decisionService.getPendingReviews(parseInt(req.query.limit) || 20);
      decisionService.close();
      res.json({ success: true, count: pending.length, decisions: pending });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  /**
   * 获取决策详情
   */
  router.get("/api/research/decisions/:id", (req, res) => {
    try {
      const decisionService = new DecisionService();
      const decision = decisionService.db
        .prepare(`SELECT * FROM decision_ledger WHERE decision_id = ?`)
        .get(req.params.id);
      decisionService.close();
      if (!decision) {
        return res.status(404).json({ error: "决策不存在" });
      }
      res.json({ success: true, decision });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  /**
   * 人工复盘决策
   * body: { thesisConfirmed, outcomeSummary, failureReason, reviewer }
   */
  router.post("/api/research/decisions/:id/review", (req, res) => {
    try {
      const { thesisConfirmed, outcomeSummary, failureReason, reviewer } = req.body;
      if (thesisConfirmed === undefined || thesisConfirmed === null) {
        return res.status(400).json({ error: "thesisConfirmed 是必填参数" });
      }
      const decisionService = new DecisionService();
      const updated = decisionService.reviewDecision(req.params.id, {
        thesisConfirmed: Boolean(thesisConfirmed),
        outcomeSummary: outcomeSummary || "",
        failureReason: failureReason || "",
        reviewer: reviewer || "user",
      });
      decisionService.close();
      res.json({ success: true, decision: updated });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  /**
   * 自动回填决策价格结果
   * 功能：查询决策后 1天/1周/1月/3月 的实际价格，更新到决策记录
   */
  router.post("/api/research/decisions/:id/update-outcome", (req, res) => {
    try {
      const decisionService = new DecisionService();
      const updated = decisionService.updateOutcome(req.params.id);
      decisionService.close();
      res.json({ success: true, decision: updated });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  /**
   * 批量回填所有待更新决策的价格结果
   */
  router.post("/api/research/decisions/batch-update-outcomes", (req, res) => {
    try {
      const decisionService = new DecisionService();
      const results = decisionService.batchUpdateOutcomes();
      decisionService.close();
      const successCount = results.filter((r) => r.success).length;
      res.json({
        success: true,
        total: results.length,
        successCount,
        failCount: results.length - successCount,
        results,
      });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  return router;
}
