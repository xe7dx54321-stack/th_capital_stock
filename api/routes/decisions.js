import crypto from "crypto";
import express from "express";


const ACTIONS = new Set([
  "continue_observing",
  "deepen_research",
  "reduce_attention",
  "close_thesis",
]);
const OUTCOME_STATUSES = new Set([
  "open",
  "confirmed",
  "failed",
  "partially_confirmed",
  "invalidated",
  "closed",
]);
const TICKER_PATTERN = /^(?:\d{6}\.(?:SZ|SH|BJ)|\d{5}\.HK|[A-Z][A-Z0-9.-]{0,9})$/;

function parseJson(raw, fallback) {
  try { return JSON.parse(raw || ""); } catch { return fallback; }
}

function cleanText(value) {
  return String(value || "").trim();
}

function cleanStringArray(value) {
  if (!Array.isArray(value)) return [];
  return [...new Set(value.map(cleanText).filter(Boolean))].slice(0, 100);
}

function cleanPrice(value) {
  if (value === undefined || value === null || value === "") return null;
  const number = Number(value);
  return Number.isFinite(number) && number > 0 ? number : Number.NaN;
}

function inferMarket(ticker) {
  if (ticker.endsWith(".SH") || ticker.endsWith(".SZ") || ticker.endsWith(".BJ")) return "CN_A";
  if (ticker.endsWith(".HK")) return "HK";
  return "US";
}

function relationExists(database, name) {
  return Boolean(database.prepare("SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name=?").get(name));
}

function outcomeHistory(database, decisionId) {
  return database.prepare(
    `SELECT outcome_id, outcome_status, summary, evidence_ids_json, observed_price,
            recorded_by, recorded_at, metadata_json
     FROM decision_outcome_log WHERE decision_id=?
     ORDER BY datetime(recorded_at) DESC, outcome_id DESC`
  ).all(decisionId).map((row) => ({
    ...row,
    evidence_ids: parseJson(row.evidence_ids_json, []),
    evidence_ids_json: undefined,
    metadata: parseJson(row.metadata_json, {}),
    metadata_json: undefined,
  }));
}

function detail(database, decisionId) {
  const row = database.prepare("SELECT * FROM decision_ledger WHERE decision_id=?").get(decisionId);
  if (!row) return null;
  const now = Date.now();
  const due = row.review_due_at ? Date.parse(row.review_due_at) : Number.NaN;
  const reviewState = row.outcome_status !== "open"
    ? "reviewed"
    : Number.isFinite(due) && due <= now ? "overdue" : "upcoming";
  return {
    ...row,
    evidence_ids: parseJson(row.evidence_ids_json, []),
    evidence_ids_json: undefined,
    kill_conditions: parseJson(row.kill_conditions_json, []),
    kill_conditions_json: undefined,
    outcome_evidence_ids: parseJson(row.outcome_evidence_ids_json, []),
    outcome_evidence_ids_json: undefined,
    metadata: parseJson(row.metadata_json, {}),
    metadata_json: undefined,
    review_state: reviewState,
    outcome_history: outcomeHistory(database, decisionId),
  };
}

export function createDecisionRouter({ database }) {
  const router = express.Router();

  router.get("/api/decisions", (req, res) => {
    const conditions = [];
    const params = [];
    if (req.query.ticker) { conditions.push("UPPER(ticker)=?"); params.push(cleanText(req.query.ticker).toUpperCase()); }
    if (req.query.outcome_status) { conditions.push("outcome_status=?"); params.push(cleanText(req.query.outcome_status)); }
    if (String(req.query.overdue || "") === "true") {
      conditions.push("outcome_status='open' AND review_due_at IS NOT NULL AND datetime(review_due_at)<=datetime('now')");
    }
    const limit = Math.max(1, Math.min(Number(req.query.limit) || 100, 200));
    const where = conditions.length ? `WHERE ${conditions.join(" AND ")}` : "";
    const rows = database.prepare(
      `SELECT decision_id FROM decision_ledger ${where}
       ORDER BY CASE WHEN outcome_status='open' THEN 0 ELSE 1 END,
                datetime(COALESCE(review_due_at, decision_time)) ASC LIMIT ?`
    ).all(...params, limit);
    res.json({ decisions: rows.map((row) => detail(database, row.decision_id)) });
  });

  router.get("/api/decisions/:id", (req, res) => {
    const decision = detail(database, req.params.id);
    if (!decision) { res.status(404).json({ error: "decision not found" }); return; }
    res.json(decision);
  });

  router.post("/api/decisions", (req, res) => {
    const ticker = cleanText(req.body?.ticker).toUpperCase();
    const action = cleanText(req.body?.action);
    const thesis = cleanText(req.body?.thesis);
    const counterargument = cleanText(req.body?.counterargument);
    const evidenceIds = cleanStringArray(req.body?.evidence_ids);
    const invalidationConditions = cleanStringArray(req.body?.invalidation_conditions);
    const reviewDueAt = cleanText(req.body?.review_due_at);
    const sourceRunId = cleanText(req.body?.source_run_id);
    const sourceMemoryId = cleanText(req.body?.source_memory_id);
    const referencePrice = cleanPrice(req.body?.reference_price);
    if (!TICKER_PATTERN.test(ticker)) { res.status(400).json({ error: "valid ticker is required" }); return; }
    if (!ACTIONS.has(action)) { res.status(400).json({ error: "unsupported decision action" }); return; }
    if (!thesis || !counterargument) { res.status(400).json({ error: "thesis and counterargument are required" }); return; }
    if (evidenceIds.length === 0) { res.status(400).json({ error: "at least one evidence_id is required" }); return; }
    if (invalidationConditions.length === 0) { res.status(400).json({ error: "at least one invalidation condition is required" }); return; }
    if (!reviewDueAt || !Number.isFinite(Date.parse(reviewDueAt))) { res.status(400).json({ error: "valid review_due_at is required" }); return; }
    if (Number.isNaN(referencePrice)) { res.status(400).json({ error: "reference_price must be positive" }); return; }
    if (sourceRunId && (!relationExists(database, "workflow_runs") || !database.prepare("SELECT 1 FROM workflow_runs WHERE run_id=?").get(sourceRunId))) {
      res.status(400).json({ error: "source_run_id does not exist" }); return;
    }
    if (sourceMemoryId && (!relationExists(database, "memory_items") || !database.prepare("SELECT 1 FROM memory_items WHERE memory_id=?").get(sourceMemoryId))) {
      res.status(400).json({ error: "source_memory_id does not exist" }); return;
    }

    const decisionId = `decision_${crypto.randomUUID().replaceAll("-", "")}`;
    const now = new Date().toISOString();
    const metadata = {
      recorded_by: cleanText(req.body?.recorded_by) || "本地研究者",
      question: cleanText(req.body?.question) || undefined,
      time_horizon: cleanText(req.body?.time_horizon) || undefined,
    };
    database.prepare(
      `INSERT INTO decision_ledger(
        decision_id, recommendation_id, ticker, market, theme, action, status, decision_time,
        reference_price, currency, thesis_summary, evidence_ids_json, bear_case_summary,
        kill_conditions_json, risk_notes, human_review_status, outcome_status, metadata_json,
        created_at, updated_at, source_run_id, source_memory_id, review_due_at,
        outcome_evidence_ids_json
      ) VALUES (?, ?, ?, ?, ?, ?, 'observation_only', ?, ?, ?, ?, ?, ?, ?, ?,
                'owner_recorded', 'open', ?, ?, ?, ?, ?, ?, '[]')`
    ).run(
      decisionId,
      cleanText(req.body?.recommendation_id) || decisionId,
      ticker,
      cleanText(req.body?.market) || inferMarket(ticker),
      cleanText(req.body?.theme) || null,
      action,
      now,
      referencePrice,
      cleanText(req.body?.currency) || null,
      thesis,
      JSON.stringify(evidenceIds),
      counterargument,
      JSON.stringify(invalidationConditions),
      cleanText(req.body?.risk_notes) || null,
      JSON.stringify(metadata),
      now,
      now,
      sourceRunId || null,
      sourceMemoryId || null,
      new Date(reviewDueAt).toISOString(),
    );
    res.status(201).json({ decision: detail(database, decisionId) });
  });

  router.post("/api/decisions/:id/outcome", (req, res) => {
    const decision = detail(database, req.params.id);
    if (!decision) { res.status(404).json({ error: "decision not found" }); return; }
    const outcomeStatus = cleanText(req.body?.outcome_status);
    const summary = cleanText(req.body?.summary);
    const recordedBy = cleanText(req.body?.recorded_by);
    const evidenceIds = cleanStringArray(req.body?.evidence_ids);
    const observedPrice = cleanPrice(req.body?.observed_price);
    if (!OUTCOME_STATUSES.has(outcomeStatus)) { res.status(400).json({ error: "unsupported outcome_status" }); return; }
    if (!summary || !recordedBy) { res.status(400).json({ error: "summary and recorded_by are required" }); return; }
    if (Number.isNaN(observedPrice)) { res.status(400).json({ error: "observed_price must be positive" }); return; }
    const recordedAt = new Date().toISOString();
    const outcomeId = `outcome_${crypto.randomUUID().replaceAll("-", "")}`;
    const write = database.transaction(() => {
      database.prepare(
        `INSERT INTO decision_outcome_log(
          outcome_id, decision_id, outcome_status, summary, evidence_ids_json,
          observed_price, recorded_by, recorded_at, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
      ).run(
        outcomeId, decision.decision_id, outcomeStatus, summary, JSON.stringify(evidenceIds),
        observedPrice, recordedBy, recordedAt, JSON.stringify(req.body?.metadata || {}),
      );
      database.prepare(
        `UPDATE decision_ledger
         SET outcome_status=?, outcome_summary=?, outcome_recorded_at=?,
             outcome_evidence_ids_json=?, updated_at=? WHERE decision_id=?`
      ).run(outcomeStatus, summary, recordedAt, JSON.stringify(evidenceIds), recordedAt, decision.decision_id);
    });
    write();
    res.json({ decision: detail(database, decision.decision_id) });
  });

  return router;
}

export { detail as getDecisionDetail };
