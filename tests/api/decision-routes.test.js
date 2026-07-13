import assert from "node:assert/strict";
import test from "node:test";

import Database from "better-sqlite3";
import express from "express";

import { createDecisionRouter } from "../../api/routes/decisions.js";


function createDatabase() {
  const db = new Database(":memory:");
  db.exec(`
    CREATE TABLE decision_ledger (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      decision_id TEXT UNIQUE NOT NULL,
      recommendation_id TEXT NOT NULL,
      ticker TEXT,
      market TEXT,
      theme TEXT,
      action TEXT NOT NULL,
      status TEXT NOT NULL,
      decision_time TEXT NOT NULL,
      reference_price REAL,
      currency TEXT,
      thesis_summary TEXT,
      evidence_ids_json TEXT NOT NULL DEFAULT '[]',
      bear_case_summary TEXT,
      kill_conditions_json TEXT NOT NULL DEFAULT '[]',
      risk_notes TEXT,
      human_review_status TEXT,
      outcome_status TEXT NOT NULL DEFAULT 'open',
      metadata_json TEXT NOT NULL DEFAULT '{}',
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      source_run_id TEXT,
      source_memory_id TEXT,
      review_due_at TEXT,
      outcome_summary TEXT,
      outcome_recorded_at TEXT,
      outcome_evidence_ids_json TEXT NOT NULL DEFAULT '[]'
    );
    CREATE TABLE decision_outcome_log (
      outcome_id TEXT PRIMARY KEY,
      decision_id TEXT NOT NULL,
      outcome_status TEXT NOT NULL,
      summary TEXT NOT NULL,
      evidence_ids_json TEXT NOT NULL DEFAULT '[]',
      observed_price REAL,
      recorded_by TEXT NOT NULL,
      recorded_at TEXT NOT NULL,
      metadata_json TEXT NOT NULL DEFAULT '{}'
    );
    CREATE TABLE workflow_runs (run_id TEXT PRIMARY KEY);
    CREATE TABLE memory_items (memory_id TEXT PRIMARY KEY);
    INSERT INTO workflow_runs VALUES ('run-1');
    INSERT INTO memory_items VALUES ('memory-1');
  `);
  return db;
}

async function startApp(t, db) {
  const app = express();
  app.use(express.json());
  app.use(createDecisionRouter({ database: db }));
  const server = await new Promise((resolve) => {
    const instance = app.listen(0, "127.0.0.1", () => resolve(instance));
  });
  t.after(async () => { await new Promise((resolve) => server.close(resolve)); db.close(); });
  return `http://127.0.0.1:${server.address().port}`;
}

test("decision API creates an auditable observation and filters overdue reviews", async (t) => {
  const db = createDatabase();
  const base = await startApp(t, db);

  const invalid = await fetch(`${base}/api/decisions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ticker: "300308.SZ", thesis: "仅有观点" }),
  });
  assert.equal(invalid.status, 400);

  const response = await fetch(`${base}/api/decisions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ticker: "300308.SZ",
      action: "continue_observing",
      thesis: "订单质量改善，但仍需验证利润兑现。",
      counterargument: "行业价格竞争可能抵消订单增长。",
      evidence_ids: ["ev-1", "ev-2"],
      invalidation_conditions: ["毛利率连续两个季度下降"],
      reference_price: 96.5,
      review_due_at: "2000-01-01T00:00:00.000Z",
      source_run_id: "run-1",
      source_memory_id: "memory-1",
    }),
  });
  assert.equal(response.status, 201);
  const created = await response.json();
  assert.equal(created.decision.ticker, "300308.SZ");
  assert.deepEqual(created.decision.evidence_ids, ["ev-1", "ev-2"]);
  assert.equal(created.decision.source_run_id, "run-1");

  const list = await fetch(`${base}/api/decisions?ticker=300308.SZ&overdue=true`);
  assert.equal(list.status, 200);
  const body = await list.json();
  assert.equal(body.decisions.length, 1);
  assert.equal(body.decisions[0].review_state, "overdue");
});

test("outcome API appends facts without changing the original judgment", async (t) => {
  const db = createDatabase();
  const base = await startApp(t, db);
  const original = {
    ticker: "300308.SZ",
    action: "deepen_research",
    thesis: "现金流改善是核心观察点。",
    counterargument: "应收账款可能掩盖现金流质量。",
    evidence_ids: ["ev-3"],
    invalidation_conditions: ["经营现金流再次转负"],
    review_due_at: "2030-01-01T00:00:00.000Z",
  };
  const createdResponse = await fetch(`${base}/api/decisions`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(original),
  });
  const created = (await createdResponse.json()).decision;

  const outcomeResponse = await fetch(`${base}/api/decisions/${created.decision_id}/outcome`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      outcome_status: "partially_confirmed",
      summary: "价格上涨，但现金流证据仍不完整。",
      evidence_ids: ["ev-outcome-1"],
      observed_price: 102.4,
      recorded_by: "本地研究者",
    }),
  });
  assert.equal(outcomeResponse.status, 200);
  const updated = (await outcomeResponse.json()).decision;
  assert.equal(updated.thesis_summary, original.thesis);
  assert.equal(updated.bear_case_summary, original.counterargument);
  assert.deepEqual(updated.kill_conditions, original.invalidation_conditions);
  assert.equal(updated.outcome_history.length, 1);
  assert.equal(updated.outcome_history[0].summary, "价格上涨，但现金流证据仍不完整。");
});
