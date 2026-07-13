import assert from "node:assert/strict";
import { mkdtempSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";


const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const tempRoot = mkdtempSync(path.join(os.tmpdir(), "smr-api-"));
const dbPath = path.join(tempRoot, "runtime.db");
const artifactRoot = path.join(tempRoot, "artifacts");
const python = process.platform === "win32"
  ? path.join(ROOT, ".venv", "Scripts", "python.exe")
  : path.join(ROOT, ".venv", "bin", "python");
process.env.SMR_DB_PATH = dbPath;
process.env.SMR_ARTIFACT_ROOTS = artifactRoot;
process.env.SMR_PYTHON = python;

const { app } = await import(`../../api/app.js?workflow-test=${Date.now()}`);
const server = await new Promise((resolve) => {
  const instance = app.listen(0, "127.0.0.1", () => resolve(instance));
});
const address = server.address();
const baseUrl = `http://127.0.0.1:${address.port}`;

async function jsonRequest(url, options) {
  const response = await fetch(`${baseUrl}${url}`, options);
  const body = await response.json();
  return { response, body };
}

async function waitForRun(runId, timeoutMs = 15000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const { body } = await jsonRequest(`/api/workflow-runs/${runId}`);
    if (["completed", "failed", "cancelled", "waiting_review"].includes(body.status)
        && body.process_status !== "running") return body;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error(`workflow ${runId} did not finish`);
}

test("workflow API validates, queues, resumes, streams and serves a safe artifact", async (t) => {
  t.after(async () => {
    await new Promise((resolve) => server.close(resolve));
    app.locals.workflowRepository.close();
  });

  const health = await jsonRequest("/api/health");
  assert.equal(health.response.status, 200);
  assert.equal(health.body.status, "ok");

  const workflows = await jsonRequest("/api/workflows");
  assert.equal(workflows.response.status, 200);
  assert.deepEqual(
    workflows.body.workflows.map((item) => item.workflow_id).sort(),
    ["daily_brief", "portfolio_review", "stock_deep_dive", "thesis_update"],
  );

  const invalid = await jsonRequest("/api/workflow-runs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ workflow_id: "arbitrary_shell", input: {} }),
  });
  assert.equal(invalid.response.status, 400);

  const request = {
    method: "POST",
    headers: { "Content-Type": "application/json", "Idempotency-Key": "stock-fixture-1" },
    body: JSON.stringify({
      workflow_id: "stock_deep_dive",
      input: { ticker: "300308.SZ", allow_network: false },
    }),
  };
  const created = await jsonRequest("/api/workflow-runs", request);
  assert.equal(created.response.status, 202);
  assert.equal(created.body.status, "queued");
  const repeated = await jsonRequest("/api/workflow-runs", request);
  assert.equal(repeated.response.status, 200);
  assert.equal(repeated.body.run_id, created.body.run_id);

  const run = await waitForRun(created.body.run_id);
  assert.equal(run.status, "completed");
  assert.ok(Number.isInteger(run.process_id));
  assert.equal(run.summary.conclusion_status, "cannot_conclude");
  assert.equal(run.artifacts.length, 1);

  const events = await jsonRequest(`/api/workflow-runs/${run.run_id}/events?after=2`);
  assert.equal(events.response.status, 200);
  assert.ok(events.body.events.length > 0);
  assert.ok(events.body.events.every((event) => event.sequence > 2));

  const stream = await fetch(`${baseUrl}/api/workflow-runs/${run.run_id}/stream?after=0`);
  const streamText = await stream.text();
  assert.match(stream.headers.get("content-type"), /text\/event-stream/);
  assert.match(streamText, /event: run\.completed/);

  const artifact = await fetch(`${baseUrl}/api/artifacts/${run.artifacts[0].artifact_id}`);
  assert.equal(artifact.status, 200);
  assert.match(artifact.headers.get("content-type"), /text\/markdown/);
  assert.match(await artifact.text(), /cannot_conclude/);

  const cancelMissing = await jsonRequest("/api/workflow-runs/run_missing/cancel", { method: "POST" });
  assert.equal(cancelMissing.response.status, 404);
});
