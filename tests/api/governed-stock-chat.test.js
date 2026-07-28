import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import {
  DEFAULT_GOVERNED_WORKFLOW_TIMEOUT_MS,
  GovernedWorkflowRunner,
} from "../../api/services/governed-workflow-runner.js";
import { TASK_TYPES, WorkflowEngine } from "../../api/services/workflow-engine.js";


test("stock deep analysis production flow contains no legacy data or LLM steps", () => {
  assert.deepEqual(
    TASK_TYPES.STOCK_DEEP_ANALYSIS.defaultFlow,
    ["resolve_entity", "run_governed_stock_deep_dive"],
  );
  assert.deepEqual(
    TASK_TYPES.STOCK_DEEP_ANALYSIS.tools,
    ["resolve_entity", "run_governed_stock_deep_dive"],
  );
});

test("governed workflow timeout defaults to ten minutes", () => {
  const runner = new GovernedWorkflowRunner({
    repository: {},
    processService: {},
    artifactRoots: ["."],
  });
  assert.equal(DEFAULT_GOVERNED_WORKFLOW_TIMEOUT_MS, 600_000);
  assert.equal(runner.timeoutMs, 600_000);
});

test("terminal status observed just after the deadline is not misclassified as timeout", async () => {
  let now = 0;
  let status = "running";
  const runner = new GovernedWorkflowRunner({
    repository: {
      getRun(runId) {
        return { run_id: runId, status };
      },
      listEvents() {
        return [];
      },
    },
    processService: {},
    artifactRoots: ["."],
    pollIntervalMs: 10,
    timeoutMs: 10,
    now: () => now,
    async sleepFn(milliseconds) {
      now += milliseconds + 1;
      status = "completed";
    },
  });

  const result = await runner.waitForTerminalRun("run_boundary_fixture");
  assert.equal(result.status, "completed");
});

test("workflow engine returns the governed V2 report without invoking legacy synthesis", async () => {
  const calls = [];
  const engine = new WorkflowEngine({
    governedWorkflowRunner: {
      async runStockDeepDive(input) {
        calls.push(input);
        return {
          run_id: "run_v2_fixture",
          workflow_id: "stock_deep_dive",
          status: "completed",
          summary: { conclusion_status: "supported", research_readiness: "research_ready" },
          report: "# 个股深度研究 V2 — 300308.SZ\n\n- 可信事实 [E101]\n",
          packet: {
            quality: {
              usable_evidence_ids: ["E101"],
              report_gate: { citation_coverage: 1 },
              report_validation: { status: "passed", errors: [] },
            },
            datasets: {
              evidence: {
                items: [{ evidence_id: "E101", source_key: "official", published_at: "2026-07-10", quality_score: 0.95 }],
              },
            },
          },
          artifacts: [
            { artifact_id: "artifact_report", artifact_type: "stock_deep_dive_report", title: "报告", mime_type: "text/markdown" },
            { artifact_id: "artifact_packet", artifact_type: "stock_research_packet_v2", title: "Packet", mime_type: "application/json" },
          ],
        };
      },
    },
  });
  engine.currentTaskType = "stock_deep_analysis";
  engine.context.currentTaskType = "stock_deep_analysis";
  engine.context.data.currentTicker = "300308.SZ";

  const result = await engine.executeFlow(["run_governed_stock_deep_dive"]);

  assert.deepEqual(calls, [{ ticker: "300308.SZ", acquisitionMode: "refresh_if_stale" }]);
  assert.equal(result.status, "completed");
  assert.equal(result.response.startsWith("# 个股深度研究 V2"), true);
  assert.equal(result.data.llmAnalysis, undefined);
  assert.equal(result.data.governedWorkflow.run_id, "run_v2_fixture");
  assert.equal(result.data.citationValidation.status, "passed");
  assert.equal(result.data.citationValidation.coverage, 1);
  assert.deepEqual(result.extractedMemories, []);
});

test("governed workflow failure never falls back to the legacy stock report", async () => {
  const engine = new WorkflowEngine({
    governedWorkflowRunner: {
      async runStockDeepDive() {
        throw new Error("quality gate rejected the report");
      },
    },
  });
  engine.currentTaskType = "stock_deep_analysis";
  engine.context.currentTaskType = "stock_deep_analysis";
  engine.context.data.currentTicker = "300308.SZ";

  const result = await engine.executeFlow(["run_governed_stock_deep_dive"]);

  assert.equal(result.status, "failed");
  assert.match(result.response, /个股深度研究 V3 执行失败/);
  assert.match(result.response, /不使用旧研究逻辑/);
  assert.doesNotMatch(result.response, /可审计研究摘要/);
  assert.equal(result.data.reportQualityGate.passed, false);
});

test("governed runner queues Python workflow and restores report plus packet artifacts", async () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "smr-governed-chat-"));
  const runDirectory = path.join(root, "run_child_fixture");
  fs.mkdirSync(runDirectory, { recursive: true });
  fs.writeFileSync(path.join(runDirectory, "stock_deep_dive.md"), "# 个股深度研究 V2\n", "utf8");
  fs.writeFileSync(path.join(runDirectory, "research_packet.json"), JSON.stringify({
    schema_version: "2.0",
    quality: {
      usable_evidence_ids: [],
      report_gate: { report_status: "cannot_conclude", citation_coverage: null },
      report_validation: { status: "passed", errors: [] },
    },
    datasets: { evidence: { items: [] } },
  }), "utf8");

  let startedRunId = null;
  const repository = {
    createQueuedRun({ runId, workflowId, input }) {
      assert.equal(workflowId, "stock_deep_dive");
      assert.deepEqual(input, {
        ticker: "300308.SZ",
        allow_network: true,
        acquisition_mode: "refresh_if_stale",
      });
      return { reused: false, run: { run_id: runId, status: "queued" } };
    },
    getRun(runId) {
      return {
        run_id: runId,
        workflow_id: "stock_deep_dive",
        status: startedRunId ? "completed" : "queued",
        summary: { conclusion_status: "cannot_conclude", research_readiness: "cannot_conclude" },
      };
    },
    listArtifacts(runId) {
      return [
        {
          artifact_id: "artifact_report",
          run_id: runId,
          artifact_type: "stock_deep_dive_report",
          relative_path: `${runId}/stock_deep_dive.md`,
          mime_type: "text/markdown",
          metadata: { artifact_root_index: 0 },
        },
        {
          artifact_id: "artifact_packet",
          run_id: runId,
          artifact_type: "stock_research_packet_v2",
          relative_path: `${runId}/research_packet.json`,
          mime_type: "application/json",
          metadata: { artifact_root_index: 0 },
        },
      ];
    },
    listEvents() { return []; },
  };
  const runner = new GovernedWorkflowRunner({
    repository,
    processService: { startExistingRun(runId) { startedRunId = runId; } },
    artifactRoots: [root],
    pollIntervalMs: 1,
    timeoutMs: 1_000,
    runIdFactory: () => "run_child_fixture",
  });

  const progressSnapshots = [];
  const result = await runner.runStockDeepDive({
    ticker: "300308.SZ",
    onProgress(progress) {
      progressSnapshots.push(progress);
    },
  });

  assert.equal(startedRunId, "run_child_fixture");
  assert.equal(result.status, "completed");
  assert.equal(result.report, "# 个股深度研究 V2\n");
  assert.equal(result.packet.schema_version, "2.0");
  assert.equal(result.artifacts.length, 2);
  assert.equal(progressSnapshots.length >= 2, true);
  assert.equal(progressSnapshots[0].run_id, "run_child_fixture");
  assert.equal(progressSnapshots[0].researchExecution.totalStages, 30);
  assert.equal(progressSnapshots[0].researchExecution.completedStages, 0);
});
