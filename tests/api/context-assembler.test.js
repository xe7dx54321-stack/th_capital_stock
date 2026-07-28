import assert from "node:assert/strict";
import test from "node:test";

import { ContextAssembler } from "../../api/services/context-assembler.js";

function buildServerMessages(turnCount = 12) {
  const messages = [];
  for (let turn = 1; turn <= turnCount; turn += 1) {
    messages.push({
      id: `u${turn}`,
      session_id: "session-authoritative",
      role: "user",
      content: `服务端第${turn}轮用户消息`,
      created_at: `2026-07-28T00:${String(turn).padStart(2, "0")}:00.000Z`,
    });
    messages.push({
      id: `a${turn}`,
      session_id: "session-authoritative",
      role: "assistant",
      content: `服务端第${turn}轮助手消息`,
      created_at: `2026-07-28T00:${String(turn).padStart(2, "0")}:30.000Z`,
    });
  }
  return messages;
}

function buildAssembler() {
  const calls = { sessionIds: [], snapshots: [] };
  const sessionService = {
    getSessionMessages(sessionId) {
      calls.sessionIds.push(sessionId);
      return buildServerMessages(12);
    },
  };
  const compactor = {
    async compact({ messages }) {
      return {
        summary: {
          entities: [{ ticker: "002396.SZ", name: "星网锐捷" }],
          userGoals: ["研究超节点预期差"],
          confirmedFacts: [],
          temporaryAssumptions: [],
          userCorrections: [],
          decisions: [{ text: "旧摘要仍写着市值 199 亿元" }],
          unresolvedQuestions: [],
          artifactRefs: ["artifact-old"],
          coveredMessageIds: messages.slice(0, -8).map((item) => item.id),
        },
        recentMessages: messages.slice(-8),
      };
    },
  };
  const contextBudget = {
    fit(sections) {
      return {
        sections,
        tokenUsage: {
          totalInputTokens: 88,
          budgetTokens: 100,
          bySection: {},
        },
        omitted: [],
      };
    },
  };
  const snapshotRepository = {
    save(snapshot) {
      calls.snapshots.push(snapshot);
      return "snapshot-001";
    },
  };

  return {
    calls,
    assembler: new ContextAssembler({
      sessionService,
      compactor,
      contextBudget,
      snapshotRepository,
    }),
  };
}

function baseInput() {
  return {
    sessionId: "session-authoritative",
    currentMessage: "继续分析，并记住市值应为 260 亿元",
    clientChatHistory: [{
      role: "assistant",
      content: "客户端截断且不可信的历史",
    }],
    taskEnvelope: {
      task_type: "claim_correction",
      topic: "星网锐捷市值纠错",
      entities: [{ ticker: "002396.SZ", name: "星网锐捷" }],
    },
    sessionState: {
      userCorrections: [{
        entity: "002396.SZ",
        field: "market_cap",
        oldValue: 199,
        newValue: 260,
        unit: "亿元",
        status: "revalidated",
      }],
      confirmedFacts: [{
        ticker: "002396.SZ",
        field: "market_cap",
        value: 260,
        unit: "亿元",
        evidenceId: "ev-current-quote",
        asOf: "2026-07-28",
      }],
      pendingQuestions: ["新市值对 PE 的影响"],
      artifactRefs: ["artifact-deep-dive"],
    },
    approvedMemories: [{
      memoryId: "approved-memory",
      allowedUsage: "factual_context",
      content: "已批准的历史论点",
      evidenceIds: ["ev-old-report"],
    }],
    artifactDigests: [{
      artifactId: "artifact-deep-dive",
      title: "星网锐捷个股深度研究",
      digest: "核心判断摘要",
      body: "不应被送入上下文的完整长报告正文".repeat(200),
    }],
    modelProfile: { contextWindowTokens: 120 },
  };
}

test("server reloads full history by sessionId instead of trusting client truncation", async () => {
  const { assembler, calls } = buildAssembler();
  const result = await assembler.assemble(baseInput());
  const serialized = JSON.stringify(result.messages);

  assert.deepEqual(calls.sessionIds, ["session-authoritative"]);
  assert.equal(result.metadata.historySource, "server_session");
  assert.equal(serialized.includes("服务端第12轮助手消息"), true);
  assert.equal(serialized.includes("客户端截断且不可信的历史"), false);
});

test("user correction is pinned ahead of stale summaries", async () => {
  const { assembler } = buildAssembler();
  const result = await assembler.assemble(baseInput());
  const pinned = JSON.stringify(result.sections.pinned);
  const compacted = JSON.stringify(result.sections.compactedHistory);
  const allMessages = JSON.stringify(result.messages);

  assert.match(pinned, /260/);
  assert.match(pinned, /ev-current-quote/);
  assert.match(compacted, /199/);
  assert.ok(allMessages.indexOf("260") < allMessages.indexOf("199"));
});

test("artifact body is replaced by digest and reference", async () => {
  const { assembler } = buildAssembler();
  const input = baseInput();
  const result = await assembler.assemble(input);
  const serialized = JSON.stringify(result.messages);

  assert.match(serialized, /artifact-deep-dive/);
  assert.match(serialized, /核心判断摘要/);
  assert.equal(serialized.includes(input.artifactDigests[0].body), false);
});

test("assembler persists an auditable context snapshot", async () => {
  const { assembler, calls } = buildAssembler();
  const result = await assembler.assemble(baseInput());

  assert.equal(result.snapshotId, "snapshot-001");
  assert.equal(calls.snapshots.length, 1);
  assert.equal(calls.snapshots[0].sessionId, "session-authoritative");
  assert.equal(calls.snapshots[0].tokenUsage.totalInputTokens, 88);
  assert.deepEqual(calls.snapshots[0].omitted, []);
});
