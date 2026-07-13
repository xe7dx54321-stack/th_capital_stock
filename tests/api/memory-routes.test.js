import assert from "node:assert/strict";
import test from "node:test";

import Database from "better-sqlite3";
import express from "express";

import { createMemoryRouter } from "../../api/routes/memories.js";


test("memory review archives the old version and records reviewer reason and time", async (t) => {
  const db = new Database(":memory:");
  db.exec(`
    CREATE TABLE memory_items (
      memory_id TEXT PRIMARY KEY, entity_type TEXT, entity_id TEXT, memory_type TEXT, content TEXT,
      status TEXT, confidence REAL, source_run_id TEXT, valid_from TEXT, valid_until TEXT,
      last_verified_at TEXT, created_at TEXT, updated_at TEXT, parent_memory_id TEXT, version INTEGER,
      field_diff_json TEXT, reviewed_by TEXT, review_reason TEXT, reviewed_at TEXT
    );
    CREATE TABLE memory_evidence_links (memory_id TEXT, evidence_id TEXT, relation TEXT, created_at TEXT, PRIMARY KEY(memory_id,evidence_id,relation));
    CREATE TABLE memory_review_log (review_id TEXT PRIMARY KEY, memory_id TEXT, action TEXT, previous_status TEXT, new_status TEXT, reviewer TEXT, reason TEXT, reviewed_at TEXT);
    CREATE TABLE workflow_runs (run_id TEXT PRIMARY KEY, workflow_id TEXT, status TEXT, summary_json TEXT, completed_at TEXT);
    CREATE TABLE workflow_events (run_id TEXT, sequence INTEGER, event_type TEXT, stage_id TEXT, level TEXT, message TEXT, payload_json TEXT, created_at TEXT, PRIMARY KEY(run_id,sequence));
  `);
  const insert = db.prepare(`INSERT INTO memory_items(
    memory_id,entity_type,entity_id,memory_type,content,status,created_at,updated_at,parent_memory_id,version,field_diff_json,source_run_id
  ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)`);
  insert.run("memory-v1", "ticker", "300308.SZ", "investment_thesis", '{"thesis":"old"}', "approved", "2026-07-01", "2026-07-01", null, 1, "[]", null);
  insert.run("memory-v2", "ticker", "300308.SZ", "investment_thesis", '{"thesis":"new"}', "candidate", "2026-07-13", "2026-07-13", "memory-v1", 2, '[{"field":"thesis","before":"old","after":"new"}]', "run-thesis");
  db.prepare("INSERT INTO memory_evidence_links VALUES (?,?,?,?)").run("memory-v2", "ev-1", "supports", "2026-07-13");
  db.prepare("INSERT INTO workflow_runs VALUES (?,?,?,?,?)").run("run-thesis", "thesis_update", "waiting_review", '{}', null);

  const app = express();
  app.use(express.json());
  app.use(createMemoryRouter({ database: db }));
  const server = await new Promise((resolve) => { const instance = app.listen(0, "127.0.0.1", () => resolve(instance)); });
  t.after(async () => { await new Promise((resolve) => server.close(resolve)); db.close(); });
  const base = `http://127.0.0.1:${server.address().port}`;

  const missingAudit = await fetch(`${base}/api/memories/memory-v2/review`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action: "approve" }),
  });
  assert.equal(missingAudit.status, 400);

  const response = await fetch(`${base}/api/memories/memory-v2/review`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action: "approve", reviewer: "owner", reason: "source checked" }),
  });
  assert.equal(response.status, 200);
  const body = await response.json();
  assert.equal(body.memory.status, "approved");
  assert.equal(body.memory.review_log[0].reviewer, "owner");
  assert.equal(body.memory.review_log[0].reason, "source checked");
  assert.ok(body.memory.review_log[0].reviewed_at);
  assert.equal(db.prepare("SELECT status FROM memory_items WHERE memory_id='memory-v1'").pluck().get(), "archived");
  assert.equal(db.prepare("SELECT content FROM memory_items WHERE memory_id='memory-v1'").pluck().get(), '{"thesis":"old"}');
  assert.equal(db.prepare("SELECT status FROM workflow_runs WHERE run_id='run-thesis'").pluck().get(), "completed");
});
