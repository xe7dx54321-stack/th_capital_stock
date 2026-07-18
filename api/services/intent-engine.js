/**
 * LLM意图引擎 - 自然语言理解与任务拆解核心
 *
 * 核心功能：
 *   1. 理解用户自然语言查询，识别意图
 *   2. 识别实体（股票代码、行业、关键词等）
 *   3. 动态规划执行流程（选择工具、排序）
 *   4. 支持上下文感知（多轮对话）
 *
 * 设计理念：
 *   - 用户不需要学习命令格式，想怎么说就怎么说
 *   - LLM是"大脑"，负责理解和规划
 *   - 工具是"手脚"，负责执行具体操作
 *   - 系统自动组装流程，不需要人工配置
 *
 * 小白讲解：
 *   这个引擎就像一个"翻译官"，把你的人话翻译成系统能懂的指令：
 *   - 你说"NVDA大涨，A股有机会吗？"
 *   - 它翻译成：先查NVDA数据 → 找A股映射 → 分析A股机会 → 生成报告
 *   - 然后指挥各个工具按顺序执行
 */

import { createChatCompletion } from "./llm-service.js";

/**
 * 意图分析结果结构
 */
class IntentResult {
  constructor(data) {
    this.intent = data.intent || "chat";
    this.intentName = data.intentName || "自由对话";
    this.entities = data.entities || {};
    this.requiredTools = data.requiredTools || [];
    this.expectedOutput = data.expectedOutput || "";
    this.isDynamic = data.isDynamic || false;
    this.reasoning = data.reasoning || "";
  }
}

/**
 * 意图引擎类
 */
export class IntentEngine {
  constructor() {
    this.availableTools = null;
    this.availableTasks = null;
  }

  setAvailableTools(tools) {
    this.availableTools = tools;
  }

  setAvailableTasks(tasks) {
    this.availableTasks = tasks;
  }

  async getTools() {
    if (!this.availableTools) {
      const { AGENT_TOOLS } = await import("./workflow-engine.js");
      this.availableTools = AGENT_TOOLS;
    }
    return this.availableTools;
  }

  async getTasks() {
    if (!this.availableTasks) {
      const { TASK_TYPES } = await import("./workflow-engine.js");
      this.availableTasks = TASK_TYPES;
    }
    return this.availableTasks;
  }

  /**
   * 将工具列表格式化为LLM可读的描述
   */
  async formatToolsForLLM() {
    const availableTools = await this.getTools();
    const tools = [];
    for (const [id, tool] of Object.entries(availableTools)) {
      tools.push({
        id,
        name: tool.name,
        description: tool.description,
        input: tool.inputSchema?.properties || {},
      });
    }
    return JSON.stringify(tools, null, 2);
  }

  /**
   * 将任务类型格式化为LLM可读的描述
   */
  async formatTasksForLLM() {
    const availableTasks = await this.getTasks();
    const tasks = [];
    for (const [key, task] of Object.entries(availableTasks)) {
      tasks.push({
        id: task.id,
        name: task.name,
        description: task.description,
        requiresEntity: task.requiresEntity || false,
        tools: task.tools || [],
      });
    }
    return JSON.stringify(tasks, null, 2);
  }

  /**
   * 解析用户自然语言查询，返回结构化意图
   *
   * 参数：
   *   userQuery: 用户输入的自然语言
   *   context: 上下文（可选，包含对话历史、已有数据等）
   *   chatHistory: 对话历史（可选，用于理解追问）
   *
   * 返回：
   *   IntentResult 对象，包含意图、实体、工具列表、期望输出
   */
  async parseIntent(userQuery, context = {}, chatHistory = []) {
    console.log(`[intent] 开始解析用户查询: "${userQuery}"`);

    const toolsDesc = await this.formatToolsForLLM();
    const tasksDesc = await this.formatTasksForLLM();

    // 修复：精简 context 描述，避免把完整 context 序列化（太长且浪费 token）
    // 只提取关键信息：已有数据摘要、当前任务类型
    const contextSummary = {
      currentTaskType: context.currentTaskType || null,
      hasInstrumentData: !!context.data?.instrumentData,
      hasStockEntity: !!context.data?.stockEntity,
      currentTicker: context.data?.currentTicker || null,
      stockName: context.data?.stockEntity?.name || null,
    };

    // 构建对话历史摘要（最近3轮，每条最多200字）
    let chatHistoryDesc = "无历史对话";
    if (chatHistory && chatHistory.length > 0) {
      const recent = chatHistory.slice(-6);
      chatHistoryDesc = recent.map(msg =>
        `${msg.role === "user" ? "用户" : "助手"}: ${msg.content.substring(0, 200)}`
      ).join("\n");
    }

    const contextDesc = JSON.stringify(contextSummary, null, 2);

    const prompt = `
你是一个专业的投研助手，负责理解用户的自然语言查询并拆解为可执行的任务。

## 用户查询
${userQuery}

## 对话历史（重要！用于理解追问）
${chatHistoryDesc}

## 上下文（已有信息）
${contextDesc}

## 可用任务类型
${tasksDesc}

## 可用工具
${toolsDesc}

## 你的任务
1. 分析用户查询的意图（特别注意：如果是对之前对话的追问，应识别为chat类型）
2. 识别实体（股票代码、行业、关键词等）
3. 规划执行流程（选择需要的工具，按执行顺序排列）
4. 判断是否需要动态流程（isDynamic=true表示由LLM决定顺序，false表示使用预设流程）

## 输出格式（必须是纯JSON，不要包含其他文字）
{
  "intent": "任务类型ID或custom",
  "intentName": "任务名称",
  "entities": {
    "usTicker": "美股代码（如有）",
    "aShareTicker": "A股代码（如有）",
    "sector": "行业（如有）",
    "keywords": ["关键词列表"],
    "focus": "用户关注的重点（如：机会、风险、原因等）"
  },
  "requiredTools": ["工具ID列表，按执行顺序排列"],
  "expectedOutput": "期望的输出内容描述",
  "isDynamic": true或false,
  "reasoning": "你的分析和决策理由"
}

## 规则
- 如果用户提到美股（如NVDA、TSLA、AAPL），必须先调用get_us_data获取美股数据
- 如果用户问A股映射或关联，必须调用find_us_mapping查找映射关系
- 如果用户问A股投资机会，必须调用get_stock_data获取A股数据
- 最后必须调用analyze_with_llm进行综合分析
- 如果用户查询比较简单（如闲聊），可以只调用analyze_with_llm
- **重要**：如果用户是对之前对话的追问（如"继续"、"接着说"、"补充一下"），intent应为"chat"，requiredTools只需["analyze_with_llm"]
- isDynamic=true表示流程由你决定，false表示使用预设的defaultFlow
- requiredTools必须按执行顺序排列，前一个工具的输出可能是后一个工具的输入
`;

    try {
      const result = await createChatCompletion([{ role: "user", content: prompt }]);
      console.log(`[intent] LLM返回结果: ${result.content.substring(0, 200)}...`);

      const jsonStr = this.extractJSON(result.content);
      const parsed = JSON.parse(jsonStr);

      const intentResult = new IntentResult(parsed);
      console.log(`[intent] 解析成功: intent=${intentResult.intent}, tools=${intentResult.requiredTools.length}个`);

      return intentResult;
    } catch (error) {
      console.error("[intent] 解析失败:", error.message);
      return this.createFallbackIntent(userQuery);
    }
  }

  /**
   * 从LLM返回中提取JSON
   * 修复：清理markdown标记和多余字符，提高JSON解析容错性
   */
  extractJSON(text) {
    // 去掉markdown代码块标记
    let cleaned = text.replace(/```json\s*/g, "").replace(/```\s*/g, "");
    // 找到第一个{和最后一个}
    const start = cleaned.indexOf("{");
    const end = cleaned.lastIndexOf("}");
    if (start >= 0 && end > start) {
      return cleaned.substring(start, end + 1);
    }
    return text;
  }

  /**
   * 创建回退意图（当LLM解析失败时使用）
   * 修复：增加更多关键词匹配，覆盖"扫描投资机会"、"每日复盘"等常见场景
   */
  createFallbackIntent(userQuery) {
    const isUsStock = /\b(NVDA|AMD|INTC|MSFT|GOOGL|AAPL|TSLA|META|AMZN|NFLX|BABA|TCEHY|JD|NIO)\b/i.test(userQuery);
    const isAShare = /\b(\d{6}\.(SZ|SH|BJ|HK))\b/i.test(userQuery) ||
                     /\b(海光信息|中际旭创|宁德时代|比亚迪|贵州茅台)\b/.test(userQuery);
    const hasMapping = userQuery.includes("映射") || userQuery.includes("关联") ||
                       userQuery.includes("对标") || userQuery.includes("联动");
    const hasAnalysis = userQuery.includes("分析") || userQuery.includes("研究") ||
                        userQuery.includes("机会") || userQuery.includes("风险");

    // 修复：增加任务类型关键词匹配
    // 小白讲解：当LLM的JSON解析失败时，用关键词来猜测用户意图
    const hasScan = userQuery.includes("扫描") || userQuery.includes("扫描一下");
    const hasBrief = userQuery.includes("复盘") || userQuery.includes("简报") ||
                     userQuery.includes("每日") || userQuery.includes("今天") && userQuery.includes("市场");
    const hasRisk = userQuery.includes("风险分析") || userQuery.includes("风险评估");

    let intent = "chat";
    let tools = ["analyze_with_llm"];
    let intentName = "自由对话";

    // 优先级：美股映射 > 美股分析 > A股分析 > 机会扫描 > 每日简报 > 风险分析 > 自由对话
    if (isUsStock && hasMapping) {
      intent = "us_mapping_analysis";
      intentName = "美股映射分析";
      tools = ["get_us_data", "find_us_mapping", "analyze_mapping_impact", "get_stock_data", "analyze_with_llm"];
    } else if (isUsStock && hasAnalysis) {
      intent = "stock_deep_analysis";
      intentName = "深度分析";
      tools = ["resolve_entity", "get_stock_data", "get_news", "analyze_with_llm"];
    } else if (isAShare && hasAnalysis) {
      intent = "stock_deep_analysis";
      intentName = "深度分析";
      tools = ["resolve_entity", "get_stock_data", "get_news", "analyze_with_llm"];
    } else if (hasScan) {
      // 修复：扫描投资机会 → opportunity_scan
      intent = "opportunity_scan";
      intentName = "机会扫描";
      tools = ["get_market_indices", "get_top_gainers", "get_top_losers", "get_volume_surge", "get_price_movement", "get_valuation_extremes", "get_latest_news", "get_pool_snapshot", "analyze_with_llm"];
    } else if (hasBrief) {
      // 修复：每日复盘/简报 → daily_brief
      intent = "daily_brief";
      intentName = "每日简报";
      tools = ["get_market_indices", "get_top_gainers", "get_top_losers", "get_volume_surge", "get_latest_news", "get_pool_snapshot", "get_decisions", "analyze_with_llm"];
    } else if (hasRisk) {
      intent = "risk_analysis";
      intentName = "风险分析";
      tools = ["get_market_indices", "get_top_losers", "get_volume_surge", "get_latest_news", "analyze_with_llm"];
    }

    return new IntentResult({
      intent,
      intentName,
      entities: {
        usTicker: isUsStock ? userQuery.match(/\b(NVDA|AMD|INTC|MSFT|GOOGL|AAPL|TSLA|META|AMZN|NFLX|NIO)\b/i)?.[0] || null : null,
        keywords: [userQuery],
      },
      requiredTools: tools,
      expectedOutput: "分析用户查询并给出回答",
      isDynamic: true,
      reasoning: "LLM解析失败，使用规则匹配",
    });
  }

  /**
   * 根据中间结果重新规划流程
   *
   * 参数：
   *   currentTool: 当前执行完的工具ID
   *   context: 当前上下文数据
   *   remainingTools: 剩余未执行的工具
   *
   * 返回：
   *   调整后的工具列表
   */
  async replanFlow(currentTool, context, remainingTools) {
    console.log(`[intent] 重新规划流程，当前工具: ${currentTool}`);

    const prompt = `
你正在执行一个投研任务，当前已完成工具：${currentTool}

## 当前上下文数据
${JSON.stringify(context, null, 2)}

## 剩余待执行工具
${JSON.stringify(remainingTools, null, 2)}

## 请判断是否需要调整流程
- 是否需要添加新的工具？
- 是否需要跳过某些工具？
- 是否需要调整执行顺序？

## 输出格式（纯JSON）
{
  "adjustments": [
    { "action": "add"|"remove"|"reorder", "toolId": "工具ID", "position": 0 }
  ],
  "reasoning": "调整理由"
}
`;

    try {
      const result = await createChatCompletion([{ role: "user", content: prompt }]);
      const jsonStr = this.extractJSON(result.content);
      const adjustments = JSON.parse(jsonStr);

      let newTools = [...remainingTools];

      for (const adj of adjustments.adjustments || []) {
        if (adj.action === "add") {
          newTools.splice(adj.position, 0, adj.toolId);
        } else if (adj.action === "remove") {
          newTools = newTools.filter(t => t !== adj.toolId);
        }
      }

      return newTools;
    } catch (error) {
      console.error("[intent] 重新规划失败:", error.message);
      return remainingTools;
    }
  }
}

export { IntentResult };