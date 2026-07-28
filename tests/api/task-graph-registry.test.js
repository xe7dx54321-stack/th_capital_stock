/**
 * TaskGraphRegistry 测试
 *
 * 功能说明：
 *   测试任务图注册表——所有研究任务类型必须在此注册，
 *   每个注册的任务包含：ID、名称、描述、默认流程、允许工具集、
 *   是否需要实体、期望制品类型和数据需求模板。
 *   核心目标：LLM 只能选择已注册的任务图，不能任意拼接工具。
 *
 * 参数说明：
 *   无直接参数，通过方法调用验证行为
 *
 * 返回值说明：
 *   所有测试应通过，如果失败说明注册表实现有问题
 *
 * 异常处理：
 *   测试失败会抛出 assert.AssertionError
 */

import assert from "node:assert/strict";
import test from "node:test";

test("TaskGraphRegistry registers and retrieves task graphs by id", async () => {
  const { TaskGraphRegistry } = await import("../../api/services/task-graph-registry.js");

  const registry = new TaskGraphRegistry();

  registry.register({
    id: "stock_deep_dive",
    name: "个股深度研究",
    description: "对指定股票进行全面深度研究分析",
    requiresEntity: true,
    defaultFlow: ["resolve_entity", "run_governed_stock_deep_dive"],
    allowedTools: ["resolve_entity", "run_governed_stock_deep_dive"],
    artifactType: "research_report",
    dataRequirementTemplate: { market: true, financial: true, news: true },
  });

  const graph = registry.get("stock_deep_dive");
  assert.ok(graph, "应能获取已注册的任务图");
  assert.equal(graph.id, "stock_deep_dive");
  assert.equal(graph.name, "个股深度研究");
  assert.equal(graph.requiresEntity, true);
  assert.ok(graph.allowedTools.includes("resolve_entity"));
});

test("TaskGraphRegistry rejects duplicate registration", async () => {
  const { TaskGraphRegistry } = await import("../../api/services/task-graph-registry.js");

  const registry = new TaskGraphRegistry();

  registry.register({
    id: "test_task",
    name: "测试任务",
    defaultFlow: [],
    allowedTools: [],
  });

  // 重复注册应抛出
  assert.throws(
    () => registry.register({ id: "test_task", name: "重复", defaultFlow: [], allowedTools: [] }),
    /already registered/i,
    "重复注册应被拒绝"
  );
});

test("TaskGraphRegistry rejects unregistered task ids", async () => {
  const { TaskGraphRegistry } = await import("../../api/services/task-graph-registry.js");

  const registry = new TaskGraphRegistry();

  // 未注册的 ID 应返回 null
  const graph = registry.get("nonexistent_task");
  assert.equal(graph, null);
});

test("TaskGraphRegistry validates tool membership for a task", async () => {
  const { TaskGraphRegistry } = await import("../../api/services/task-graph-registry.js");

  const registry = new TaskGraphRegistry();

  registry.register({
    id: "stock_deep_dive",
    name: "个股深度研究",
    defaultFlow: ["resolve_entity", "run_governed_stock_deep_dive"],
    allowedTools: ["resolve_entity", "run_governed_stock_deep_dive"],
  });

  // 合法工具
  assert.equal(registry.isToolAllowed("stock_deep_dive", "resolve_entity"), true);
  // 非法工具
  assert.equal(registry.isToolAllowed("stock_deep_dive", "hack_tool"), false);
});

test("TaskGraphRegistry lists all registered task types", async () => {
  const { TaskGraphRegistry, createDefaultRegistry } = await import("../../api/services/task-graph-registry.js");

  // 使用默认注册表（包含所有首批任务类型）
  const registry = createDefaultRegistry();
  const allTypes = registry.list();

  // 首批任务类型必须全部注册
  const expectedIds = [
    "stock_deep_dive",
    "operating_driver_valuation",
    "pair_switch_decision",
    "theme_expectation_gap",
    "industry_causal_explainer",
    "company_signal_plan",
    "claim_correction",
    "daily_brief",
    "portfolio_review",
    "thesis_update",
  ];

  for (const expectedId of expectedIds) {
    assert.ok(allTypes.some(t => t.id === expectedId),
      `任务类型 ${expectedId} 应在默认注册表中`);
  }
});

test("TaskGraphRegistry claim_correction has revalidation flow", async () => {
  const { createDefaultRegistry } = await import("../../api/services/task-graph-registry.js");

  const registry = createDefaultRegistry();
  const correction = registry.get("claim_correction");

  assert.ok(correction, "claim_correction 任务图应存在");
  assert.ok(correction.defaultFlow.includes("run_governed_workflow"),
    "纠错流程应进入受治理工作流，由工作流重新获取权威数据并重算依赖");
  assert.ok(correction.defaultFlow.includes("get_stock_data"),
    "纠错流程必须先重新取数，不能直接信任用户给出的新数值");
  assert.ok(correction.artifactType === "correction_diff",
    "纠错任务的制品类型应为 correction_diff");
});
