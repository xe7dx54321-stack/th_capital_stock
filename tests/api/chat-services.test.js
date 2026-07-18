/**
 * 增强版 ChatBot 服务单元测试
 */

import assert from "node:assert/strict";
import { mkdtempSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import { GrowthTracker } from "../../api/services/growth-service.js";
import { VectorMemory } from "../../api/services/vector-memory.js";


/**
 * 创建临时数据库
 */
function createTempDb() {
  const dir = mkdtempSync(path.join(os.tmpdir(), "smr-growth-test-"));
  return {
    dir,
    vectorPath: path.join(dir, "vector.db"),
    growthPath: path.join(dir, "growth.db"),
  };
}


test("GrowthTracker - 更新标的阶段", () => {
  const { growthPath } = createTempDb();
  const tracker = new GrowthTracker(growthPath);

  const id = tracker.updateStockStage("300308.SZ", "discovered", {
    name: "中际旭创",
    sector: "通信",
  });
  assert.ok(id > 0, "应该返回有效的记录 ID");

  const stocks = tracker.getStockGrowth("300308.SZ");
  assert.equal(stocks.length, 1, "应该有一条记录");
  assert.equal(stocks[0].name, "中际旭创", "名称应该匹配");
  assert.equal(stocks[0].stage, "discovered", "阶段应该匹配");
  tracker.close();
});


test("GrowthTracker - 阶段历史追踪", () => {
  const { growthPath } = createTempDb();
  const tracker = new GrowthTracker(growthPath);

  tracker.updateStockStage("300308.SZ", "discovered", { name: "中际旭创" });
  tracker.updateStockStage("300308.SZ", "candidate", { notes: "基本面不错" });
  tracker.updateStockStage("300308.SZ", "watchlist", { notes: "加入观察池" });

  const history = tracker.getStockStageHistory("300308.SZ");
  assert.equal(history.length, 3, "应该有 3 条阶段历史");

  const stock = tracker.getStockGrowth("300308.SZ");
  assert.equal(stock[0].stage, "watchlist", "当前阶段应该是 watchlist");
  tracker.close();
});


test("GrowthTracker - 记录和查询活动", () => {
  const { growthPath } = createTempDb();
  const tracker = new GrowthTracker(growthPath);

  tracker.recordUserActivity("research_started", { ticker: "300308.SZ" });
  tracker.recordUserActivity("research_started", { ticker: "300394.SZ" });
  tracker.recordUserActivity("decision_made", { ticker: "300308.SZ", action: "buy" });

  const activities = tracker.getUserActivity(null, 10);
  assert.equal(activities.length, 3, "应该有 3 条活动");

  const started = tracker.getUserActivity("research_started", 10);
  assert.equal(started.length, 2, "应该有 2 条 research_started 活动");

  const stats = tracker.getUserActivityStats();
  assert.equal(stats.totalActivities, 3, "总活动数应该是 3");
  assert.equal(stats.recent7DaysActivities, 3, "近 7 天活动应该是 3");
  tracker.close();
});


test("GrowthTracker - 里程碑管理", () => {
  const { growthPath } = createTempDb();
  const tracker = new GrowthTracker(growthPath);

  tracker.addMilestone("完成第一次研究", { ticker: "300308.SZ" });
  tracker.addMilestone("首次决策", { action: "buy" });

  const milestones = tracker.getMilestones(10);
  assert.equal(milestones.length, 2, "应该有 2 个里程碑");
  assert.equal(milestones[0].milestone, "首次决策", "最新的应该在前面");
  assert.equal(milestones[1].milestone, "完成第一次研究", "最老的应该在后面");
  tracker.close();
});


test("GrowthTracker - 决策追踪", () => {
  const { growthPath } = createTempDb();
  const tracker = new GrowthTracker(growthPath);

  tracker.recordDecision("dec-1", "buy", { tsCode: "300308.SZ", notes: "首次买入" });
  tracker.updateDecisionOutcome("dec-1", "win", { performance: 15.5 });

  const decisions = tracker.getDecisionTracking(null, 10);
  assert.equal(decisions.length, 1, "应该有 1 条决策");
  assert.equal(decisions[0].outcome, "win", "结果应该是 win");
  assert.equal(decisions[0].performance, 15.5, "表现应该是 15.5");

  const stats = tracker.getDecisionStats();
  assert.equal(stats.totalDecisions, 1, "总决策数应该是 1");
  assert.equal(stats.decisionsWithOutcome, 1, "有结果的决策数应该是 1");
  tracker.close();
});


test("GrowthTracker - 成长概览", () => {
  const { growthPath } = createTempDb();
  const tracker = new GrowthTracker(growthPath);

  tracker.updateStockStage("300308.SZ", "discovered", { name: "中际旭创" });
  tracker.updateStockStage("300394.SZ", "candidate", { name: "中际旭创" });
  tracker.recordUserActivity("test", { foo: "bar" });

  const overview = tracker.getGrowthOverview();
  assert.ok(overview.stockGrowth, "应该包含 stockGrowth 字段");
  assert.equal(overview.stockGrowth.length, 2, "应该有 2 个不同阶段");
  assert.equal(overview.totalActivities, 1, "应该有 1 条活动");
  tracker.close();
});


test("VectorMemory - 余弦相似度计算", () => {
  const { vectorPath } = createTempDb();
  const memory = new VectorMemory(vectorPath);

  // 完全相同的向量
  const vec1 = [1, 0, 0];
  const vec2 = [1, 0, 0];
  assert.equal(memory.cosineSimilarity(vec1, vec2), 1, "相同向量相似度应该是 1");

  // 正交向量
  const vec3 = [1, 0, 0];
  const vec4 = [0, 1, 0];
  assert.equal(memory.cosineSimilarity(vec3, vec4), 0, "正交向量相似度应该是 0");

  // 完全反向
  const vec5 = [1, 0, 0];
  const vec6 = [-1, 0, 0];
  assert.equal(memory.cosineSimilarity(vec5, vec6), -1, "反向向量相似度应该是 -1");

  // 部分相似
  const vec7 = [1, 1, 0];
  const vec8 = [1, 0, 0];
  const sim = memory.cosineSimilarity(vec7, vec8);
  assert.ok(sim > 0 && sim < 1, "部分相似向量相似度应该在 0 到 1 之间");
  memory.close();
});


test("VectorMemory - 向量与 Buffer 转换", () => {
  const { vectorPath } = createTempDb();
  const memory = new VectorMemory(vectorPath);

  const vec = [0.1, 0.2, 0.3, 0.4, 0.5];
  const buffer = memory.vectorToBuffer(vec);
  const restored = memory.bufferToVector(buffer);

  assert.equal(restored.length, vec.length, "长度应该相同");
  for (let i = 0; i < vec.length; i++) {
    assert.ok(Math.abs(restored[i] - vec[i]) < 1e-6, `索引 ${i} 的值应该接近`);
  }
  memory.close();
});


test("VectorMemory - 对话历史管理", () => {
  const { vectorPath } = createTempDb();
  const memory = new VectorMemory(vectorPath);

  memory.storeChatHistory("今天有哪些机会", "请稍后，我帮您查询", "opportunity_radar");
  memory.storeChatHistory("帮助", "您可以这样使用我", "help");

  const history = memory.getChatHistory(10);
  assert.equal(history.length, 2, "应该有 2 条对话历史");
  assert.equal(history[0].message, "帮助", "最新的应该在前面");

  const context = memory.getRecentContext(5);
  assert.equal(context.length, 2, "应该有 2 条上下文");
  assert.equal(context[0].message, "今天有哪些机会", "最老的应该在前面");

  const deleted = memory.deleteChatHistory(history[0].id);
  assert.equal(deleted, 1, "应该删除 1 条");

  const afterDelete = memory.getChatHistory(10);
  assert.equal(afterDelete.length, 1, "删除后应该剩下 1 条");
  memory.close();
});


test("VectorMemory - 统计信息", () => {
  const { vectorPath } = createTempDb();
  const memory = new VectorMemory(vectorPath);

  memory.storeChatHistory("a", "b", "intent1");
  memory.storeChatHistory("c", "d", "intent2");

  const stats = memory.getStats();
  assert.equal(stats.totalChats, 2, "对话总数应该是 2");
  memory.close();
});
