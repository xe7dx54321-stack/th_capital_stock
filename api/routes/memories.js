import crypto from "crypto";
import express from "express";


const TRANSITIONS = {
  candidate: { approve: "approved", reject: "rejected", archive: "archived" },
  approved: { archive: "archived" },
  rejected: { archive: "archived" },
  archived: {},
};

function parseJson(raw, fallback) {
  try { return JSON.parse(raw || ""); } catch { return fallback; }
}

function detail(database, memoryId) {
  const row = database.prepare("SELECT * FROM memory_items WHERE memory_id=?").get(memoryId);
  if (!row) return null;
  return {
    ...row,
    content: parseJson(row.content, {}),
    field_diff: parseJson(row.field_diff_json, []),
    field_diff_json: undefined,
    evidence_links: database.prepare(
      "SELECT evidence_id, relation, created_at FROM memory_evidence_links WHERE memory_id=? ORDER BY evidence_id, relation"
    ).all(memoryId),
    review_log: database.prepare(
      `SELECT review_id, action, previous_status, new_status, reviewer, reason, reviewed_at
       FROM memory_review_log WHERE memory_id=? ORDER BY reviewed_at DESC, review_id DESC`
    ).all(memoryId),
  };
}

function finishSourceRun(database, memory, action, reviewer, reason, reviewedAt) {
  if (!memory.source_run_id) return;
  const run = database.prepare("SELECT status, summary_json FROM workflow_runs WHERE run_id=?").get(memory.source_run_id);
  if (!run || run.status !== "waiting_review") return;
  const summary = parseJson(run.summary_json, {});
  summary.review_status = action === "approve" ? "approved" : action === "reject" ? "rejected" : "archived";
  summary.reviewed_by = reviewer;
  summary.review_reason = reason;
  summary.reviewed_at = reviewedAt;
  database.prepare(
    "UPDATE workflow_runs SET status='completed', summary_json=?, completed_at=? WHERE run_id=?"
  ).run(JSON.stringify(summary), reviewedAt, memory.source_run_id);
  const sequence = database.prepare(
    "SELECT COALESCE(MAX(sequence),0)+1 AS sequence FROM workflow_events WHERE run_id=?"
  ).get(memory.source_run_id).sequence;
  database.prepare(
    `INSERT INTO workflow_events(run_id, sequence, event_type, level, message, payload_json, created_at)
     VALUES (?, ?, 'run.completed', 'info', ?, ?, ?)`
  ).run(
    memory.source_run_id, sequence, `Memory candidate ${summary.review_status}`,
    JSON.stringify({ memory_id: memory.memory_id, review_status: summary.review_status }), reviewedAt,
  );
}

export function createMemoryRouter({ database }) {
  const router = express.Router();

  router.get("/api/memories", (req, res) => {
    const conditions = [];
    const params = [];
    if (req.query.status) { conditions.push("status=?"); params.push(String(req.query.status)); }
    if (req.query.entity_id) { conditions.push("entity_id=?"); params.push(String(req.query.entity_id)); }
    const where = conditions.length ? `WHERE ${conditions.join(" AND ")}` : "";
    const rows = database.prepare(
      `SELECT memory_id, entity_type, entity_id, memory_type, status, confidence, source_run_id,
              parent_memory_id, version, created_at, updated_at, reviewed_by, reviewed_at
       FROM memory_items ${where} ORDER BY datetime(updated_at) DESC, version DESC LIMIT 200`
    ).all(...params);
    res.json({ memories: rows });
  });

  router.get("/api/memories/:id", (req, res) => {
    const memory = detail(database, req.params.id);
    if (!memory) { res.status(404).json({ error: "memory not found" }); return; }
    res.json(memory);
  });

  router.post("/api/memories/:id/review", (req, res) => {
    const action = String(req.body?.action || "").trim();
    const reviewer = String(req.body?.reviewer || "").trim();
    const reason = String(req.body?.reason || "").trim();
    if (!reviewer || !reason) { res.status(400).json({ error: "reviewer and reason are required" }); return; }
    const memory = detail(database, req.params.id);
    if (!memory) { res.status(404).json({ error: "memory not found" }); return; }
    const newStatus = TRANSITIONS[memory.status]?.[action];
    if (!newStatus) { res.status(409).json({ error: `action ${action} is not allowed from ${memory.status}` }); return; }
    const reviewedAt = new Date().toISOString();

    const review = database.transaction(() => {
      if (action === "approve") {
        const previous = database.prepare(
          `SELECT memory_id FROM memory_items
           WHERE entity_type=? AND entity_id=? AND memory_type=? AND status='approved' AND memory_id<>?
           ORDER BY version DESC LIMIT 1`
        ).get(memory.entity_type, memory.entity_id, memory.memory_type, memory.memory_id);
        if (previous) {
          database.prepare(
            "UPDATE memory_items SET status='archived', reviewed_by=?, review_reason=?, reviewed_at=?, updated_at=? WHERE memory_id=?"
          ).run(reviewer, reason, reviewedAt, reviewedAt, previous.memory_id);
          database.prepare(
            "INSERT INTO memory_review_log VALUES (?, ?, 'supersede', 'approved', 'archived', ?, ?, ?)"
          ).run(`review_${crypto.randomUUID().replaceAll("-", "")}`, previous.memory_id, reviewer, reason, reviewedAt);
        }
      }
      database.prepare(
        "UPDATE memory_items SET status=?, reviewed_by=?, review_reason=?, reviewed_at=?, updated_at=? WHERE memory_id=?"
      ).run(newStatus, reviewer, reason, reviewedAt, reviewedAt, memory.memory_id);
      database.prepare(
        `INSERT INTO memory_review_log(
          review_id, memory_id, action, previous_status, new_status, reviewer, reason, reviewed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
      ).run(
        `review_${crypto.randomUUID().replaceAll("-", "")}`, memory.memory_id, action, memory.status,
        newStatus, reviewer, reason, reviewedAt,
      );
      finishSourceRun(database, memory, action, reviewer, reason, reviewedAt);
    });

    try {
      review();
      res.json({ memory: detail(database, memory.memory_id) });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  return router;
}

export { detail as getMemoryDetail };
