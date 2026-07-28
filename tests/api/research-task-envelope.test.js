/**
 * ResearchTaskEnvelope 和 ResearchSessionState 测试
 *
 * 功能说明：
 *   这个文件测试研究任务信封(Envelope)和会话状态管理。
 *   核心目标是确保多轮对话中，系统能记住上一轮的标的、假设、数据和制品，
 *   而不是把追问误判为"新问题"然后丢弃所有上下文。
 *
 * 参数说明：
 *   无直接参数，通过 mock 数据和测试用例验证行为
 *
 * 返回值说明：
 *   所有测试应通过，如果失败说明实现有问题
 *
 * 异常处理：
 *   测试失败会抛出 assert.AssertionError
 */

import assert from "node:assert/strict";
import test from "node:test";

// === Part 1: ResearchTaskEnvelope 契约测试 ===

test("ResearchTaskEnvelope rejects unknown task types", async () => {
  const { validateTaskEnvelope } = await import("../../api/services/research-task-contracts.js");

  // 未知任务类型应该被拒绝
  const invalidEnvelope = {
    task_type: "unknown_task",
    entities: [{ ticker: "300308.SZ", role: "target" }],
    relation_to_previous: "new_task",
  };

  assert.throws(
    () => validateTaskEnvelope(invalidEnvelope),
    /unknown task type/i,
    "未知任务类型应被拒绝"
  );
});

test("ResearchTaskEnvelope rejects empty entities for research tasks", async () => {
  const { validateTaskEnvelope } = await import("../../api/services/research-task-contracts.js");

  // 研究类任务必须有实体
  const emptyEnvelope = {
    task_type: "stock_deep_dive",
    entities: [],
    relation_to_previous: "new_task",
  };

  assert.throws(
    () => validateTaskEnvelope(emptyEnvelope),
    /empty entities/i,
    "研究任务必须有实体"
  );
});

test("ResearchTaskEnvelope rejects invalid relation types", async () => {
  const { validateTaskEnvelope } = await import("../../api/services/research-task-contracts.js");

  // 非法关系类型
  const invalidRelation = {
    task_type: "stock_deep_dive",
    entities: [{ ticker: "300308.SZ", role: "target" }],
    relation_to_previous: "invalid_relation",
    parent_task_id: "task_123",
  };

  assert.throws(
    () => validateTaskEnvelope(invalidRelation),
    /invalid relation/i,
    "非法关系类型应被拒绝"
  );
});

test("ResearchTaskEnvelope accepts valid envelopes with all required fields", async () => {
  const { validateTaskEnvelope } = await import("../../api/services/research-task-contracts.js");

  const validEnvelope = {
    task_type: "stock_deep_dive",
    entities: [{ ticker: "300308.SZ", role: "target" }],
    topic: "光模块行业分析",
    time_horizon: { from: 2024, to: 2026 },
    decision_goal: "估值分析",
    requested_artifact: "research_report",
    relation_to_previous: "new_task",
    constraints: {},
    confidence: 0.95,
    needs_clarification: false,
  };

  // 应该不抛出异常
  const result = validateTaskEnvelope(validEnvelope);
  assert.equal(result.valid, true);
  assert.equal(result.taskType, "stock_deep_dive");
});

// === Part 2: ResearchSessionState 测试 ===

test("ResearchSessionState persists and restores task state across conversation turns", async () => {
  const { ResearchSessionState } = await import("../../api/services/research-session-state.js");

  // 创建会话状态
  const state = new ResearchSessionState("session_001");

  // 设置第一轮任务状态
  state.setCurrentTask({
    taskId: "task_001",
    taskType: "stock_deep_dive",
    entities: [{ ticker: "688041.SH", role: "target" }],
    topic: "海光信息经营估值",
    confirmedFacts: [
      { field: "market_cap", value: 2600, unit: "亿元", asOf: "2026-07-21" }
    ],
    modelAssumptions: [
      { variable: "dcu_shipment_2026", value: 50, unit: "万颗" }
    ],
    artifactRefs: ["artifact_report_001"],
    pendingQuestions: ["验证DCU出货量假设"],
  });

  // 序列化
  const serialized = state.serialize();

  // 新建状态并恢复
  const restored = new ResearchSessionState("session_001");
  restored.deserialize(serialized);

  // 验证恢复后的状态
  const task = restored.getCurrentTask();
  assert.equal(task.taskId, "task_001");
  assert.equal(task.taskType, "stock_deep_dive");
  assert.equal(task.entities[0].ticker, "688041.SH");
  assert.equal(task.confirmedFacts[0].value, 2600);
  assert.equal(task.pendingQuestions.length, 1);
});

test("ResearchSessionState isolates temporary assumptions from formal memory", async () => {
  const { ResearchSessionState } = await import("../../api/services/research-session-state.js");

  const state = new ResearchSessionState("session_002");

  // 添加临时假设
  state.addModelAssumption({
    variable: "temp_growth_rate",
    value: 0.25,
    unit: "percentage",
    isTemporary: true, // 标记为临时假设
  });

  // 添加正式事实
  state.addConfirmedFact({
    field: "revenue_2025",
    value: 382.4,
    unit: "亿元",
    source: "年报",
    evidenceId: "ev_001",
  });

  // 获取应写入正式记忆的内容（不应包含临时假设）
  const memoryCandidates = state.getMemoryCandidates();

  // 临时假设不应进入记忆候选
  assert.equal(memoryCandidates.some(c => c.variable === "temp_growth_rate"), false,
    "临时假设不应进入正式记忆候选");
});

// === Part 3: 追问识别与任务关系测试 ===

test("continue relation preserves previous task entities and topic", async () => {
  const { resolveTaskRelation } = await import("../../api/services/research-task-contracts.js");

  const previousTask = {
    taskId: "task_001",
    taskType: "stock_deep_dive",
    entities: [{ ticker: "688041.SH", role: "target" }],
    topic: "海光信息经营估值",
  };

  const userInput = "继续";

  const envelope = resolveTaskRelation(userInput, previousTask);

  // "继续"应该是 continue 关系，继承上一轮的实体和主题
  assert.equal(envelope.relation_to_previous, "continue");
  assert.equal(envelope.task_type, "stock_deep_dive");
  assert.equal(envelope.entities[0].ticker, "688041.SH");
  assert.equal(envelope.topic, "海光信息经营估值");
});

test("那第二个呢 derives second entity from previous multi-entity task", async () => {
  const { resolveTaskRelation } = await import("../../api/services/research-task-contracts.js");

  const previousTask = {
    taskId: "task_001",
    taskType: "pair_switch_decision",
    entities: [
      { ticker: "300274.SZ", role: "sell" },
      { ticker: "688041.SH", role: "buy" },
    ],
    topic: "阳光电源换海光信息",
  };

  const userInput = "那第二个呢";

  const envelope = resolveTaskRelation(userInput, previousTask);

  // "那第二个呢"应该是 derive 关系，关注第二个实体
  assert.equal(envelope.relation_to_previous, "derive");
  assert.equal(envelope.entities[0].ticker, "688041.SH");
  assert.equal(envelope.entities[0].role, "target");
});

test("你刚才说海光已经很贵，那超节点还有谁 triggers theme search with derive relation", async () => {
  const { resolveTaskRelation } = await import("../../api/services/research-task-contracts.js");

  const previousTask = {
    taskId: "task_001",
    taskType: "operating_driver_valuation",
    entities: [{ ticker: "688041.SH", role: "target" }],
    topic: "海光信息估值",
    derivedTheme: "超节点",
  };

  const userInput = "你刚才说海光已经很贵，那超节点还有谁";

  const envelope = resolveTaskRelation(userInput, previousTask);

  // 这是主题筛选任务，应该是 derive 关系
  assert.equal(envelope.relation_to_previous, "derive");
  assert.equal(envelope.task_type, "theme_expectation_gap");
  assert.ok(envelope.topic.includes("超节点"), "主题应包含超节点");
});

test("星网锐捷市值是260亿，不是199亿 triggers correction workflow", async () => {
  const { resolveTaskRelation } = await import("../../api/services/research-task-contracts.js");

  const previousTask = {
    taskId: "task_001",
    taskType: "theme_expectation_gap",
    entities: [{ ticker: "002396.SZ", role: "candidate" }],
    topic: "超节点预期差筛选",
    confirmedFacts: [
      { field: "market_cap", value: 199, unit: "亿元", ticker: "002396.SZ" }
    ],
  };

  const userInput = "星网锐捷市值是260亿，不是199亿";

  const envelope = resolveTaskRelation(userInput, previousTask);

  // 用户纠错应该触发 correct 关系
  assert.equal(envelope.relation_to_previous, "correct");
  assert.equal(envelope.task_type, "claim_correction");
  assert.equal(envelope.entities[0].ticker, "002396.SZ");
  assert.ok(envelope.correctionTarget, "应指明纠错目标");
});

// === Part 4: 确保追问不会被降级为通用聊天 ===

test("isFollowUpQuestion detects continue keywords", async () => {
  const { isFollowUpQuestion } = await import("../../api/services/research-task-contracts.js");

  assert.equal(isFollowUpQuestion("继续"), true, "继续是追问");
  assert.equal(isFollowUpQuestion("接着往下讲"), true, "接着往下讲是追问");
  assert.equal(isFollowUpQuestion("没说完"), true, "没说完是追问");
  assert.equal(isFollowUpQuestion("你刚才说海光很贵"), true, "你刚才说是追问");
  assert.equal(isFollowUpQuestion("分析一下海光信息"), false, "新问题不是追问");
});

test("follow-up question returns continue relation with previous task type", async () => {
  const { resolveTaskRelation } = await import("../../api/services/research-task-contracts.js");

  const previousTask = {
    taskId: "task_001",
    taskType: "stock_deep_dive",
    entities: [{ ticker: "688041.SH", role: "target" }],
    topic: "海光信息深度研究",
  };

  // "继续"应该返回 continue 关系，保持 stock_deep_dive 任务类型
  const envelope = resolveTaskRelation("继续", previousTask);
  assert.equal(envelope.relation_to_previous, "continue");
  assert.equal(envelope.task_type, "stock_deep_dive");
  assert.equal(envelope.entities[0].ticker, "688041.SH");
  assert.ok(envelope.confirmedFacts !== undefined, "continue 应继承 confirmedFacts");
});

test("resolveTaskRelation without previous task returns new_task", async () => {
  const { resolveTaskRelation } = await import("../../api/services/research-task-contracts.js");

  const envelope = resolveTaskRelation("继续", null);
  assert.equal(envelope.relation_to_previous, "new_task");
  assert.equal(envelope.task_type, "chat");
});

test("correction relation extracts numeric target from input", async () => {
  const { resolveTaskRelation } = await import("../../api/services/research-task-contracts.js");

  const previousTask = {
    taskId: "task_001",
    taskType: "stock_deep_dive",
    entities: [{ ticker: "002396.SZ", name: "星网锐捷", role: "target" }],
    topic: "星网锐捷分析",
  };

  const envelope = resolveTaskRelation("星网锐捷市值是260亿，不是199亿", previousTask);
  assert.equal(envelope.relation_to_previous, "correct");
  assert.equal(envelope.task_type, "claim_correction");
  assert.ok(envelope.correctionTarget, "应提取纠错目标");
  assert.equal(envelope.correctionTarget.entity, "002396.SZ");
});