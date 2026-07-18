/**
 * Agent 编排器 - 多轮对话上下文管理器
 * 
 * 核心功能：
 *   1. 维护对话状态和上下文历史
 *   2. 调用 WorkflowEngine 处理用户查询
 *   3. 管理多轮对话的状态转换
 *   4. 提供统一的对话接口
 *   5. 支持流式响应和进度追踪
 * 
 * 小白讲解：
 *   这个服务就像一个"项目经理"，负责管理整个对话过程：
 *   - 记住之前聊了什么（上下文历史）
 *   - 调用工作流引擎处理当前问题
 *   - 跟踪每个任务的执行进度
 *   - 把结果整理好反馈给用户
 * 
 * 对话生命周期：
 *   开始对话 → 理解意图 → 规划流程 → 执行流程 → 返回结果 → 继续对话（循环）
 */

import express from "express";
import { WorkflowEngine, TASK_TYPES, AGENT_TOOLS, runWorkflow } from "./workflow-engine.js";

const CONVERSATION_TIMEOUT = 30 * 60 * 1000;

export class ConversationManager {
  constructor() {
    this.conversations = new Map();
    this.cleanupInterval = setInterval(() => this.cleanupExpired(), 5 * 60 * 1000);
  }

  createConversation() {
    const conversationId = `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const conversation = {
      id: conversationId,
      createdAt: Date.now(),
      lastActivityAt: Date.now(),
      history: [],
      workflowState: "idle",
      currentTask: null,
      context: {},
      workflowEngine: null,
    };
    this.conversations.set(conversationId, conversation);
    return conversation;
  }

  getConversation(conversationId) {
    const conversation = this.conversations.get(conversationId);
    if (!conversation) return null;
    
    conversation.lastActivityAt = Date.now();
    return conversation;
  }

  async processMessage(conversationId, message) {
    let conversation = this.getConversation(conversationId);
    if (!conversation) {
      conversation = this.createConversation();
    }

    conversation.history.push({
      role: "user",
      content: message,
      timestamp: Date.now(),
    });

    conversation.workflowState = "processing";

    try {
      const engine = new WorkflowEngine();
      engine.context.history = conversation.history;
      engine.context.input = conversation.context || {};
      
      const result = await engine.processUserQuery(message);
      
      conversation.currentTask = result.taskType;
      conversation.workflowState = result.status;
      conversation.context = result.data;
      conversation.workflowEngine = engine;

      const assistantResponse = {
        role: "assistant",
        content: result.response,
        timestamp: Date.now(),
        taskType: result.taskType,
        workflowSummary: result.workflowSummary,
        executionHistory: result.executionHistory,
      };
      conversation.history.push(assistantResponse);

      return {
        conversationId: conversation.id,
        ...result,
        conversationHistory: conversation.history,
      };
    } catch (error) {
      conversation.workflowState = "error";
      const errorResponse = {
        role: "assistant",
        content: `处理失败：${error.message}`,
        timestamp: Date.now(),
        taskType: "error",
        error: error.message,
      };
      conversation.history.push(errorResponse);

      return {
        conversationId: conversation.id,
        status: "error",
        response: `处理失败：${error.message}`,
        error: error.message,
        conversationHistory: conversation.history,
      };
    }
  }

  cleanupExpired() {
    const now = Date.now();
    for (const [id, conversation] of this.conversations) {
      if (now - conversation.lastActivityAt > CONVERSATION_TIMEOUT) {
        this.conversations.delete(id);
      }
    }
  }

  close() {
    clearInterval(this.cleanupInterval);
    this.conversations.clear();
  }
}

export class AgentOrchestrator {
  constructor() {
    this.conversationManager = new ConversationManager();
  }

  async handleUserMessage(message, conversationId = null) {
    const result = await this.conversationManager.processMessage(conversationId, message);
    return result;
  }

  getConversation(conversationId) {
    return this.conversationManager.getConversation(conversationId);
  }

  getTaskTypes() {
    return Object.values(TASK_TYPES).map(t => ({
      id: t.id,
      name: t.name,
      description: t.description,
      requiresEntity: t.requiresEntity,
      defaultFlow: t.defaultFlow,
      tools: t.tools.map(toolId => AGENT_TOOLS[toolId]).filter(Boolean),
    }));
  }

  getTools() {
    return Object.values(AGENT_TOOLS);
  }

  async runTask(taskType, input, conversationId = null) {
    const task = TASK_TYPES[taskType];
    if (!task) throw new Error("无效的 taskType");

    const engine = new WorkflowEngine();
    engine.setInput(input);
    
    if (input?.ticker) {
      engine.context.data.currentTicker = input.ticker;
    }
    
    const result = await engine.executeFlow(task.defaultFlow);
    
    if (conversationId) {
      const conversation = this.getConversation(conversationId);
      if (conversation) {
        conversation.history.push({
          role: "assistant",
          content: result.response,
          timestamp: Date.now(),
          taskType,
          workflowSummary: result.workflowSummary,
        });
      }
    }
    
    return result;
  }
}

export function createAgentRouter() {
  const router = express.Router();
  const orchestrator = new AgentOrchestrator();

  router.post("/api/agent/message", async (req, res) => {
    try {
      const { message, conversationId } = req.body;
      if (!message || typeof message !== "string") {
        return res.status(400).json({ error: "请提供 message 参数" });
      }

      const result = await orchestrator.handleUserMessage(message, conversationId);
      res.json(result);
    } catch (error) {
      console.error("Agent message error:", error);
      res.status(500).json({ error: error.message });
    }
  });

  router.get("/api/agent/conversation/:id", (req, res) => {
    try {
      const conversation = orchestrator.getConversation(req.params.id);
      if (!conversation) {
        return res.status(404).json({ error: "对话不存在" });
      }
      res.json(conversation);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  router.get("/api/agent/task-types", (_req, res) => {
    try {
      res.json({ taskTypes: orchestrator.getTaskTypes() });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  router.get("/api/agent/tools", (_req, res) => {
    try {
      res.json({ tools: orchestrator.getTools() });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  router.post("/api/agent/run-task", async (req, res) => {
    try {
      const { taskType, input, conversationId } = req.body;
      if (!taskType || !TASK_TYPES[taskType]) {
        return res.status(400).json({ error: "无效的 taskType" });
      }

      const result = await orchestrator.runTask(taskType, input || {}, conversationId);
      res.json(result);
    } catch (error) {
      console.error("Agent run task error:", error);
      res.status(500).json({ error: error.message });
    }
  });

  return router;
}

export async function runAgentWorkflow(query) {
  return await runWorkflow(query);
}