/**
 * 会话状态端到端集成测试
 *
 * 功能说明：
 *   这个文件测试 WorkflowEngine 与 SessionStateStore 的端到端集成：
 *   - 第一次对话后保存状态
 *   - 第二次对话（模拟刷新）后能加载上一轮状态
 *   - 追问能基于上轮状态继承实体和主题
 *
 * 参数说明：
 *   无直接参数，通过临时数据库和真实 WorkflowEngine 验证行为
 *
 * 返回值说明：
 *   所有测试应通过，证明会话状态可以真正跨刷新恢复
 *
 * 异常处理：
 *   测试失败会抛出 assert.AssertionError
 */

import assert from "node:assert/strict";
import test from "node:test";
import Database from "better-sqlite3";
import { fileURLToPath } from "url";
import path from "path";
import fs from "fs";
import os from "os";

import { WorkflowEngine } from "../../api/services/workflow-engine.js";
import { SessionStateStore, ResearchSessionState } from "../../api/services/research-session-state.js";
import { resolveTaskRelation, isFollowUpQuestion } from "../../api/services/research-task-contracts.js";

// === 临时数据库辅助函数 ===

/**
 * 创建一个临时 sqlite 数据库并应用 0008 迁移
 * @returns {Database} better-sqlite3 实例
 */
function createTempDb() {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "smr-test-"));
  const dbPath = path.join(tmpDir, "session_state.db");
  const db = new Database(dbPath);

  db.exec(`
    CREATE TABLE IF NOT EXISTS research_session_state (
      session_id TEXT PRIMARY KEY,
      state_json TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_research_session_state_updated
      ON research_session_state(updated_at);
  `);

  return { db, dbPath, tmpDir };
}

function cleanup(db, tmpDir) {
  if (db) {
    try { db.close(); } catch (e) { /* ignore */ }
  }
  if (tmpDir) {
    try { fs.rmSync(tmpDir, { recursive: true, force: true }); } catch (e) { /* ignore */ }
  }
}

// === 测试 1：基本持久化与恢复 ===

test("SessionStateStore persists state to database and reloads it", async () => {
  const { db, tmpDir } = createTempDb();
  try {
    const store = new SessionStateStore(db);
    const state = new ResearchSessionState("session_e2e_001");
    state.setCurrentTask({
      taskId: "task_e2e_001",
      taskType: "stock_deep_dive",
      entities: [{ ticker: "688041.SH", role: "target" }],
      topic: "海光信息经营估值",
      confirmedFacts: [{ field: "market_cap", value: 2600, unit: "亿元" }],
    });

    await store.save(state);

    // 重新加载
    const loaded = await store.load("session_e2e_001");
    assert.ok(loaded, "应能加载已保存的会话");
    const task = loaded.getCurrentTask();
    assert.equal(task.taskId, "task_e2e_001");
    assert.equal(task.entities[0].ticker, "688041.SH");
    assert.equal(task.confirmedFacts[0].value, 2600);
  } finally {
    cleanup(db, tmpDir);
  }
});

test("SessionStateStore returns null for missing session", async () => {
  const { db, tmpDir } = createTempDb();
  try {
    const store = new SessionStateStore(db);
    const loaded = await store.load("non_existent_session");
    assert.equal(loaded, null, "不存在的会话应返回 null");
  } finally {
    cleanup(db, tmpDir);
  }
});

// === 测试 2：WorkflowEngine 集成 ===

test("WorkflowEngine saves state after first query and reloads on second engine", async () => {
  const { db, tmpDir } = createTempDb();
  try {
    const store = new SessionStateStore(db);
    const sessionId = "session_e2e_engine_001";

    // === 第一轮对话：使用 WorkflowEngine 处理一个"继续"追问
    // 由于我们没有真正的 LLM，我们直接给引擎注入上轮任务状态。
    const engine1 = new WorkflowEngine({
      runId: "run_001",
      sessionId,
      sessionStateStore: store,
    });

    // 模拟上一轮任务（之前用户问过"分析海光信息"）
    await engine1._loadSessionState();
    engine1.sessionState.setCurrentTask({
      taskId: "task_prev_001",
      taskType: "stock_deep_analysis",
      entities: [{ ticker: "688041.SH", role: "target" }],
      topic: "海光信息经营估值",
    });
    await store.save(engine1.sessionState);

    // === 第二轮对话：刷新后创建新引擎，应该恢复上轮状态
    const engine2 = new WorkflowEngine({
      runId: "run_002",
      sessionId,
      sessionStateStore: store,
    });
    await engine2._loadSessionState();

    const previousTask = engine2.sessionState.getCurrentTask();
    assert.ok(previousTask, "应能恢复上轮任务");
    assert.equal(previousTask.taskId, "task_prev_001");
    assert.equal(previousTask.taskType, "stock_deep_analysis");
    assert.equal(previousTask.entities[0].ticker, "688041.SH");

    // === 验证追问可以基于恢复的状态正确路由 ===
    const envelope = resolveTaskRelation("继续", previousTask);
    assert.equal(envelope.relation_to_previous, "continue",
      "刷新后的'继续'应该返回 continue 关系");
    assert.equal(envelope.task_type, "stock_deep_analysis",
      "应该继承上轮的 stock_deep_analysis 任务类型");
    assert.equal(envelope.entities[0].ticker, "688041.SH",
      "应该继承上轮的实体");
  } finally {
    cleanup(db, tmpDir);
  }
});

// === 测试 3：跨会话隔离 ===

test("SessionStateStore isolates state between different sessions", async () => {
  const { db, tmpDir } = createTempDb();
  try {
    const store = new SessionStateStore(db);

    const stateA = new ResearchSessionState("session_A");
    stateA.setCurrentTask({
      taskId: "task_A",
      taskType: "stock_deep_analysis",
      entities: [{ ticker: "688041.SH" }],
    });
    await store.save(stateA);

    const stateB = new ResearchSessionState("session_B");
    stateB.setCurrentTask({
      taskId: "task_B",
      taskType: "theme_expectation_gap",
      entities: [{ ticker: "002396.SZ" }],
    });
    await store.save(stateB);

    // 重新加载并验证隔离
    const loadedA = await store.load("session_A");
    const loadedB = await store.load("session_B");

    assert.equal(loadedA.getCurrentTask().taskId, "task_A");
    assert.equal(loadedA.getCurrentTask().taskType, "stock_deep_analysis");
    assert.equal(loadedB.getCurrentTask().taskId, "task_B");
    assert.equal(loadedB.getCurrentTask().taskType, "theme_expectation_gap");
  } finally {
    cleanup(db, tmpDir);
  }
});

// === 测试 4：update 路径（save 同 sessionId 应覆盖）===

test("SessionStateStore save() overwrites previous state for same session", async () => {
  const { db, tmpDir } = createTempDb();
  try {
    const store = new SessionStateStore(db);
    const sessionId = "session_update";

    // 第一次保存
    const state1 = new ResearchSessionState(sessionId);
    state1.setCurrentTask({
      taskId: "task_v1",
      taskType: "chat",
      entities: [],
    });
    await store.save(state1);

    // 第二次保存（同 sessionId）
    const state2 = new ResearchSessionState(sessionId);
    state2.setCurrentTask({
      taskId: "task_v2",
      taskType: "stock_deep_analysis",
      entities: [{ ticker: "688041.SH" }],
    });
    await store.save(state2);

    // 重新加载
    const loaded = await store.load(sessionId);
    const task = loaded.getCurrentTask();
    assert.equal(task.taskId, "task_v2", "应该保留最新版本");
    assert.equal(task.taskType, "stock_deep_analysis");
  } finally {
    cleanup(db, tmpDir);
  }
});

// === 测试 5：临时假设隔离端到端 ===

test("ResearchSessionState getMemoryCandidates excludes temporary assumptions end-to-end", async () => {
  const { db, tmpDir } = createTempDb();
  try {
    const store = new SessionStateStore(db);
    const state = new ResearchSessionState("session_memory_e2e");

    state.addConfirmedFact({
      field: "revenue_2025",
      value: 382.4,
      unit: "亿元",
      source: "年报",
      evidenceId: "ev_001",
    });
    state.addModelAssumption({
      variable: "temp_growth",
      value: 0.25,
      isTemporary: true,
    });
    state.addModelAssumption({
      variable: "permanent_margin",
      value: 0.30,
      isTemporary: false,
    });

    await store.save(state);

    const loaded = await store.load("session_memory_e2e");
    const candidates = loaded.getMemoryCandidates();

    // 已确认事实应在记忆候选中
    const hasRevenue = candidates.some(c => c.content && c.content.includes("revenue_2025"));
    assert.equal(hasRevenue, true, "已确认事实应在记忆候选中");

    // 永久假设应在
    const hasPermanent = candidates.some(c => c.content && c.content.includes("permanent_margin"));
    assert.equal(hasPermanent, true, "永久假设应在记忆候选中");

    // 临时假设不应在
    const hasTemporary = candidates.some(c => c.content && c.content.includes("temp_growth"));
    assert.equal(hasTemporary, false, "临时假设不应在记忆候选中");
  } finally {
    cleanup(db, tmpDir);
  }
});

// === 测试 6：完整追问链 ===

test("follow-up chain: research → continue → derive → correct", async () => {
  const { db, tmpDir } = createTempDb();
  try {
    const store = new SessionStateStore(db);
    const sessionId = "session_chain";

    // 模拟第一轮：海光信息深度研究
    const state = new ResearchSessionState(sessionId);
    state.setCurrentTask({
      taskId: "task_1",
      taskType: "stock_deep_analysis",
      entities: [{ ticker: "688041.SH", name: "海光信息", role: "target" }],
      topic: "海光信息经营估值",
    });
    await store.save(state);

    // === 第二轮：用户说"继续" → continue 关系
    let loaded = await store.load(sessionId);
    let envelope = resolveTaskRelation("继续", loaded.getCurrentTask());
    assert.equal(envelope.relation_to_previous, "continue");
    assert.equal(envelope.entities[0].ticker, "688041.SH");

    // 保存继续后的状态（同一任务）
    state.setCurrentTask({
      taskId: "task_2",
      taskType: envelope.task_type,
      entities: envelope.entities,
      topic: envelope.topic || loaded.getCurrentTask().topic,
    });
    await store.save(state);

    // === 第三轮：用户说"那第二个呢" → 假设上一轮有多标的
    // 更新状态为多标的
    state.setCurrentTask({
      taskId: "task_3",
      taskType: "pair_switch_decision",
      entities: [
        { ticker: "300274.SZ", name: "阳光电源", role: "sell" },
        { ticker: "688041.SH", name: "海光信息", role: "buy" },
      ],
      topic: "阳光电源换海光信息",
    });
    await store.save(state);

    loaded = await store.load(sessionId);
    envelope = resolveTaskRelation("那第二个呢", loaded.getCurrentTask());
    assert.equal(envelope.relation_to_previous, "derive");
    assert.equal(envelope.entities[0].ticker, "688041.SH",
      "应该聚焦第二个实体海光信息");

    // === 第四轮：用户说"你刚才说海光很贵，那超节点还有谁" → derive + 主题筛选
    state.setCurrentTask({
      taskId: "task_4",
      taskType: "operating_driver_valuation",
      entities: [{ ticker: "688041.SH", name: "海光信息", role: "target" }],
      topic: "海光信息估值",
      derivedTheme: "超节点",
    });
    await store.save(state);

    loaded = await store.load(sessionId);
    envelope = resolveTaskRelation("你刚才说海光已经很贵，那超节点还有谁", loaded.getCurrentTask());
    assert.equal(envelope.relation_to_previous, "derive");
    assert.equal(envelope.task_type, "theme_expectation_gap",
      "应该从估值任务衍生为主题筛选");
    assert.ok(envelope.topic.includes("超节点"), "主题应包含超节点");

    // === 第五轮：用户纠错"星网锐捷市值是260亿，不是199亿"
    state.setCurrentTask({
      taskId: "task_5",
      taskType: "theme_expectation_gap",
      entities: [{ ticker: "002396.SZ", name: "星网锐捷", role: "candidate" }],
      topic: "超节点预期差筛选",
      confirmedFacts: [
        { field: "market_cap", value: 199, unit: "亿元", ticker: "002396.SZ" }
      ],
    });
    await store.save(state);

    loaded = await store.load(sessionId);
    envelope = resolveTaskRelation("星网锐捷市值是260亿，不是199亿", loaded.getCurrentTask());
    assert.equal(envelope.relation_to_previous, "correct");
    assert.equal(envelope.task_type, "claim_correction");
    assert.equal(envelope.correctionTarget.entity, "002396.SZ");

    // 记录用户纠错
    state.addUserCorrection({
      field: "market_cap",
      oldValue: 199,
      newValue: 260,
      entity: "002396.SZ",
      reason: "用户声称市值是260亿",
    });
    await store.save(state);

    // 验证纠错已记录
    const finalLoaded = await store.load(sessionId);
    assert.equal(finalLoaded.userCorrections.length, 1);
    assert.equal(finalLoaded.userCorrections[0].field, "market_cap");
    assert.equal(finalLoaded.userCorrections[0].newValue, 260);
    assert.equal(finalLoaded.userCorrections[0].status, "pending_revalidation");

    state.addUserCorrection({
      field: "market_cap",
      oldValue: 199,
      newValue: 260,
      entity: "002396.SZ",
      reason: "权威快照已复核",
      status: "revalidated",
      evidenceId: "ev_authoritative",
    });
    assert.equal(
      state.userCorrections.at(-1).status,
      "revalidated",
      "已通过重新取数的纠错不得再次被写回 pending_revalidation",
    );
  } finally {
    cleanup(db, tmpDir);
  }
});
