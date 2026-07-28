import assert from "node:assert/strict";
import fs from "node:fs";
import { mkdtempSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import Database from "better-sqlite3";

import { WorkflowRepository } from "../../api/repositories/workflow-repository.js";
import { executeAuditedWorkflowChat, formatPersistedAssistantMessage } from "../../api/services/chat-enhanced-service.js";
import { WorkflowAuditService } from "../../api/services/workflow-audit-service.js";


const ROOT = path.resolve(import.meta.dirname, "..", "..");

function createAuditFixture() {
  const root = mkdtempSync(path.join(os.tmpdir(), "smr-audit-"));
  const dbPath = path.join(root, "runtime.db");
  const artifactRoot = path.join(root, "artifacts");
  const db = new Database(dbPath);
  db.exec(fs.readFileSync(path.join(ROOT, "migrations", "0002_workflow_runtime.sql"), "utf8"));
  db.exec(fs.readFileSync(path.join(ROOT, "migrations", "0003_workflow_api.sql"), "utf8"));
  db.close();
  const repository = new WorkflowRepository(dbPath);
  const auditService = new WorkflowAuditService({ repository, artifactRoot });
  return { root, repository, auditService };
}

function partialResult() {
  return {
    taskType: "opportunity_scan",
    status: "partial",
    response: "发现两项机会，但一个新闻源获取失败。",
    data: {
      llmAnalysis: { usage: { input_tokens: 120, output_tokens: 80 } },
      dataHealth: {
        status: "warning", can_claim_current: true, total_evidence: 2,
        fresh_current_evidence: 1, counts: { fresh: 1, stale: 0, missing: 0, undated: 0, fetch_failed: 1 },
      },
      evidenceCatalog: [
        { evidence_id: "E001", source_name: "新浪财经实时行情", source_urls: [], as_of: "2026-07-19T01:00:00.000Z", freshness: "fresh", item_count: 8 },
        { evidence_id: "E002", source_name: "本地新闻库", source_urls: [], as_of: null, freshness: "fetch_failed", item_count: 0 },
      ],
      evidenceSnapshots: [
        { schema_version: 1, evidence_id: "E001", tool_id: "get_market_indices", source_id: "sina_realtime", captured_at: "2026-07-19T01:00:00.000Z", success: true, message: "ok", truncated: false, snapshot_sha256: "a".repeat(64), data: [{ price: 3500 }] },
      ],
      citationValidation: {
        status: "warning", coverage: 0.5, auditable_claim_count: 2, cited_claim_count: 1,
        cited_evidence_ids: ["E001"], unknown_citation_ids: [],
        missing_citation_claims: [{ line_number: 2, text: "新闻源失败 1 个", evidence_ids: [] }],
        current_claim_violations: [],
      },
    },
    executionHistory: [],
    workflowSummary: { totalSteps: 3, completedSteps: 2, failedSteps: 1, skippedSteps: 0 },
  };
}

test("persisted assistant message keeps the report body free of execution metadata", () => {
  const message = formatPersistedAssistantMessage({
    ...partialResult(),
    taskType: "market_attribution",
    run_id: "run_agent_sample",
    governed_run_id: "run_stock_v2_sample",
    artifacts: [
      {
        artifact_id: "artifact_v2_report",
        artifact_type: "stock_deep_dive_report",
        title: "个股深度研究 V2",
        mime_type: "text/markdown",
      },
      {
        artifact_id: "artifact_v2_packet",
        artifact_type: "stock_research_packet_v2",
        title: "Research Packet v2",
        mime_type: "application/json",
      },
    ],
    workflowSummary: { totalSteps: 3, completedSteps: 3 },
    data: {
      dataHealth: { status: "healthy", can_claim_current: true, total_evidence: 3, fresh_current_evidence: 2 },
      citationValidation: { status: "passed", coverage: 1 },
    },
  });

  assert.equal(message, "发现两项机会，但一个新闻源获取失败。");
  assert.doesNotMatch(message, /执行信息|任务编号|权威研究任务|引用校验|artifact_v2/);
});

test("audited governed chat preserves child run and artifacts for API response and reload", async (t) => {
  const { repository, auditService } = createAuditFixture();
  t.after(() => repository.close());
  const governedArtifacts = [
    { artifact_id: "artifact_child_report", artifact_type: "stock_deep_dive_report", title: "V2 报告", mime_type: "text/markdown" },
    { artifact_id: "artifact_child_packet", artifact_type: "stock_research_packet_v2", title: "V2 Packet", mime_type: "application/json" },
  ];

  const result = await executeAuditedWorkflowChat({
    message: "深度分析中际旭创",
    sessionId: "session-governed",
    auditService,
    governedWorkflowRunner: { runStockDeepDive() {} },
    engineFactory: ({ governedWorkflowRunner }) => ({
      context: {},
      async processUserQuery() {
        assert.ok(governedWorkflowRunner);
        return {
          taskType: "stock_deep_analysis",
          status: "completed",
          response: "# 个股深度研究 V2\n",
          data: {
            governedWorkflow: {
              run_id: "run_child_v2",
              artifacts: governedArtifacts,
            },
          },
          executionHistory: [],
          workflowSummary: { totalSteps: 2, completedSteps: 2, failedSteps: 0, skippedSteps: 0 },
          extractedMemories: [],
        };
      },
    }),
  });

  assert.equal(result.governed_run_id, "run_child_v2");
  assert.equal(result.artifacts.length, 3);
  assert.deepEqual(result.artifacts.slice(0, 2), governedArtifacts);
  assert.equal(result.artifacts[2].artifact_type, "agent_report");
  assert.match(result.artifacts[2].title, /执行审计记录/);
  const parent = repository.getRun(result.run_id);
  assert.equal(parent.summary.governed_run_id, "run_child_v2");
  assert.deepEqual(parent.summary.governed_artifact_ids, ["artifact_child_report", "artifact_child_packet"]);
  const restoredMessage = formatPersistedAssistantMessage(result);
  assert.equal(restoredMessage, "# 个股深度研究 V2");
  assert.doesNotMatch(restoredMessage, /run_child_v2|artifact_child_report/);
});

test("audited chat persists run events, model usage and markdown artifact", async (t) => {
  const { repository, auditService } = createAuditFixture();
  t.after(() => repository.close());

  const result = await executeAuditedWorkflowChat({
    message: "扫描今天的机会",
    sessionId: "session-1",
    conversationContext: { chatHistory: [{ role: "user", content: "先看市场" }] },
    auditService,
    engineFactory: ({ onEvent }) => ({
      context: {},
      async processUserQuery() {
        onEvent({ timestamp: new Date().toISOString(), stepId: "get_news", message: "正在执行 [1/3]: 获取新闻...", data: null });
        onEvent({ timestamp: new Date().toISOString(), stepId: "get_news", message: "✓ 获取新闻 完成", data: { count: 8, rows: [{ large: "payload" }] } });
        return partialResult();
      },
    }),
  });

  assert.match(result.run_id, /^run_agent_/);
  assert.equal(result.artifacts.length, 2);
  const run = repository.getRun(result.run_id);
  assert.equal(run.status, "failed");
  assert.equal(run.error_code, "partial_failure");
  assert.equal(run.summary.execution_status, "partial");
  assert.equal(run.summary.session_id, "session-1");
  assert.deepEqual(run.summary.model_usage, { input_tokens: 120, output_tokens: 80 });
  assert.equal(run.summary.data_health.status, "warning");
  assert.deepEqual(run.summary.evidence_catalog.map((item) => item.evidence_id), ["E001", "E002"]);
  assert.equal(run.summary.artifact_ids.length, 2);
  assert.equal(run.summary.citation_validation.status, "warning");

  const events = repository.listEvents(result.run_id);
  assert.deepEqual(events.map((event) => event.event_type), [
    "run.started", "stage.started", "stage.completed", "model.usage", "data.health.checked", "report.citations.checked", "run.partial",
  ]);
  assert.equal(events[2].payload.data_summary.kind, "object");
  assert.deepEqual(events[2].payload.data_summary.keys, ["count", "rows"]);

  const artifact = repository.getArtifact(result.artifacts[0].artifact_id);
  const artifactPath = path.join(auditService.artifactRoot, artifact.relative_path);
  const markdown = fs.readFileSync(artifactPath, "utf8");
  assert.match(markdown, /任务编号：run_agent_/);
  assert.match(markdown, /扫描今天的机会/);
  assert.match(markdown, /一个新闻源获取失败/);
  assert.match(markdown, /## 数据健康/);
  assert.match(markdown, /可否支撑“当前\/今日”判断：可以/);
  assert.match(markdown, /\[E001\] 新浪财经实时行情/);
  assert.match(markdown, /## 引用校验/);
  assert.match(markdown, /时效性陈述引用覆盖率：50%/);
  assert.equal(artifact.metadata.data_health_status, "warning");
  assert.equal(artifact.metadata.evidence_count, 2);
  assert.equal(artifact.metadata.citation_status, "warning");

  const evidenceArtifact = repository.getArtifact(result.artifacts[1].artifact_id);
  assert.equal(evidenceArtifact.artifact_type, "evidence_snapshot");
  const evidencePath = path.join(auditService.artifactRoot, evidenceArtifact.relative_path);
  const evidencePayload = JSON.parse(fs.readFileSync(evidencePath, "utf8"));
  assert.equal(evidencePayload.run_id, result.run_id);
  assert.equal(evidencePayload.snapshots[0].evidence_id, "E001");
  assert.equal(evidencePayload.snapshots[0].data[0].price, 3500);
});

test("failed chat keeps a traceable run id and terminal failure event", async (t) => {
  const { repository, auditService } = createAuditFixture();
  t.after(() => repository.close());

  let thrown;
  try {
    await executeAuditedWorkflowChat({
      message: "触发失败",
      auditService,
      engineFactory: () => ({
        context: {},
        async processUserQuery() { throw new Error("fixture exploded"); },
      }),
    });
  } catch (error) {
    thrown = error;
  }

  assert.ok(thrown);
  assert.match(thrown.runId, /^run_agent_/);
  const run = repository.getRun(thrown.runId);
  assert.equal(run.status, "failed");
  assert.equal(run.error_message, "fixture exploded");
  assert.equal(repository.listEvents(thrown.runId).at(-1).event_type, "run.failed");
});

test("inline agent run does not block a queued governed workflow", (t) => {
  const { repository, auditService } = createAuditFixture();
  t.after(() => repository.close());

  auditService.startChatRun({ message: "agent is running" });
  const governed = repository.createQueuedRun({
    runId: "run_governed_fixture",
    workflowId: "daily_brief",
    input: { allow_network: false },
    idempotencyKey: null,
    requestHash: "fixture-hash",
  });

  assert.equal(governed.reused, false);
  assert.equal(governed.run.status, "queued");
});
