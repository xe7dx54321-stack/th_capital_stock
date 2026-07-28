/**
 * ConversationTaskRouterV2 测试
 *
 * 功能说明：
 *   测试 V2 版对话任务路由器。它接收用户自然语言输入和会话状态，
 *   输出一个 ResearchTaskEnvelope，包含任务类型、实体、关系和流程。
 *   与 V1 的区别：
 *   - 不再把追问降级为通用聊天
 *   - 只能选择已注册的任务图
 *   - 路由结果和理由可审计
 *   - 支持四种任务关系（continue/derive/correct/new_task）
 *
 * 参数说明：
 *   无直接参数，通过 mock 数据验证行为
 *
 * 返回值说明：
 *   所有测试应通过
 *
 * 异常处理：
 *   测试失败会抛出 assert.AssertionError
 */

import assert from "node:assert/strict";
import test from "node:test";

test("ConversationTaskRouterV2 routes new stock research to stock_deep_dive", async () => {
  const { ConversationTaskRouterV2 } = await import("../../api/services/conversation-task-router-v2.js");
  const { createDefaultRegistry } = await import("../../api/services/task-graph-registry.js");

  const registry = createDefaultRegistry();

  // Mock LLM 返回个股深研意图
  const mockLlmRouter = async (userQuery, context) => ({
    task_type: "stock_deep_dive",
    entities: [{ ticker: "688041.SH", name: "海光信息", role: "target" }],
    topic: userQuery,
    confidence: 0.9,
    reasoning: "用户要求分析特定股票",
  });

  const router = new ConversationTaskRouterV2({ registry, llmRouter: mockLlmRouter });

  const envelope = await router.route("分析一下海光信息", {
    sessionState: null,
    chatHistory: [],
  });

  assert.equal(envelope.task_type, "stock_deep_dive");
  assert.equal(envelope.entities[0].ticker, "688041.SH");
  assert.equal(envelope.relation_to_previous, "new_task");
  assert.ok(envelope.flow, "路由结果应包含执行流程");
  assert.ok(envelope.flow.includes("resolve_entity"), "流程应包含实体解析");
  assert.ok(envelope.reasoning, "路由结果应包含理由");
});

test("ConversationTaskRouterV2 routes continue to previous task type", async () => {
  const { ConversationTaskRouterV2 } = await import("../../api/services/conversation-task-router-v2.js");
  const { createDefaultRegistry } = await import("../../api/services/task-graph-registry.js");

  const registry = createDefaultRegistry();
  const mockLlmRouter = async () => ({ task_type: "chat", entities: [], confidence: 0.1 });

  const router = new ConversationTaskRouterV2({ registry, llmRouter: mockLlmRouter });

  // 模拟上一轮任务状态
  const sessionState = {
    getCurrentTask: () => ({
      taskId: "task_001",
      taskType: "stock_deep_dive",
      entities: [{ ticker: "688041.SH", role: "target" }],
      topic: "海光信息经营估值",
    }),
  };

  const envelope = await router.route("继续", { sessionState, chatHistory: [] });

  assert.equal(envelope.relation_to_previous, "continue");
  assert.equal(envelope.task_type, "stock_deep_dive");
  assert.equal(envelope.entities[0].ticker, "688041.SH");
});

test("ConversationTaskRouterV2 routes correction to claim_correction task", async () => {
  const { ConversationTaskRouterV2 } = await import("../../api/services/conversation-task-router-v2.js");
  const { createDefaultRegistry } = await import("../../api/services/task-graph-registry.js");

  const registry = createDefaultRegistry();
  const mockLlmRouter = async () => ({ task_type: "chat", entities: [], confidence: 0.1 });

  const router = new ConversationTaskRouterV2({ registry, llmRouter: mockLlmRouter });

  const sessionState = {
    getCurrentTask: () => ({
      taskId: "task_001",
      taskType: "theme_expectation_gap",
      entities: [{ ticker: "002396.SZ", name: "星网锐捷", role: "candidate" }],
      topic: "超节点预期差筛选",
    }),
  };

  const envelope = await router.route("星网锐捷市值是260亿，不是199亿", { sessionState, chatHistory: [] });

  assert.equal(envelope.relation_to_previous, "correct");
  assert.equal(envelope.task_type, "claim_correction");
  assert.ok(envelope.correctionTarget, "应包含纠错目标");
  assert.ok(envelope.flow, "应包含执行流程");
});

test("ConversationTaskRouterV2 rejects LLM returning unregistered task type", async () => {
  const { ConversationTaskRouterV2 } = await import("../../api/services/conversation-task-router-v2.js");
  const { createDefaultRegistry } = await import("../../api/services/task-graph-registry.js");

  const registry = createDefaultRegistry();

  // Mock LLM 返回未注册的任务类型
  const mockLlmRouter = async () => ({
    task_type: "hack_arbitrary_task",
    entities: [],
    confidence: 0.9,
  });

  const router = new ConversationTaskRouterV2({ registry, llmRouter: mockLlmRouter });

  // 应降级为 chat 而不是使用未注册的任务
  const envelope = await router.route("随便分析一下", { sessionState: null, chatHistory: [] });

  assert.equal(envelope.task_type, "chat",
    "未注册的任务类型应降级为 chat");
});

test("ConversationTaskRouterV2 handles LLM unavailability gracefully", async () => {
  const { ConversationTaskRouterV2 } = await import("../../api/services/conversation-task-router-v2.js");
  const { createDefaultRegistry } = await import("../../api/services/task-graph-registry.js");

  const registry = createDefaultRegistry();

  // Mock LLM 抛出异常
  const mockLlmRouter = async () => { throw new Error("LLM unavailable"); };

  const router = new ConversationTaskRouterV2({ registry, llmRouter: mockLlmRouter });

  const envelope = await router.route("分析一下海光信息", { sessionState: null, chatHistory: [] });

  // LLM 不可用时应降级为 chat
  assert.equal(envelope.task_type, "chat");
  assert.ok(envelope.reasoning.includes("不可用") || envelope.reasoning.includes("unavailable"),
    "理由应说明 LLM 不可用");
});

test("ConversationTaskRouterV2 derive routes to theme_expectation_gap from valuation", async () => {
  const { ConversationTaskRouterV2 } = await import("../../api/services/conversation-task-router-v2.js");
  const { createDefaultRegistry } = await import("../../api/services/task-graph-registry.js");

  const registry = createDefaultRegistry();
  const mockLlmRouter = async () => ({ task_type: "chat", entities: [], confidence: 0.1 });

  const router = new ConversationTaskRouterV2({ registry, llmRouter: mockLlmRouter });

  const sessionState = {
    getCurrentTask: () => ({
      taskId: "task_001",
      taskType: "operating_driver_valuation",
      entities: [{ ticker: "688041.SH", role: "target" }],
      topic: "海光信息估值",
      derivedTheme: "超节点",
    }),
  };

  const envelope = await router.route("你刚才说海光已经很贵，那超节点还有谁", { sessionState, chatHistory: [] });

  assert.equal(envelope.relation_to_previous, "derive");
  assert.equal(envelope.task_type, "theme_expectation_gap");
  assert.ok(envelope.topic.includes("超节点"));
});

test("ConversationTaskRouterV2 produces auditable routing result", async () => {
  const { ConversationTaskRouterV2 } = await import("../../api/services/conversation-task-router-v2.js");
  const { createDefaultRegistry } = await import("../../api/services/task-graph-registry.js");

  const registry = createDefaultRegistry();
  const mockLlmRouter = async () => ({
    task_type: "stock_deep_dive",
    entities: [{ ticker: "688041.SH", role: "target" }],
    confidence: 0.9,
    reasoning: "用户指定股票",
  });

  const router = new ConversationTaskRouterV2({ registry, llmRouter: mockLlmRouter });

  const envelope = await router.route("分析海光信息", { sessionState: null, chatHistory: [] });

  // 审计字段
  assert.ok(envelope.routingTrace, "应包含路由追踪");
  assert.ok(envelope.routingTrace.llmResult, "追踪应包含 LLM 原始结果");
  assert.ok(envelope.routingTrace.finalTaskType, "追踪应包含最终任务类型");
  assert.ok(envelope.routingTrace.relation, "追踪应包含任务关系");
  assert.equal(typeof envelope.routingTrace.timestamp, "string", "追踪应包含时间戳");
});

test("WorkflowEngine production entry uses Router V2 for the six golden natural-language tasks", async () => {
  const { WorkflowEngine } = await import("../../api/services/workflow-engine.js");
  const { ConversationTaskRouterV2 } = await import("../../api/services/conversation-task-router-v2.js");
  const { createDefaultRegistry } = await import("../../api/services/task-graph-registry.js");

  const registry = createDefaultRegistry();
  const unavailableModel = async () => { throw new Error("model unavailable in deterministic route test"); };
  const taskRouterV2 = new ConversationTaskRouterV2({ registry, llmRouter: unavailableModel });
  const engine = new WorkflowEngine({ taskRouterV2 });
  engine.sessionState = null;
  engine.context.chatHistory = [];

  const cases = [
    ["把阳光电源换成海光信息，做调仓比较（300274.SZ、688041.SH）", "pair_switch_decision"],
    ["给海光信息 688041.SH 做经营驱动估值模型", "operating_driver_valuation"],
    ["筛选超节点主题里的预期差候选", "theme_expectation_gap"],
    ["星网锐捷的市值不是 199 亿，请纠正这个错误", "claim_correction"],
    ["为什么 DCI 需求明确但 A 股一直没有催化和行情？", "industry_causal_explainer"],
    ["给德科立 688205.SH 做 90 天信号跟踪计划：认证、工厂和出货节奏", "company_signal_plan"],
  ];

  for (const [query, expectedTaskType] of cases) {
    const result = await engine.analyzeAndPlan(query);
    assert.equal(result.taskType, expectedTaskType, query);
    assert.ok(result.flow.length > 0, `${expectedTaskType} 应有可执行流程`);
    assert.ok(result.flow.every((toolId) => engine.taskGraphRegistry.isToolAllowed(expectedTaskType, toolId)));
  }
});
