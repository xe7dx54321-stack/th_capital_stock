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
import Database from "better-sqlite3";
import path from "path";
import { fileURLToPath } from "url";
import { runWorkflow, WorkflowEngine } from "./workflow-engine.js";
import { VectorMemory } from "./vector-memory.js";
import { GrowthTracker } from "./growth-service.js";
import { SessionService } from "./session-service.js";
import { SessionStateStore } from "./research-session-state.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SESSION_STATE_DB_PATH = path.join(__dirname, "..", "..", "01_data", "db", "vector.db");

/**
 * 获取或创建 SessionStateStore 单例
 *
 * 小白讲解：这是"记忆笔记本"的总管。
 * 它通过 vector.db 复用同一个连接，确保所有会话状态集中管理。
 * 用单例模式避免每次请求都打开新连接。
 */
let _sessionStateStoreInstance = null;
export function getSessionStateStore() {
  if (_sessionStateStoreInstance) return _sessionStateStoreInstance;
  try {
    const db = new Database(SESSION_STATE_DB_PATH);
    // 确保表存在（与 0008 迁移一致）
    db.exec(`
      CREATE TABLE IF NOT EXISTS research_session_state (
        session_id TEXT PRIMARY KEY,
        state_json TEXT NOT NULL,
        updated_at TEXT NOT NULL
      );
      CREATE INDEX IF NOT EXISTS idx_research_session_state_updated
        ON research_session_state(updated_at);
    `);
    _sessionStateStoreInstance = new SessionStateStore(db);
    return _sessionStateStoreInstance;
  } catch (error) {
    console.error("[getSessionStateStore] 初始化失败:", error.message);
    return null;
  }
}

export function formatPersistedAssistantMessage(result) {
  // 会话正文只保存用户真正要阅读的结果。运行编号、质量门和制品入口属于
  // 结构化元数据，由前台独立展示；把它们拼进 Markdown 会污染长篇报告。
  return String(result?.response || "").trim();
}

export async function buildEnhancedChatResponse(query, repository, options = {}) {
  const {
    enableVector = true,
    enableGrowth = true,
    conversationContext = {},
    auditService = null,
    governedWorkflowRunner = null,
  } = options;

  const result = await executeAuditedWorkflowChat({
    message: query,
    conversationContext,
    auditService,
    governedWorkflowRunner,
  });

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
    status: result.status,
    run_id: result.run_id,
    artifacts: result.artifacts || [],
    context: result.context,
    timestamp: new Date().toISOString(),
  };
}

export async function executeAuditedWorkflowChat({
  message,
  conversationContext = {},
  sessionId = null,
  auditService = null,
  governedWorkflowRunner = null,
  onResearchProgress = null,
  engineFactory = (options) => new WorkflowEngine(options),
}) {
  const chatHistory = Array.isArray(conversationContext?.chatHistory)
    ? conversationContext.chatHistory
    : [];
  const runId = auditService?.startChatRun({
    message,
    sessionId,
    chatHistoryCount: chatHistory.length,
  }) || null;
  // === 接入 SessionStateStore ===
  // 小白讲解：把"记忆笔记本"的管理员传给 WorkflowEngine，
  // 这样每次对话都会自动加载上轮状态、对话后自动保存。
  const sessionStateStore = getSessionStateStore();
  const engine = engineFactory({
    onEvent: runId ? (entry) => auditService.recordEngineEvent(runId, entry) : null,
    runId,
    governedWorkflowRunner,
    onResearchProgress,
    sessionId,
    sessionStateStore,
  });

  // HTTP 对话上下文只携带历史消息，不接受写记忆或写决策授权标志。
  engine.context.input = {};
  try {
    const result = await engine.processUserQuery(message, chatHistory);
    if (!runId) return result;
    const audited = auditService.completeChatRun(runId, { message, sessionId, result });
    const governedArtifacts = result.data?.governedWorkflow?.artifacts || [];
    return {
      ...result,
      run_id: runId,
      governed_run_id: result.data?.governedWorkflow?.run_id || null,
      artifacts: [...governedArtifacts, ...audited.artifacts],
    };
  } catch (error) {
    if (runId) {
      try {
        auditService.failChatRun(runId, error);
      } catch (auditError) {
        console.error("记录失败任务审计信息失败:", auditError.message);
      }
      error.runId = runId;
    }
    throw error;
  }
}

function writeSseEvent(res, eventName, payload) {
  if (res.writableEnded || res.destroyed) return false;
  return res.write(`event: ${eventName}\ndata: ${JSON.stringify(payload)}\n\n`);
}

function persistCompletedChat({ message, result, sessionId }) {
  try {
    const vector = new VectorMemory();
    vector.storeChatHistory(message, result.response || "", result.taskType || "chat");
    vector.close();
  } catch (error) {
    console.warn("保存对话历史失败（不影响本次回复）:", error.message);
  }

  if (!sessionId) return;
  try {
    const service = new SessionService();
    service.addMessage(sessionId, "user", message, null);
    service.addMessage(sessionId, "assistant", formatPersistedAssistantMessage(result), result.taskType || "chat");
    service.close();
  } catch (error) {
    console.warn("保存会话消息失败（不影响本次回复）:", error.message);
  }
}

export function createEnhancedChatRouter({
  repository,
  workflowChatExecutor = executeAuditedWorkflowChat,
  persistChat = persistCompletedChat,
}) {
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
        auditService: req.app.locals.workflowAuditService || null,
        governedWorkflowRunner: req.app.locals.governedWorkflowRunner || null,
      });
      res.json(result);
    } catch (error) {
      console.error("Enhanced chat error:", error);
      res.status(500).json({ error: error.message, run_id: error.runId || null });
    }
  });

  router.post("/api/chat/workflow", async (req, res) => {
    try {
      const { message, conversationContext, sessionId } = req.body;
      if (!message || typeof message !== "string") {
        return res.status(400).json({ error: "请提供 message 参数" });
      }

      const result = await workflowChatExecutor({
        message,
        conversationContext: conversationContext || {},
        sessionId: sessionId || null,
        auditService: req.app.locals.workflowAuditService || null,
        governedWorkflowRunner: req.app.locals.governedWorkflowRunner || null,
      });

      // 保存对话到数据库，让刷新后还能看到历史记录
      // 小白讲解：就像把聊天记录存到日记本里，下次打开还能翻看
      persistChat({ message, result, sessionId });

      res.json(result);
    } catch (error) {
      console.error("Workflow chat error:", error);
      res.status(500).json({ error: error.message, run_id: error.runId || null });
    }
  });

  router.post("/api/chat/workflow/stream", async (req, res) => {
    const { message, conversationContext, sessionId } = req.body || {};
    if (!message || typeof message !== "string") {
      return res.status(400).json({ error: "请提供 message 参数" });
    }

    res.status(200);
    res.set({
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    });
    res.flushHeaders?.();

    let clientConnected = true;
    res.on("close", () => {
      clientConnected = false;
    });
    const heartbeat = setInterval(() => {
      if (clientConnected && !res.writableEnded) res.write(": heartbeat\n\n");
    }, 15_000);
    heartbeat.unref?.();

    writeSseEvent(res, "connected", {
      status: "connected",
      message: "研究连接已建立",
      timestamp: new Date().toISOString(),
    });

    try {
      const result = await workflowChatExecutor({
        message,
        conversationContext: conversationContext || {},
        sessionId: sessionId || null,
        auditService: req.app.locals.workflowAuditService || null,
        governedWorkflowRunner: req.app.locals.governedWorkflowRunner || null,
        onResearchProgress: async (progress) => {
          if (!clientConnected) throw new Error("client disconnected");
          writeSseEvent(res, "research_progress", progress);
        },
      });
      persistChat({ message, result, sessionId });
      if (clientConnected) writeSseEvent(res, "result", result);
    } catch (error) {
      console.error("Streaming workflow chat error:", error);
      if (clientConnected) {
        writeSseEvent(res, "error", {
          error: error.message,
          run_id: error.runId || null,
        });
      }
    } finally {
      clearInterval(heartbeat);
      if (clientConnected && !res.writableEnded) res.end();
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
        { id: "market_attribution", name: "涨跌幅归因", description: "用榜单与巨潮公告交叉核对异动线索" },
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
        "get_volume_surge", "get_price_movement", "get_valuation_extremes", "get_latest_news", "get_movement_news",
        "get_pool_snapshot", "query_memory", "get_value_score", "get_decisions",
        "run_discovery", "analyze_with_llm",
        "run_governed_stock_deep_dive",
      ],
    });
  });

  return router;
}
