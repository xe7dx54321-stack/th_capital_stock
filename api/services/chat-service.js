/**
 * ChatBot 服务 - 自然语言交互接口
 * 
 * 功能：
 *   1. 接收用户中文提问
 *   2. 识别意图（股票分析、价值评分、机会雷达、新发现、新闻等）
 *   3. 调用对应模块获取数据
 *   4. 通过 LLM 生成自然语言回复
 *   5. 支持流式响应（SSE）
 * 
 * 小白讲解：
 *   这个服务就像一个"智能助手"——用户用中文提问（比如"帮我分析中际旭创"），
 *   它能理解用户要什么，去数据库里找对应的数据，然后用自然语言把结果说出来。
 */

import express from "express";

import { ResearchRepository } from "../repositories/research-repository.js";
import { buildValueScores } from "./scoring-service.js";
import { buildStockDetail } from "./stock-detail-service.js";
import { buildDashboard } from "./report-service.js";
import { buildDiscoveries } from "./discovery-service.js";
import { MarketDataService } from "./market-data-service.js";


/**
 * 意图识别结果类型
 */
const INTENT_TYPES = {
  STOCK_ANALYSIS: "stock_analysis",
  VALUE_SCORE: "value_score",
  OPPORTUNITY_RADAR: "opportunity_radar",
  DISCOVERY_CANDIDATES: "discovery_candidates",
  MARKET_NEWS: "market_news",
  HELP: "help",
  UNKNOWN: "unknown",
};

const STOCK_NAME_MAP = {
  "300308.SZ": "中际旭创",
  "000063.SZ": "中兴通讯",
  "688205.SH": "杰普特",
  "688800.SH": "澜起科技",
  "002281.SZ": "光迅科技",
  "002837.SZ": "英维克",
  "300394.SZ": "天孚通信",
  "300502.SZ": "新易盛",
  "300620.SZ": "光库科技",
  "872808.BJ": "中讯四方",
  "09988.HK": "阿里巴巴",
  "301171.SZ": "华如科技",
  "00020.HK": "蒙牛乳业",
  "002230.SZ": "科大讯飞",
  "603039.SH": "泛微网络",
  "688111.SH": "金山办公",
  "002957.SZ": "科瑞技术",
  "002050.SZ": "三花智控",
  "002600.SZ": "领益智造",
  "002796.SZ": "世运电路",
  "09980.HK": "网易",
  "300124.SZ": "汇川技术",
  "301368.SZ": "丰立智能",
  "600580.SH": "卧龙电驱",
  "601689.SH": "拓普集团",
  "603728.SH": "鸣志电器",
  "688017.SH": "绿的谐波",
  "688322.SH": "奥比中光",
  "300593.SZ": "新雷能",
  "603986.SH": "兆易创新",
  "688525.SH": "芯海科技",
  "00981.HK": "中芯国际",
  "01347.HK": "华虹半导体",
  "301269.SZ": "华大九天",
  "688008.SH": "澜起科技",
  "688041.SH": "海光信息",
  "688256.SH": "寒武纪",
  "688521.SH": "芯原股份",
  "688027.SH": "国盾量子",
};


/**
 * 识别用户提问的意图
 * 
 * 小白讲解：看看用户的问题是关于什么的——是问某只股票，还是问机会，还是问新发现？
 * 
 * 参数：
 *   query: 用户的中文提问
 *   repository: ResearchRepository 实例
 * 
 * 返回：
 *   object: { intent: 意图类型, params: 参数对象 }
 */
function recognizeIntent(query, repository) {
  const q = query.toLowerCase().trim();

  let matchedStock = null;

  for (const [code, name] of Object.entries(STOCK_NAME_MAP)) {
    const codeLower = code.toLowerCase();
    const codeWithoutSuffix = code.replace(/\.(SZ|SH|BJ|HK)$/i, "").toLowerCase();
    const nameLower = name.toLowerCase();
    
    if (q.includes(codeLower) || q.includes(codeWithoutSuffix) || q.includes(nameLower)) {
      let sector = null;
      try {
        const marketService = new MarketDataService();
        try {
          const entity = marketService.resolveEntity(code);
          sector = entity.sector;
        } finally {
          marketService.close();
        }
      } catch (e) {
        console.warn("Failed to get sector info:", e.message);
      }
      matchedStock = { ts_code: code, name: name, sector: sector };
      break;
    }
  }

  if (!matchedStock) {
    try {
      const marketService = new MarketDataService();
      try {
        const allStocks = marketService.db
          .prepare(`SELECT DISTINCT ts_code, sector FROM stock_pool`)
          .all();

        for (const stock of allStocks) {
          const code = stock.ts_code?.toLowerCase();
          const codeWithoutSuffix = stock.ts_code?.replace(/\.(SZ|SH|BJ|HK)$/i, "").toLowerCase();
          const name = STOCK_NAME_MAP[stock.ts_code]?.toLowerCase();
          
          if (q.includes(code) || q.includes(codeWithoutSuffix) || (name && q.includes(name))) {
            const entity = marketService.resolveEntity(stock.ts_code);
            matchedStock = { ts_code: stock.ts_code, name: STOCK_NAME_MAP[stock.ts_code] || entity.name || stock.ts_code, sector: entity.sector || stock.sector };
            break;
          }
        }
      } finally {
        marketService.close();
      }
    } catch (e) {
      console.warn("Failed to load stock list from big DB:", e.message);
    }
  }

  try {
    if (!matchedStock) {
      const scoreInputs = repository.getValueScoreInputs();
      for (const input of scoreInputs) {
        const code = input.tsCode?.toLowerCase();
        const name = input.name?.toLowerCase() || input.tsCode?.toLowerCase();
        if (q.includes(code) || q.includes(name)) {
          matchedStock = { ts_code: input.tsCode, name: input.name || input.tsCode, sector: input.sector };
          break;
        }
      }
    }
  } catch (e) {
    console.warn("Failed to load stock list:", e.message);
  }

  if (matchedStock) {
    if (q.includes("分析") || q.includes("研究") || q.includes("怎么样") || q.includes("如何")) {
      return { intent: INTENT_TYPES.STOCK_ANALYSIS, params: { stock: matchedStock } };
    }
    if (q.includes("评分") || q.includes("估值") || q.includes("vfm") || q.includes("价值")) {
      return { intent: INTENT_TYPES.VALUE_SCORE, params: { stock: matchedStock } };
    }
    return { intent: INTENT_TYPES.STOCK_ANALYSIS, params: { stock: matchedStock } };
  }

  if (q.includes("机会") || q.includes("雷达") || q.includes("推荐") || q.includes("选股")) {
    return { intent: INTENT_TYPES.OPPORTUNITY_RADAR, params: {} };
  }

  if (q.includes("发现") || q.includes("新标的") || q.includes("候选") || q.includes("新增")) {
    return { intent: INTENT_TYPES.DISCOVERY_CANDIDATES, params: {} };
  }

  if (q.includes("新闻") || q.includes("消息") || q.includes("公告")) {
    return { intent: INTENT_TYPES.MARKET_NEWS, params: {} };
  }

  if (q.includes("帮助") || q.includes("用法") || q.includes("功能")) {
    return { intent: INTENT_TYPES.HELP, params: {} };
  }

  return { intent: INTENT_TYPES.UNKNOWN, params: {} };
}


/**
 * 收集股票分析数据
 */
function collectStockAnalysisData(stock, repository) {
  const result = {
    stock: stock,
  };

  try {
    // 股票详情
    const detail = repository.getStockDetailInput(stock.ts_code);
    if (detail) {
      result.detail = buildStockDetail(stock.ts_code, detail);
    }
  } catch (e) {
    console.warn("Failed to load stock detail:", e.message);
  }

  try {
    // VFM 评分
    const scoreInputs = repository.getValueScoreInputs();
    const scores = buildValueScores(scoreInputs);
    const stockScore = scores.scores.find(s => s.tsCode === stock.ts_code);
    if (stockScore) {
      result.valueScore = stockScore;
    }
  } catch (e) {
    console.warn("Failed to load VFM scores:", e.message);
  }

  return result;
}


/**
 * 生成股票分析的自然语言回复
 */
function generateStockAnalysisResponse(data) {
  const { stock, detail, valueScore } = data;

  let response = `好的，我来为您分析 **${stock.name || stock.ts_code}**。\n\n`;

  // 基础信息
  if (detail) {
    response += `### 基本信息\n`;
    response += `- 代码: ${stock.ts_code}\n`;
    response += `- 所属板块: ${detail.sector || "未知"}\n`;
    if (detail.price) {
      response += `- 当前价格: ${detail.price}元\n`;
      response += `- 涨跌幅: ${detail.pctChange || "N/A"}\n`;
    }
    response += "\n";
  } else {
    response += `### 基本信息\n`;
    response += `- 代码: ${stock.ts_code}\n`;
    response += `- 所属板块: ${stock.sector || "未知"}\n\n`;
  }

  // VFM 评分
  if (valueScore && valueScore.vfmScoreCard) {
    const vfm = valueScore.vfmScoreCard;
    response += `### VFM 价值评分\n`;
    response += `- 综合评分: ${vfm.compositeScore || 0}/10\n`;
    response += `- 基本面质量: ${vfm.fundamentalQuality || 0}/10\n`;
    response += `- 估值位置: ${vfm.valuationPosition || 0}/10\n`;
    response += `- 技术动量: ${vfm.technicalMomentum || 0}/10\n`;
    response += `- 主题相关性: ${vfm.themeRelevance || 0}/10\n`;
    response += `- 产业位置: ${vfm.industryPosition || 0}/10\n`;

    if (vfm.redFlags && vfm.redFlags.length > 0) {
      response += `\n#### ⚠️ 警示信号\n`;
      vfm.redFlags.forEach(flag => {
        response += `- ${flag}\n`;
      });
    }

    // 简单分析
    const composite = vfm.compositeScore || 0;
    if (composite >= 7) {
      response += `\n**📊 分析结论**: 综合评分较高，基本面和主题匹配度较好，值得关注。\n`;
    } else if (composite >= 5) {
      response += `\n**📊 分析结论**: 综合评分中等，建议结合其他因素综合判断。\n`;
    } else {
      response += `\n**📊 分析结论**: 综合评分较低，建议谨慎评估。\n`;
    }
  } else {
    response += `### VFM 价值评分\n`;
    response += `- 暂无评分数据（可能尚未入池或数据未更新）\n`;
    response += `- 可运行价值评分管线获取最新数据\n`;
  }

  return response;
}


/**
 * 生成价值评分的自然语言回复
 */
function generateValueScoreResponse(data) {
  if (!data.valueScore) {
    return "抱歉，暂未找到该标的的 VFM 评分数据。";
  }

  const vfm = data.valueScore.vfmScoreCard;
  let response = `**${data.stock.name || data.stock.ts_code}** 的 VFM 价值评分卡：\n\n`;

  response += `| 维度 | 分数 |\n`;
  response += `|------|------|\n`;
  response += `| 综合评分 | ${vfm.compositeScore || 0}/10 |\n`;
  response += `| 基本面质量 | ${vfm.fundamentalQuality || 0}/10 |\n`;
  response += `| 估值位置 | ${vfm.valuationPosition || 0}/10 |\n`;
  response += `| 技术动量 | ${vfm.technicalMomentum || 0}/10 |\n`;
  response += `| 主题相关性 | ${vfm.themeRelevance || 0}/10 |\n`;
  response += `| 产业位置 | ${vfm.industryPosition || 0}/10 |\n`;

  if (vfm.redFlags && vfm.redFlags.length > 0) {
    response += `\n⚠️ **警示信号**: ${vfm.redFlags.join("、")}\n`;
  }

  return response;
}


/**
 * 生成机会雷达的自然语言回复
 */
function generateOpportunityRadarResponse(scanData) {
  if (!scanData) {
    return "抱歉，机会扫描数据暂不可用。";
  }

  let response = `📊 **今日机会扫描报告**\n\n`;
  response += `扫描日期: ${scanData.scanDate}\n\n`;

  if (scanData.topGainers && scanData.topGainers.length > 0) {
    response += `## 📈 涨幅榜 TOP 8\n\n`;
    scanData.topGainers.forEach((stock, index) => {
      const name = STOCK_NAME_MAP[stock.ts_code] || stock.ts_code;
      response += `${index + 1}. **${name}** (${stock.ts_code})\n`;
      response += `   - 涨跌幅: ${(stock.pct_chg || 0).toFixed(2)}%\n`;
      response += `   - 收盘价: ${(stock.close || 0).toFixed(2)}\n`;
      response += `   - 成交量: ${(stock.vol || 0).toLocaleString()}\n`;
      response += `\n`;
    });
  }

  if (scanData.topLosers && scanData.topLosers.length > 0) {
    response += `## 📉 跌幅榜 TOP 5\n\n`;
    scanData.topLosers.forEach((stock, index) => {
      const name = STOCK_NAME_MAP[stock.ts_code] || stock.ts_code;
      response += `${index + 1}. **${name}** (${stock.ts_code})\n`;
      response += `   - 涨跌幅: ${(stock.pct_chg || 0).toFixed(2)}%\n`;
      response += `   - 收盘价: ${(stock.close || 0).toFixed(2)}\n`;
      response += `\n`;
    });
  }

  if (scanData.volumeSurge && scanData.volumeSurge.length > 0) {
    response += `## 🚀 放量异动\n\n`;
    scanData.volumeSurge.forEach((stock, index) => {
      const name = STOCK_NAME_MAP[stock.ts_code] || stock.ts_code;
      response += `${index + 1}. **${name}** (${stock.ts_code})\n`;
      response += `   - 成交量: ${(stock.current_vol || 0).toLocaleString()} (${(stock.vol_ratio || 0).toFixed(1)}倍)\n`;
      response += `   - 涨跌幅: ${(stock.pct_chg || 0).toFixed(2)}%\n`;
      response += `\n`;
    });
  }

  if (scanData.priceMovement && scanData.priceMovement.length > 0) {
    response += `## ⚡ 价格异动（涨跌幅 ≥ 3%）\n\n`;
    scanData.priceMovement.forEach((stock, index) => {
      const name = STOCK_NAME_MAP[stock.ts_code] || stock.ts_code;
      const isUp = stock.pct_chg > 0;
      response += `${index + 1}. **${name}** (${stock.ts_code}) - ${isUp ? "⬆️" : "⬇️"} ${(stock.pct_chg || 0).toFixed(2)}%\n`;
    });
    response += `\n`;
  }

  if (scanData.poolSnapshot && scanData.poolSnapshot.length > 0) {
    const poolGainers = scanData.poolSnapshot.filter(s => s.pct_chg > 2).slice(0, 5);
    const poolLosers = scanData.poolSnapshot.filter(s => s.pct_chg < -2).slice(0, 5);
    
    if (poolGainers.length > 0) {
      response += `## ✨ 股票池强势标的\n\n`;
      poolGainers.forEach((stock, index) => {
        const name = STOCK_NAME_MAP[stock.ts_code] || stock.ts_code;
        response += `${index + 1}. **${name}** (${stock.ts_code}) - ⬆️ ${(stock.pct_chg || 0).toFixed(2)}%\n`;
        response += `   - 板块: ${stock.sector || "未知"} | 池子: ${stock.pool_type || "未知"}\n`;
      });
      response += `\n`;
    }
    
    if (poolLosers.length > 0) {
      response += `## ⚠️ 股票池弱势标的\n\n`;
      poolLosers.forEach((stock, index) => {
        const name = STOCK_NAME_MAP[stock.ts_code] || stock.ts_code;
        response += `${index + 1}. **${name}** (${stock.ts_code}) - ⬇️ ${(stock.pct_chg || 0).toFixed(2)}%\n`;
      });
      response += `\n`;
    }
  }

  if (scanData.valuationExtremes && scanData.valuationExtremes.length > 0) {
    response += `## 💰 估值极端标的\n\n`;
    scanData.valuationExtremes.forEach((stock, index) => {
      const name = STOCK_NAME_MAP[stock.ticker] || stock.ticker;
      const isLow = stock.historical_percentile <= 20;
      response += `${index + 1}. **${name}** (${stock.ticker})\n`;
      response += `   - 估值分位: ${stock.historical_percentile || 0}% ${isLow ? "(历史低位)" : "(历史高位)"}\n`;
      response += `   - PE: ${stock.pe_ttm || "-"} | PB: ${stock.pb || "-"}\n`;
      response += `\n`;
    });
  }

  if (scanData.latestNews && scanData.latestNews.length > 0) {
    response += `## 📰 最新新闻热点\n\n`;
    scanData.latestNews.slice(0, 5).forEach((news, index) => {
      response += `${index + 1}. **${news.title || "无标题"}**\n`;
      response += `   - 来源: ${news.source_name || "未知"}\n`;
      response += `   - 时间: ${news.published_at || "未知"}\n`;
      if (news.tickers_json) {
        try {
          const tickers = JSON.parse(news.tickers_json);
          response += `   - 关联股票: ${tickers.join(", ")}\n`;
        } catch (e) {}
      }
      response += `\n`;
    });
  }

  response += `💡 如需深入分析某只股票，请说"帮我分析 [股票名称]"`;

  return response;
}


/**
 * 生成新发现候选的自然语言回复
 */
function generateDiscoveryResponse(discoveries) {
  if (!discoveries || discoveries.length === 0) {
    return "目前没有新发现的候选标的。可以运行自主发现管线扫描新标的。";
  }

  let response = `🔍 **新发现候选标的**\n\n`;
  response += `共发现 ${discoveries.length} 个新候选：\n\n`;

  // 按主题分组
  const bySector = {};
  discoveries.forEach(d => {
    const sector = d.sector || "未分类";
    if (!bySector[sector]) bySector[sector] = [];
    bySector[sector].push(d);
  });

  for (const [sector, items] of Object.entries(bySector)) {
    response += `### ${sector}\n`;
    items.forEach(item => {
      response += `- **${item.name || item.ticker}** (${item.ticker}) - 发现方法: ${item.discoveryMethod || "未知"}\n`;
    });
    response += "\n";
  }

  response += `💡 提示: 这些候选需经过 VFM 评分和 3 道门筛选后才能提案入池。\n`;

  return response;
}


/**
 * 生成新闻的自然语言回复
 */
function generateNewsResponse(newsList) {
  if (!newsList || newsList.length === 0) {
    return "目前没有最新新闻。";
  }

  let response = `📰 **最新新闻**\n\n`;
  newsList.slice(0, 5).forEach((news, index) => {
    response += `${index + 1}. **${news.title || news.headline}**\n`;
    response += `   - 时间: ${news.publishTime || news.date || "未知"}\n`;
    if (news.summary) {
      response += `   - 摘要: ${news.summary}\n`;
    }
    response += `\n`;
  });

  return response;
}


/**
 * 生成帮助信息
 */
function generateHelpResponse() {
  return `👋 您好！我是 SMR 研究助手，可以帮您做以下事情：\n\n` +
    `### 股票分析\n` +
    `- "帮我分析中际旭创"\n` +
    `- "中际旭创怎么样"\n` +
    `- "分析 300308"\n\n` +
    `### 价值评分\n` +
    `- "中际旭创的价值评分"\n` +
    `- "300308 的 VFM 评分"\n\n` +
    `### 机会雷达\n` +
    `- "今天有哪些机会"\n` +
    `- "机会雷达"\n\n` +
    `### 新发现\n` +
    `- "有哪些新发现的股票"\n` +
    `- "新标的"\n\n` +
    `### 新闻\n` +
    `- "最近有什么新闻"\n` +
    `- "最新公告"\n\n` +
    `💡 提示: 您可以直接说股票名称或代码，我会自动识别。`;
}


/**
 * 生成未知意图的回复
 */
function generateUnknownResponse(query) {
  return `抱歉，我不太理解您的问题："${query}"\n\n` +
    `您可以尝试：\n` +
    `- 分析某只股票："帮我分析中际旭创"\n` +
    `- 查询价值评分："中际旭创的 VFM 评分"\n` +
    `- 查看机会："今天有哪些机会"\n` +
    `- 查看新发现："有哪些新发现的股票"\n` +
    `- 查看新闻："最近有什么新闻"\n` +
    `- 获取帮助："帮助"`;
}


/**
 * 主聊天服务函数
 * 
 * 小白讲解：这是聊天服务的核心——先理解用户问什么，再去对应的数据模块找答案，
 * 最后用自然语言把答案说出来。
 * 
 * 参数：
 *   query: 用户的中文提问
 *   repository: ResearchRepository 实例
 * 
 * 返回：
 *   object: { intent, response, data }
 */
export function buildChatResponse(query, repository) {
  // 1. 识别意图
  const { intent, params } = recognizeIntent(query, repository);

  // 2. 根据意图收集数据
  let data = {};
  let response = "";

  switch (intent) {
    case INTENT_TYPES.STOCK_ANALYSIS:
      data = collectStockAnalysisData(params.stock, repository);
      response = generateStockAnalysisResponse(data);
      break;

    case INTENT_TYPES.VALUE_SCORE:
      data = collectStockAnalysisData(params.stock, repository);
      response = generateValueScoreResponse(data);
      break;

    case INTENT_TYPES.OPPORTUNITY_RADAR:
      try {
        let scanData = null;
        const marketService = new MarketDataService();
        try {
          const topGainers = marketService.getTopGainers(8);
          const topLosers = marketService.getTopLosers(5);
          const volumeSurge = marketService.getVolumeSurge(8, 1.5);
          const latestNews = marketService.getLatestNews(10);
          const poolSnapshot = marketService.getPoolSnapshot();
          const priceMovement = marketService.getPriceMovement(3, 10);
          const valuationExtremes = marketService.getValuationExtremes(8);
          const recentFundamentals = marketService.getRecentFundamentals(5);

          const latestDate = marketService.db
            .prepare(`SELECT MAX(trade_date) as date FROM daily_bar`)
            .get()?.date || "未知";

          scanData = {
            scanDate: latestDate,
            topGainers,
            topLosers,
            volumeSurge,
            latestNews,
            poolSnapshot,
            priceMovement,
            valuationExtremes,
            recentFundamentals,
          };
        } finally {
          marketService.close();
        }
        
        data.scanData = scanData;
        response = generateOpportunityRadarResponse(scanData);
      } catch (e) {
        response = `获取机会扫描数据失败：${e.message}`;
      }
      break;

    case INTENT_TYPES.DISCOVERY_CANDIDATES:
      try {
        const inputs = repository.getDiscoveryInputs();
        const discoveries = buildDiscoveries(inputs);
        data.discoveries = discoveries;
        response = generateDiscoveryResponse(discoveries);
      } catch (e) {
        response = `获取新发现数据失败：${e.message}`;
      }
      break;

    case INTENT_TYPES.MARKET_NEWS:
      try {
        const news = repository.listNews();
        data.news = news;
        response = generateNewsResponse(news);
      } catch (e) {
        response = `获取新闻数据失败：${e.message}`;
      }
      break;

    case INTENT_TYPES.HELP:
      response = generateHelpResponse();
      break;

    case INTENT_TYPES.UNKNOWN:
    default:
      response = generateUnknownResponse(query);
      break;
  }

  return {
    intent,
    query,
    response,
    data,
    timestamp: new Date().toISOString(),
  };
}


/**
 * 创建 ChatBot 路由
 */
export function createChatRouter({ repository }) {
  const router = express.Router();

  // POST /api/chat - 聊天接口
  router.post("/api/chat", async (req, res) => {
    try {
      const { message } = req.body;
      if (!message || typeof message !== "string") {
        return res.status(400).json({ error: "请提供 message 参数" });
      }

      const result = buildChatResponse(message, repository);
      res.json(result);
    } catch (error) {
      console.error("Chat service error:", error);
      res.status(500).json({ error: error.message });
    }
  });

  // GET /api/chat/intents - 获取支持的意图列表
  router.get("/api/chat/intents", (_req, res) => {
    res.json({
      intents: [
        { type: INTENT_TYPES.STOCK_ANALYSIS, description: "股票分析", example: "帮我分析中际旭创" },
        { type: INTENT_TYPES.VALUE_SCORE, description: "价值评分", example: "中际旭创的 VFM 评分" },
        { type: INTENT_TYPES.OPPORTUNITY_RADAR, description: "机会雷达", example: "今天有哪些机会" },
        { type: INTENT_TYPES.DISCOVERY_CANDIDATES, description: "新发现", example: "有哪些新发现的股票" },
        { type: INTENT_TYPES.MARKET_NEWS, description: "市场新闻", example: "最近有什么新闻" },
        { type: INTENT_TYPES.HELP, description: "帮助", example: "帮助" },
      ],
    });
  });

  return router;
}
