import Database from "better-sqlite3";


const TERMINAL_STATUSES = new Set(["completed", "failed", "cancelled"]);
const INLINE_WORKFLOW_PREFIX = "agent_";

export class WorkflowConflictError extends Error {}

function parseJson(raw, fallback) {
  try {
    return JSON.parse(raw || "");
  } catch {
    return fallback;
  }
}

function nowIso() {
  return new Date().toISOString();
}

export class WorkflowRepository {
  constructor(dbPath) {
    this.dbPath = dbPath;
    this.db = new Database(dbPath);
    this.db.pragma("busy_timeout = 15000");
    this.db.pragma("foreign_keys = ON");
  }

  close() {
    this.db.close();
  }

  createQueuedRun({ runId, workflowId, input, idempotencyKey, requestHash }) {
    const transaction = this.db.transaction(() => {
      if (idempotencyKey) {
        const previous = this.db.prepare(
          "SELECT run_id, request_hash FROM workflow_run_requests WHERE idempotency_key=?"
        ).get(idempotencyKey);
        if (previous) {
          if (previous.request_hash !== requestHash) {
            throw new WorkflowConflictError("Idempotency key was already used with a different request");
          }
          return { run: this.getRun(previous.run_id), reused: true };
        }
      }

      const active = this.db.prepare(
        `SELECT run_id FROM workflow_runs
         WHERE status IN ('queued','running') AND workflow_id NOT LIKE '${INLINE_WORKFLOW_PREFIX}%'
         ORDER BY created_at LIMIT 1`
      ).get();
      if (active) {
        throw new WorkflowConflictError(`Write workflow already active: ${active.run_id}`);
      }

      const createdAt = nowIso();
      this.db.prepare(
        `INSERT INTO workflow_runs(run_id, workflow_id, status, input_json, created_at, process_status)
         VALUES (?, ?, 'queued', ?, ?, 'pending')`
      ).run(runId, workflowId, JSON.stringify(input), createdAt);
      this.db.prepare(
        `INSERT INTO workflow_events(run_id, sequence, event_type, level, message, payload_json, created_at)
         VALUES (?, 1, 'run.queued', 'info', ?, '{}', ?)`
      ).run(runId, `Queued ${workflowId}`, createdAt);
      if (idempotencyKey) {
        this.db.prepare(
          `INSERT INTO workflow_run_requests(idempotency_key, run_id, request_hash, created_at)
           VALUES (?, ?, ?, ?)`
        ).run(idempotencyKey, runId, requestHash, createdAt);
      }
      return { run: this.getRun(runId), reused: false };
    });
    return transaction();
  }

  createInlineRun({ runId, workflowId, input }) {
    if (!String(workflowId).startsWith(INLINE_WORKFLOW_PREFIX)) {
      throw new TypeError(`Inline workflow_id must start with ${INLINE_WORKFLOW_PREFIX}`);
    }
    const createdAt = nowIso();
    const transaction = this.db.transaction(() => {
      this.db.prepare(
        `INSERT INTO workflow_runs(
           run_id, workflow_id, status, input_json, created_at, started_at, process_status
         ) VALUES (?, ?, 'running', ?, ?, ?, 'inline')`
      ).run(runId, workflowId, JSON.stringify(input || {}), createdAt, createdAt);
      this.db.prepare(
        `INSERT INTO workflow_events(
           run_id, sequence, event_type, level, message, payload_json, created_at
         ) VALUES (?, 1, 'run.started', 'info', ?, '{}', ?)`
      ).run(runId, `Started ${workflowId}`, createdAt);
      return this.getRun(runId);
    });
    return transaction();
  }

  appendEvent(runId, { eventType, stageId = null, level = "info", message, payload = {} }) {
    const transaction = this.db.transaction(() => {
      const sequence = this.db.prepare(
        "SELECT COALESCE(MAX(sequence),0)+1 AS sequence FROM workflow_events WHERE run_id=?"
      ).get(runId).sequence;
      const createdAt = nowIso();
      this.db.prepare(
        `INSERT INTO workflow_events(
           run_id, sequence, event_type, stage_id, level, message, payload_json, created_at
         ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
      ).run(
        runId,
        sequence,
        eventType,
        stageId,
        level,
        String(message || "").slice(0, 2000),
        JSON.stringify(payload || {}),
        createdAt,
      );
      return { run_id: runId, sequence, event_type: eventType, stage_id: stageId, level, message, payload, created_at: createdAt };
    });
    return transaction();
  }

  finalizeInlineRun(runId, {
    status,
    summary = {},
    errorCode = null,
    errorMessage = null,
    eventType = `run.${status}`,
    eventMessage = `Run ${status}`,
    eventLevel = status === "failed" ? "error" : "info",
    eventPayload = {},
  }) {
    const allowedStatuses = new Set(["completed", "failed", "waiting_review", "cancelled"]);
    if (!allowedStatuses.has(status)) throw new TypeError(`Unsupported inline run status: ${status}`);
    const completedAt = status === "waiting_review" ? null : nowIso();
    const transaction = this.db.transaction(() => {
      const updated = this.db.prepare(
        `UPDATE workflow_runs
         SET status=?, summary_json=?, error_code=?, error_message=?, completed_at=?, process_status=?
         WHERE run_id=? AND workflow_id LIKE '${INLINE_WORKFLOW_PREFIX}%'`
      ).run(
        status,
        JSON.stringify(summary || {}),
        errorCode,
        errorMessage ? String(errorMessage).slice(0, 2000) : null,
        completedAt,
        status,
        runId,
      );
      if (updated.changes !== 1) throw new Error(`Inline workflow run not found: ${runId}`);
      const sequence = this.db.prepare(
        "SELECT COALESCE(MAX(sequence),0)+1 AS sequence FROM workflow_events WHERE run_id=?"
      ).get(runId).sequence;
      const eventCreatedAt = nowIso();
      this.db.prepare(
        `INSERT INTO workflow_events(
           run_id, sequence, event_type, level, message, payload_json, created_at
         ) VALUES (?, ?, ?, ?, ?, ?, ?)`
      ).run(
        runId,
        sequence,
        eventType,
        eventLevel,
        String(eventMessage).slice(0, 2000),
        JSON.stringify(eventPayload || {}),
        eventCreatedAt,
      );
      return this.getRun(runId);
    });
    return transaction();
  }

  registerArtifact({ artifactId, runId, artifactType, title, relativePath, mimeType, metadata = {} }) {
    const createdAt = nowIso();
    this.db.prepare(
      `INSERT INTO workflow_artifacts(
         artifact_id, run_id, artifact_type, title, relative_path, mime_type, metadata_json, created_at
       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
    ).run(
      artifactId,
      runId,
      artifactType,
      title,
      relativePath,
      mimeType,
      JSON.stringify(metadata || {}),
      createdAt,
    );
    return this.getArtifact(artifactId);
  }

  getRun(runId) {
    const row = this.db.prepare(
      `SELECT run_id, workflow_id, status, input_json, summary_json, error_code, error_message,
              created_at, started_at, completed_at, cancel_requested_at, process_id, process_status
       FROM workflow_runs WHERE run_id=?`
    ).get(runId);
    if (!row) return null;
    return {
      run_id: row.run_id,
      workflow_id: row.workflow_id,
      status: row.status,
      input: parseJson(row.input_json, {}),
      summary: parseJson(row.summary_json, {}),
      error_code: row.error_code,
      error_message: row.error_message,
      created_at: row.created_at,
      started_at: row.started_at,
      completed_at: row.completed_at,
      cancel_requested_at: row.cancel_requested_at,
      process_id: row.process_id,
      process_status: row.process_status,
    };
  }

  listRuns(limit = 50) {
    return this.db.prepare(
      "SELECT run_id FROM workflow_runs ORDER BY datetime(created_at) DESC LIMIT ?"
    ).all(Math.max(1, Math.min(Number(limit) || 50, 200))).map((row) => this.getRun(row.run_id));
  }

  listEvents(runId, afterSequence = 0) {
    return this.db.prepare(
      `SELECT run_id, sequence, event_type, stage_id, level, message, payload_json, created_at
       FROM workflow_events WHERE run_id=? AND sequence>? ORDER BY sequence`
    ).all(runId, Math.max(0, Number(afterSequence) || 0)).map((row) => ({
      run_id: row.run_id,
      sequence: row.sequence,
      event_type: row.event_type,
      stage_id: row.stage_id,
      level: row.level,
      message: row.message,
      payload: parseJson(row.payload_json, {}),
      created_at: row.created_at,
    }));
  }

  listArtifacts(runId) {
    return this.db.prepare(
      `SELECT artifact_id, run_id, artifact_type, title, relative_path, mime_type, metadata_json, created_at
       FROM workflow_artifacts WHERE run_id=? ORDER BY datetime(created_at), artifact_id`
    ).all(runId).map((row) => ({
      artifact_id: row.artifact_id,
      run_id: row.run_id,
      artifact_type: row.artifact_type,
      title: row.title,
      relative_path: row.relative_path,
      mime_type: row.mime_type,
      metadata: parseJson(row.metadata_json, {}),
      created_at: row.created_at,
    }));
  }

  getArtifact(artifactId) {
    const row = this.db.prepare(
      `SELECT artifact_id, run_id, artifact_type, title, relative_path, mime_type, metadata_json, created_at
       FROM workflow_artifacts WHERE artifact_id=?`
    ).get(artifactId);
    if (!row) return null;
    return {
      artifact_id: row.artifact_id,
      run_id: row.run_id,
      artifact_type: row.artifact_type,
      title: row.title,
      relative_path: row.relative_path,
      mime_type: row.mime_type,
      metadata: parseJson(row.metadata_json, {}),
      created_at: row.created_at,
    };
  }

  setProcessState(runId, processId, processStatus) {
    this.db.prepare(
      "UPDATE workflow_runs SET process_id=COALESCE(?, process_id), process_status=? WHERE run_id=?"
    ).run(processId ?? null, processStatus, runId);
  }

  failIfActive(runId, errorMessage) {
    const run = this.getRun(runId);
    if (!run || !["queued", "running"].includes(run.status)) return;
    const transaction = this.db.transaction(() => {
      const sequence = this.db.prepare(
        "SELECT COALESCE(MAX(sequence),0)+1 AS sequence FROM workflow_events WHERE run_id=?"
      ).get(runId).sequence;
      const completedAt = nowIso();
      this.db.prepare(
        `UPDATE workflow_runs
         SET status='failed', error_code='process_exit', error_message=?, completed_at=?, process_status='failed'
         WHERE run_id=? AND status IN ('queued','running')`
      ).run(String(errorMessage).slice(0, 2000), completedAt, runId);
      this.db.prepare(
        `INSERT INTO workflow_events(run_id, sequence, event_type, level, message, payload_json, created_at)
         VALUES (?, ?, 'run.failed', 'error', ?, '{"error_code":"process_exit"}', ?)`
      ).run(runId, sequence, String(errorMessage).slice(0, 2000), completedAt);
    });
    transaction();
  }

  requestCancel(runId) {
    const run = this.getRun(runId);
    if (!run) return null;
    if (TERMINAL_STATUSES.has(run.status)) return { requested: false, run };
    const requestedAt = nowIso();
    const transaction = this.db.transaction(() => {
      this.db.prepare(
        "UPDATE workflow_runs SET cancel_requested_at=COALESCE(cancel_requested_at, ?) WHERE run_id=?"
      ).run(requestedAt, runId);
      if (run.status === "waiting_review") {
        const sequence = this.db.prepare(
          "SELECT COALESCE(MAX(sequence),0)+1 AS sequence FROM workflow_events WHERE run_id=?"
        ).get(runId).sequence;
        this.db.prepare(
          "UPDATE workflow_runs SET status='cancelled', completed_at=? WHERE run_id=?"
        ).run(requestedAt, runId);
        this.db.prepare(
          `INSERT INTO workflow_events(run_id, sequence, event_type, level, message, payload_json, created_at)
           VALUES (?, ?, 'run.cancelled', 'info', 'Run cancelled while waiting for review', '{}', ?)`
        ).run(runId, sequence, requestedAt);
      }
    });
    transaction();
    return { requested: true, run: this.getRun(runId) };
  }
}
