import assert from "node:assert/strict";
import test from "node:test";

import { ConversationCompactor } from "../../api/services/conversation-compactor.js";

function buildMessages(turnCount = 12) {
  const messages = [];
  for (let turn = 1; turn <= turnCount; turn += 1) {
    messages.push({
      id: `u${turn}`,
      role: "user",
      content: turn === 8
        ? "星网锐捷市值是260亿元，不是199亿元"
        : `第${turn}轮用户问题`,
    });
    messages.push({
      id: `a${turn}`,
      role: "assistant",
      content: `第${turn}轮研究回答`,
    });
  }
  return messages;
}

test("compactor keeps the latest four complete turns and summarizes earlier messages", async () => {
  const compactor = new ConversationCompactor({
    keepRecentTurns: 4,
    summarize: async ({ messages }) => ({
      entities: [{ ticker: "002396.SZ", name: "星网锐捷" }],
      userGoals: ["研究超节点预期差"],
      confirmedFacts: [],
      temporaryAssumptions: [],
      userCorrections: [{
        entity: "002396.SZ",
        field: "market_cap",
        oldValue: 199,
        newValue: 260,
        unit: "亿元",
      }],
      decisions: [],
      unresolvedQuestions: ["重新核验当前市值"],
      artifactRefs: ["artifact_deep_dive"],
      coveredMessageIds: messages.map((item) => item.id),
    }),
  });

  const result = await compactor.compact({ messages: buildMessages(12) });

  assert.equal(result.recentMessages.length, 8);
  assert.deepEqual(
    result.recentMessages.map((item) => item.id),
    ["u9", "a9", "u10", "a10", "u11", "a11", "u12", "a12"],
  );
  assert.equal(result.summary.userCorrections[0].newValue, 260);
  assert.deepEqual(result.summary.coveredMessageIds, [
    "u1", "a1", "u2", "a2", "u3", "a3", "u4", "a4",
    "u5", "a5", "u6", "a6", "u7", "a7", "u8", "a8",
  ]);
});

test("invalid model summary falls back to a complete deterministic working-memory shape", async () => {
  const compactor = new ConversationCompactor({
    keepRecentTurns: 2,
    summarize: async () => ({ prose: "not a valid structured summary" }),
  });

  const result = await compactor.compact({ messages: buildMessages(6) });

  for (const field of [
    "entities",
    "userGoals",
    "confirmedFacts",
    "temporaryAssumptions",
    "userCorrections",
    "decisions",
    "unresolvedQuestions",
    "artifactRefs",
    "coveredMessageIds",
  ]) {
    assert.ok(Array.isArray(result.summary[field]), `${field} must be an array`);
  }
  assert.equal(result.degraded, true);
  assert.equal(result.degradationReason, "invalid_model_summary");
});

test("previously covered messages are not summarized a second time", async () => {
  let summarizedIds = [];
  const compactor = new ConversationCompactor({
    keepRecentTurns: 2,
    summarize: async ({ messages }) => {
      summarizedIds = messages.map((item) => item.id);
      return {
        entities: [],
        userGoals: [],
        confirmedFacts: [],
        temporaryAssumptions: [],
        userCorrections: [],
        decisions: [],
        unresolvedQuestions: [],
        artifactRefs: [],
        coveredMessageIds: summarizedIds,
      };
    },
  });

  await compactor.compact({
    messages: buildMessages(6),
    previousSummary: {
      entities: [],
      userGoals: [],
      confirmedFacts: [],
      temporaryAssumptions: [],
      userCorrections: [],
      decisions: [],
      unresolvedQuestions: [],
      artifactRefs: [],
      coveredMessageIds: ["u1", "a1", "u2", "a2"],
    },
  });

  assert.equal(summarizedIds.includes("u1"), false);
  assert.equal(summarizedIds.includes("a2"), false);
});
