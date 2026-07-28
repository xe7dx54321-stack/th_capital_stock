import assert from "node:assert/strict";
import test from "node:test";

import { IntentEngine } from "../../api/services/intent-engine.js";
import { WorkflowEngine, resolveMultipleTickers, resolveTicker } from "../../api/services/workflow-engine.js";


test("德科立公司名正确解析为 688205.SH", () => {
  const query = "请对德科立做一个深度分析";
  assert.equal(resolveTicker("德科立"), "688205.SH");
  assert.deepEqual(resolveMultipleTickers(query), ["688205.SH"]);
  assert.equal(resolveTicker("杰普特"), "688025.SH");
});

test("模型不可用时，德科立深度分析仍路由到 V3", () => {
  const query = "请对德科立做一个深度分析";
  const intent = new IntentEngine().createFallbackIntent(query);
  assert.equal(intent.intent, "stock_deep_analysis");
  assert.equal(intent.entities.aShareTicker, "688205.SH");
  assert.deepEqual(intent.requiredTools, ["resolve_entity", "run_governed_stock_deep_dive"]);

  const engine = new WorkflowEngine();
  assert.equal(engine.detectTaskType(query), "STOCK_DEEP_ANALYSIS");
});
