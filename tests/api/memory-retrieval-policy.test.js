import assert from "node:assert/strict";
import test from "node:test";

import { MemoryRetrievalPolicy } from "../../api/services/memory-retrieval-policy.js";

function memory(overrides = {}) {
  return {
    memory_id: "mem-default",
    memory_type: "research_fact",
    entity_id: "688205.SH",
    content: { text: "2025 年营业收入为 12 亿元" },
    status: "approved",
    as_of: "2025-12-31",
    valid_until: "2027-12-31",
    evidence_ids: ["ev-annual-report"],
    conflict_flag: 0,
    preference_source: null,
    ...overrides,
  };
}

test("candidate memory never enters factual context", () => {
  const policy = new MemoryRetrievalPolicy();
  const result = policy.selectForContext([
    memory({ memory_id: "approved-fact" }),
    memory({ memory_id: "candidate-fact", status: "candidate" }),
    memory({ memory_id: "rejected-fact", status: "rejected" }),
    memory({ memory_id: "conflicted-fact", conflict_flag: 1 }),
  ], {
    entityIds: ["688205.SH"],
    consumer: "stock_deep_dive",
    now: "2026-07-28T00:00:00.000Z",
  });

  assert.deepEqual(result.selected.map((item) => item.memoryId), ["approved-fact"]);
  assert.equal(result.selected[0].allowedUsage, "factual_context");
  assert.ok(result.reviewOnly.some((item) => item.memoryId === "candidate-fact"));
  assert.ok(result.reviewOnly.some((item) => item.memoryId === "conflicted-fact"));
});

test("approved fact without evidence cannot be used as factual context", () => {
  const policy = new MemoryRetrievalPolicy();
  const result = policy.selectForContext([
    memory({ memory_id: "unsupported-fact", evidence_ids: [] }),
  ], {
    entityIds: ["688205.SH"],
    consumer: "thesis_update",
    now: "2026-07-28T00:00:00.000Z",
  });

  assert.equal(result.selected.length, 0);
  assert.equal(result.reviewOnly[0].allowedUsage, "review_only");
  assert.equal(result.reviewOnly[0].exclusionReason, "missing_evidence");
});

test("frameworks and explicit preferences are isolated from factual usage", () => {
  const policy = new MemoryRetrievalPolicy();
  const result = policy.selectForContext([
    memory({
      memory_id: "framework",
      memory_type: "analysis_framework",
      entity_id: null,
      evidence_ids: [],
      content: { text: "从产能、利用率、价格三条线验证收入" },
    }),
    memory({
      memory_id: "explicit-preference",
      memory_type: "user_preference",
      entity_id: null,
      evidence_ids: [],
      preference_source: "user_explicit",
      content: { text: "优先分析现金流" },
    }),
    memory({
      memory_id: "inferred-preference",
      memory_type: "user_preference",
      entity_id: null,
      evidence_ids: [],
      preference_source: "model_inferred",
      content: { text: "用户偏好高风险" },
    }),
  ], {
    entityIds: ["688205.SH"],
    consumer: "stock_deep_dive",
    now: "2026-07-28T00:00:00.000Z",
  });

  const usageById = Object.fromEntries(
    result.selected.map((item) => [item.memoryId, item.allowedUsage]),
  );
  assert.equal(usageById.framework, "method_context");
  assert.equal(usageById["explicit-preference"], "preference_constraint");
  assert.equal(usageById["inferred-preference"], undefined);
});

test("every selected memory records why and where it was used", () => {
  const retrievals = [];
  const policy = new MemoryRetrievalPolicy({
    recordRetrieval: (memoryId, reason, options) => {
      retrievals.push({ memoryId, reason, options });
      return `ret-${memoryId}`;
    },
  });

  const result = policy.selectForContext([
    memory({ memory_id: "approved-fact" }),
  ], {
    entityIds: ["688205.SH"],
    consumer: "claim_correction",
    retrievalReason: "同一标的事实纠错需要历史基准",
    now: "2026-07-28T00:00:00.000Z",
  });

  assert.equal(result.selected.length, 1);
  assert.equal(retrievals.length, 1);
  assert.equal(retrievals[0].memoryId, "approved-fact");
  assert.equal(retrievals[0].options.consumer, "claim_correction");
  assert.equal(retrievals[0].options.retrievalUsage, "factual_context");
});
