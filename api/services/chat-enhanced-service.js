/**
 * 增强版 ChatBot 服务 - 集成 Workflow 引擎
 * 
 * 核心设计：
 *   1. 不再是简单的单轮对话，而是调用 WorkflowEngine 进行流程规划和执行
 *   2. 支持多轮对话上下文
 *   3. 真正的 Agent 模式：理解问题 → 规划流程 → 调用工具 → 生成报告
 * 
 * 工作流程：
 *   用户提问 → 意图识别 → 流程规划 → 数据收集 → 记忆检索 → AI分析 → 报告生成 → 返回结果
 * 
 * 小白讲解：
 *   这个服务现在就像一个真正的"研究员"：
 *   - 先听懂你问什么（意图识别）
 *   - 规划需要做哪些工作（流程规划）
 *   - 去数据库和网络找资料（数据收集）
 *   - 翻以前的研究笔记（记忆检索）
 *   - 综合分析所有信息（AI分析）
 *   - 写出完整的研究报告（报告生成）
 */

import express from "express";
import { runWorkflow, WorkflowEngine } from "./workflow-engine.js";
import { VectorMemory } from "./vector-memory.js";
import { GrowthTracker } from "./growth-service.js";
import { SessionService } from "./session-service.js";

export async function buildEnhancedChatResponse(query, repository, options = {}) {
  const { enableVector = true, enableGrowth = true, conversationContext = {} } = options;

  const engine = new WorkflowEngine();
  engine.context.input = conversationContext || {};

  // 修复：从conversationContext中提取chatHistory传给引擎
  // 小白讲解：就像打电话时要让对方知道之前聊了什么，
  // 这样引擎才能理解用户的追问是在接着之前的话题
  const chatHistory = conversationContext?.chatHistory || [];
  const result = await engine.processUserQuery(query, chatHistory);

  let vector = null;
  if (enableVector) {
    try {
      vector = new VectorMemory();
      const relevant = await vector.searchSimilar(query, { limit: 3, threshold: 0.4 });
      if (relevant.length > 0) {
        result.context = {
          similarContents: relevant.map(item => ({
            content: item.content,
            contentType: item.contentType,
            similarity: item.similarity,
          })),
          summary: `找到 ${relevant.length} 个相关历史内容`,
        };
      }
    } catch (e) {
      console.warn("向量检索失败:", e.message);
    }
  }

  if (vector) {
    try {
      await Promise.all([
        vector.storeEmbedding(query, "chat_message", { intent: result.taskType, role: "user" }).catch(() => null),
        vector.storeEmbedding(result.response, "chat_message", { intent: result.taskType, role: "assistant" }).catch(() => null),
        vector.storeChatHistory(query, result.response, result.taskType).catch(() => null),
      ]);
    } catch (e) {
      console.warn("保存对话历史失败:", e.message);
    } finally {
      vector.close();
    }
  }

  if (enableGrowth) {
    try {
      const growth = new GrowthTracker();
      growth.recordUserActivity("chat_query", {
        query,
        intent: result.taskType,
        usedLLM: !!result.data?.llmAnalysis,
        timestamp: new Date().toISOString(),
      });
      growth.close();
    } catch (e) {
      console.warn("成长系统记录失败:", e.message);
    }
  }

  return {
    intent: result.taskType,
    query,
    response: result.response,
    data: result.data,
    taskType: result.taskType,
    workflowSummary: result.workflowSummary,
    executionHistory: result.executionHistory,
    context: result.context,
    timestamp: new Date().toISOString(),
  };
}

export function createEnhancedChatRouter({ repository }) {
  const router = express.Router();

  router.post("/api/chat/enhanced", async (req, res) => {
    try {
      const { message, enableVector, enableGrowth, conversationContext } = req.body;
      if (!message || typeof message !== "string") {
        return res.status(400).json({ error: "请提供 message 参数" });
      }

      const result = await buildEnhancedChatResponse(message, repository, {
        enableVector: enableVector !== false,
        enableGrowth: enableGrowth !== false,
        conversationContext: conversationContext || {},
      });
      res.json(result);
    } catch (error) {
      console.error("Enhanced chat error:", error);
      res.status(500).json({ error: error.message });
    }
  });

  router.post("/api/chat/workflow", async (req, res) => {
    try {
      const { message, conversationContext, sessionId } = req.body;
      if (!message || typeof message !== "string") {
        return res.status(400).json({ error: "请提供 message 参数" });
      }

      const engine = new WorkflowEngine();
      engine.context.input = conversationContext || {};
      // 传递对话历史给 WorkflowEngine，支持连续对话
      // 小白讲解：把之前的聊天记录传给AI，这样它才能理解你的追问
      const chatHistory = conversationContext?.chatHistory || [];
      const result = await engine.processUserQuery(message, chatHistory);

      // 保存对话到数据库，让刷新后还能看到历史记录
      // 小白讲解：就像把聊天记录存到日记本里，下次打开还能翻看
      try {
        const vector = new VectorMemory();
        vector.storeChatHistory(message, result.response || "", result.taskType || "chat");
        vector.close();
      } catch (e) {
        console.warn("保存对话历史失败（不影响本次回复）:", e.message);
      }

      // 如果传了 sessionId，把消息保存到对应的会话中
      // 对应 Codex 的 rollout 保存机制：每条消息都写入 session
      if (sessionId) {
        try {
          const svc = new SessionService();
          svc.addMessage(sessionId, "user", message, null);
          svc.addMessage(sessionId, "assistant", result.response || "", result.taskType || "chat");
          svc.close();
        } catch (e) {
          console.warn("保存会话消息失败（不影响本次回复）:", e.message);
        }
      }

      res.json(result);
    } catch (error) {
      console.error("Workflow chat error:", error);
      res.status(500).json({ error: error.message });
    }
  });

  router.get("/api/chat/workflow-status", (req, res) => {
    res.json({
      success: true,
      message: "Workflow 引擎运行正常",
      availableTaskTypes: [
        { id: "stock_deep_analysis", name: "股票深度分析", description: "对指定股票进行全面深度研究分析" },
        { id: "value_score", name: "价值评分", description: "计算股票的 VFM 价值评分" },
        { id: "opportunity_scan", name: "机会扫描", description: "扫描市场中的投资机会" },
        { id: "discovery", name: "新发现", description: "发现新的潜在投资标的" },
        { id: "market_news", name: "市场新闻", description: "获取最新的市场新闻和公告" },
        { id: "portfolio_review", name: "组合回顾", description: "回顾当前组合的表现和风险状况" },
        { id: "daily_brief", name: "每日简报", description: "汇总当天的市场变化和研究更新" },
        { id: "thesis_update", name: "投资论更新", description: "更新或验证投资论点" },
        { id: "risk_analysis", name: "风险分析", description: "分析股票或组合的风险状况" },
        { id: "competitor_analysis", name: "竞争对手分析", description: "分析股票的竞争对手和行业格局" },
        { id: "trend_analysis", name: "趋势分析", description: "分析股票的价格趋势和技术形态" },
        { id: "chat", name: "自由对话", description: "自由聊天" },
      ],
      availableTools: [
        "resolve_entity", "get_stock_data", "get_news", "get_top_gainers", "get_top_losers",
        "get_volume_surge", "get_price_movement", "get_valuation_extremes", "get_latest_news",
        "get_pool_snapshot", "query_memory", "save_memory", "get_value_score", "get_decisions",
        "create_decision", "run_discovery", "analyze_with_llm",
      ],
    });
  });

  return router;
}