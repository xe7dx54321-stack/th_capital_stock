import assert from "node:assert/strict";
import test from "node:test";

import {
  ContextBudget,
  ContextBudgetExceededError,
} from "../../api/services/context-budget.js";

const countTokens = (value) => String(value || "").length;

function buildBudget(overrides = {}) {
  return new ContextBudget({
    maxInputTokens: 120,
    reserveOutputTokens: 20,
    countTokens,
    sectionLimits: {
      system: 20,
      task: 15,
      pinned: 35,
      recentTurns: 20,
      compactedHistory: 10,
      approvedMemory: 10,
      artifactDigests: 10,
    },
    ...overrides,
  });
}

test("assembled context never exceeds the configured token budget", () => {
  const budget = buildBudget();
  const result = budget.fit({
    system: [{ id: "system", text: "S".repeat(18), priority: 100 }],
    task: [{ id: "task", text: "T".repeat(14), priority: 100 }],
    pinned: [{ id: "correction", text: "C".repeat(30), priority: 100, pinned: true }],
    recentTurns: [
      { id: "turn-new", text: "R".repeat(18), priority: 90 },
      { id: "turn-old", text: "O".repeat(18), priority: 10 },
    ],
    compactedHistory: [{ id: "history", text: "H".repeat(20), priority: 30 }],
    approvedMemory: [{ id: "memory", text: "M".repeat(20), priority: 40 }],
    artifactDigests: [{ id: "artifact", text: "A".repeat(20), priority: 20 }],
  });

  assert.ok(result.tokenUsage.totalInputTokens <= 100);
  assert.equal(result.tokenUsage.budgetTokens, 100);
  assert.ok(result.sections.pinned.some((item) => item.id === "correction"));
});

test("omitted sections are recorded with deterministic reasons", () => {
  const budget = buildBudget();
  const result = budget.fit({
    system: [{ id: "system", text: "S".repeat(20), priority: 100 }],
    task: [{ id: "task", text: "T".repeat(15), priority: 100 }],
    pinned: [{ id: "fact", text: "F".repeat(35), priority: 100, pinned: true }],
    recentTurns: [{ id: "recent", text: "R".repeat(20), priority: 90 }],
    compactedHistory: [{ id: "old-summary", text: "H".repeat(30), priority: 30 }],
    approvedMemory: [{ id: "old-memory", text: "M".repeat(30), priority: 20 }],
    artifactDigests: [{ id: "old-artifact", text: "A".repeat(30), priority: 10 }],
  });

  assert.ok(result.omitted.length > 0);
  for (const item of result.omitted) {
    assert.ok(item.id);
    assert.ok(item.section);
    assert.match(item.reason, /section_budget_exceeded|total_budget_exceeded/);
  }
});

test("pinned facts and corrections fail explicitly instead of being silently truncated", () => {
  const budget = buildBudget({
    maxInputTokens: 60,
    reserveOutputTokens: 20,
    sectionLimits: {
      system: 5,
      task: 5,
      pinned: 50,
      recentTurns: 0,
      compactedHistory: 0,
      approvedMemory: 0,
      artifactDigests: 0,
    },
  });

  assert.throws(
    () => budget.fit({
      system: [],
      task: [],
      pinned: [{ id: "oversized-correction", text: "C".repeat(45), pinned: true }],
    }),
    (error) => error instanceof ContextBudgetExceededError
      && error.code === "pinned_context_exceeds_budget",
  );
});
