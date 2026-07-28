/**
 * ConversationTaskRouterV2 - V2 版对话任务路由器
 *
 * 功能说明：
 *   这是 V2 版的路由器，替代旧的 isFollowUpQuestion + analyzeAndPlan 路径。
 *   它接收用户自然语言和会话状态，输出一个 ResearchTaskEnvelope。
 *   核心改进：
 *   - 追问不再降级为通用聊天
 *   - 只能选择已注册的任务图
 *   - 路由结果和理由可审计
 *   - 支持四种任务关系
 *
 * 参数说明：
 *   constructor({ registry, llmRouter }) - 创建路由器
 *   route(userQuery, { sessionState, chatHistory }) - 路由用户输入
 *
 * 返回值说明：
 *   route() 返回 ResearchTaskEnvelope，包含：
 *   - task_type: 任务类型（必须已注册）
 *   - entities: 实体列表
 *   - topic: 主题
 *   - relation_to_previous: 任务关系
 *   - flow: 执行流程
 *   - reasoning: 路由理由
 *   - routingTrace: 审计追踪
 *
 * 异常处理：
 *   LLM 不可用时降级为 chat
 *   LLM 返回未注册任务时降级为 chat
 */

/**
 * 小白讲解：
 *   这个文件是"翻译官"——把用户说的话翻译成系统能执行的任务。
 *   它的工作流程：
 *   1. 先检查是不是追问（继续/那第二个呢/不对市值是260亿）
 *   2. 如果是追问，根据上一轮任务决定关系（continue/derive/correct）
 *   3. 如果不是追问，让 LLM 判断任务类型
 *   4. 检查 LLM 返回的任务是否在注册表中
 *   5. 如果不在，降级为通用聊天
 *   6. 输出包含审计追踪的任务信封
 */

import { resolveTaskRelation, isFollowUpQuestion, validateTaskEnvelope } from "./research-task-contracts.js";
import { createChatCompletion } from "./llm-service.js";
import { resolveKnownTickers, STOCK_NAME_MAP } from "./security-aliases.js";

const LEGACY_TASK_ALIASES = Object.freeze({
  stock_deep_analysis: "stock_deep_dive",
  multi_stock_comparison: "pair_switch_decision",
  value_score: "operating_driver_valuation",
  discovery: "theme_expectation_gap",
});

function normalizeTaskType(taskType) {
  const normalized = String(taskType || "").trim();
  return LEGACY_TASK_ALIASES[normalized] || normalized;
}

function entitiesFromQuery(userQuery) {
  return resolveKnownTickers(userQuery).map((ticker, index) => ({
    ticker,
    name: STOCK_NAME_MAP[ticker] || ticker,
    role: index === 0 ? "target" : "comparison",
  }));
}

export function detectDeterministicResearchTask(userQuery) {
  const query = String(userQuery || "").trim();
  if (!query) return null;
  const entities = entitiesFromQuery(query);

  if (/(纠正|更正|不对|错了|不是).*(市值|营收|收入|利润|EPS|PE|PB|估值)/i.test(query)
      || /(市值|营收|收入|利润|EPS|PE|PB|估值).*(不对|错了|不是)/i.test(query)) {
    return { task_type: "claim_correction", entities, confidence: 0.99, reason: "明确的事实纠错请求" };
  }
  if (/(信号跟踪|跟踪计划|信号计划|监测计划|90\s*天|认证.*工厂|工厂.*出货|出货节奏)/i.test(query)) {
    return { task_type: "company_signal_plan", entities, confidence: 0.98, reason: "明确的公司信号跟踪请求" };
  }
  if (/(换仓|调仓|换成|替换|换掉|二选一)/i.test(query) && entities.length >= 2) {
    return { task_type: "pair_switch_decision", entities, confidence: 0.98, reason: "明确的双标的换仓请求" };
  }
  if (/(经营驱动|驱动估值|目标价|估值模型|情景估值|盈利预测)/i.test(query) && entities.length >= 1) {
    return { task_type: "operating_driver_valuation", entities, confidence: 0.97, reason: "明确的经营驱动估值请求" };
  }
  if (/(预期差|主题筛选|候选池|产业主题).*(筛选|排序|标的|候选|弹性)/i.test(query)
      || /(筛选|排序).*(预期差|主题|候选)/i.test(query)) {
    return { task_type: "theme_expectation_gap", entities, confidence: 0.96, reason: "明确的主题预期差筛选请求" };
  }
  if (/(为什么|因果|传导|催化缺失|没有催化|没行情|没有行情|兑现时滞)/i.test(query)
      && /(产业|行业|需求|订单|催化|行情|传导)/i.test(query)) {
    return { task_type: "industry_causal_explainer", entities, confidence: 0.95, reason: "明确的产业因果解释请求" };
  }
  if (/(深度分析|深度研究|完整研报|全面分析|公司研究)/i.test(query) && entities.length >= 1) {
    return { task_type: "stock_deep_dive", entities, confidence: 0.96, reason: "明确的个股深度研究请求" };
  }
  return null;
}

export function createRegistryLlmRouter(registry) {
  return async (userQuery, { chatHistory = [], previousTask = null } = {}) => {
    const taskMenu = registry.list().map((graph) => ({
      id: graph.id,
      name: graph.name,
      description: graph.description,
      requiresEntity: graph.requiresEntity,
    }));
    const recentHistory = chatHistory.slice(-6).map((item) => ({
      role: item.role,
      content: String(item.content || "").slice(0, 300),
    }));
    const prompt = [
      "你是投研产品的意图路由器。只能从给定 task_type 菜单中选择一个任务。",
      "不要规划工具，不要回答研究问题。输出纯 JSON。",
      `任务菜单：${JSON.stringify(taskMenu)}`,
      `上一任务：${JSON.stringify(previousTask || null)}`,
      `最近对话：${JSON.stringify(recentHistory)}`,
      `用户输入：${userQuery}`,
      '输出格式：{"task_type":"菜单中的ID","entities":[{"ticker":"证券代码","name":"公司名","role":"target"}],"topic":"任务主题","confidence":0.0,"reasoning":"简短理由"}',
    ].join("\n");
    const result = await createChatCompletion([{ role: "user", content: prompt }], {
      temperature: 0,
      maxTokens: 600,
    });
    const text = String(result.content || "").replace(/```json\s*|```\s*/gi, "");
    const start = text.indexOf("{");
    const end = text.lastIndexOf("}");
    if (start < 0 || end <= start) throw new Error("LLM router returned no JSON object");
    const parsed = JSON.parse(text.slice(start, end + 1));
    return { ...parsed, task_type: normalizeTaskType(parsed.task_type) };
  };
}

export class ConversationTaskRouterV2 {
  /**
   * 构造函数
   *
   * @param {Object} options
   * @param {Object} options.registry - TaskGraphRegistry 实例
   * @param {Function} options.llmRouter - LLM 路由函数 (query, context) => { task_type, entities, ... }
   */
  constructor({ registry, llmRouter }) {
    this.registry = registry;
    this.llmRouter = llmRouter;
  }

  /**
   * 路由用户输入
   *
   * @param {string} userQuery - 用户输入
   * @param {Object} options
   * @param {Object|null} options.sessionState - 会话状态（ResearchSessionState 或兼容对象）
   * @param {Array} options.chatHistory - 聊天历史
   * @returns {Object} ResearchTaskEnvelope
   */
  async route(userQuery, { sessionState, chatHistory = [] } = {}) {
    const timestamp = new Date().toISOString();
    const previousTask = sessionState?.getCurrentTask?.() || null;

    // === 第一步：检查是否是追问或纠错 ===
    // 小白讲解：先看用户是不是在追问上一轮的内容，或者在纠正上一轮的数据。
    // isFollowUpQuestion 检测"继续/接着/刚才"等关键词，
    // resolveTaskRelation 则能进一步检测纠错（"不是""错了"）和派生（"那...呢"）。
    // 两者任一命中且有上轮任务时，直接使用关系解析结果，不走 LLM。
    if (previousTask) {
      const relationEnvelope = resolveTaskRelation(userQuery, previousTask);

      // 只有当关系不是 new_task 时才走追问路径
      if (relationEnvelope.relation_to_previous !== "new_task") {
        // 从注册表获取任务图
        const graph = this.registry.get(relationEnvelope.task_type);
        if (graph) {
          const envelope = {
            task_type: graph.id,
            name: graph.name,
            entities: relationEnvelope.entities || [],
            topic: relationEnvelope.topic || previousTask.topic,
            relation_to_previous: relationEnvelope.relation_to_previous,
            parent_task_id: previousTask.taskId,
            flow: [...graph.defaultFlow],
            allowedTools: [...graph.allowedTools],
            artifactType: graph.artifactType,
            reasoning: relationEnvelope.reasoning || `追问关系: ${relationEnvelope.relation_to_previous}`,
            confidence: relationEnvelope.confidence || 0.9,
            correctionTarget: relationEnvelope.correctionTarget || null,
            confirmedFacts: relationEnvelope.confirmedFacts || [],
            routingTrace: {
              timestamp,
              step: "follow_up_detection",
              llmResult: null,
              followUpRelation: relationEnvelope.relation_to_previous,
              finalTaskType: graph.id,
              relation: relationEnvelope.relation_to_previous,
              previousTaskId: previousTask.taskId,
            },
          };
          return envelope;
        }
      }
    }

    // === 第二步：调用 LLM 路由 ===
    // 小白讲解：如果不是追问，或者追问但没有上轮任务，
    // 就让 LLM 判断用户想做什么类型的研究。
    let llmResult = null;
    let llmError = null;

    try {
      llmResult = await this.llmRouter(userQuery, { chatHistory, previousTask });
    } catch (error) {
      llmError = error.message;
    }

    const deterministic = detectDeterministicResearchTask(userQuery);
    if (deterministic && this.registry.has(deterministic.task_type)) {
      const modelTaskType = normalizeTaskType(llmResult?.task_type);
      if (!modelTaskType || modelTaskType === "chat" || modelTaskType !== deterministic.task_type) {
        llmResult = {
          ...llmResult,
          task_type: deterministic.task_type,
          entities: deterministic.entities.length > 0
            ? deterministic.entities
            : (llmResult?.entities || []),
          topic: llmResult?.topic || userQuery,
          confidence: deterministic.confidence,
          reasoning: modelTaskType && modelTaskType !== deterministic.task_type
            ? `高确定性语义校验纠偏：${modelTaskType} → ${deterministic.task_type}（${deterministic.reason}）`
            : deterministic.reason,
        };
        llmError = null;
      }
    }

    // === 第三步：验证 LLM 返回的任务类型 ===
    // 小白讲解：LLM 可能返回一个不存在的任务类型。
    // 这时系统会降级为通用聊天，而不是执行未注册的流程。
    let finalTaskType = "chat";
    let entities = [];
    let topic = userQuery;
    let reasoning = "";

    if (llmResult && !llmError) {
      const normalizedTaskType = normalizeTaskType(llmResult.task_type);
      if (this.registry.has(normalizedTaskType)) {
        // LLM 返回了已注册的任务类型
        finalTaskType = normalizedTaskType;
        entities = llmResult.entities || [];
        topic = llmResult.topic || userQuery;
        reasoning = llmResult.reasoning || `LLM 路由到 ${llmResult.task_type}`;
      } else {
        // LLM 返回了未注册的任务类型 → 降级为 chat
        reasoning = `LLM 返回未注册的任务类型 "${llmResult.task_type}"，降级为通用对话`;
      }
    } else if (llmError) {
      // LLM 不可用 → 降级为 chat
      reasoning = `LLM 不可用（${llmError}），降级为通用对话`;
    } else {
      reasoning = "LLM 未返回有效结果，降级为通用对话";
    }

    // === 第四步：从注册表获取流程 ===
    const graph = this.registry.get(finalTaskType);
    const flow = graph ? [...graph.defaultFlow] : ["query_memory", "analyze_with_llm"];
    const allowedTools = graph ? [...graph.allowedTools] : ["query_memory", "analyze_with_llm"];
    const artifactType = graph ? graph.artifactType : "text";

    // === 第五步：构建可审计的信封 ===
    const envelope = {
      task_type: finalTaskType,
      name: graph?.name || "自由对话",
      entities,
      topic,
      relation_to_previous: previousTask ? "new_task" : "new_task",
      parent_task_id: previousTask?.taskId || null,
      flow,
      allowedTools,
      artifactType,
      reasoning,
      confidence: llmResult?.confidence || 0.5,
      routingTrace: {
        timestamp,
        step: "llm_routing",
        llmResult: llmResult || { error: llmError },
        followUpRelation: null,
        finalTaskType,
        relation: "new_task",
        previousTaskId: previousTask?.taskId || null,
      },
    };

    return envelope;
  }
}
