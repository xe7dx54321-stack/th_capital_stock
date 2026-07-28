import crypto from "node:crypto";
import fs from "node:fs";

import { resolveArtifactPath } from "../routes/artifacts.js";
import { buildResearchExecutionSummary } from "./research-execution-summary.js";


const TERMINAL_STATUSES = new Set(["completed", "failed", "cancelled", "waiting_review"]);
const TICKER_PATTERN = /^(?:\d{6}\.(?:SZ|SH|BJ)|\d{5}\.HK|[A-Z][A-Z0-9.-]{0,9})$/;
const ACQUISITION_MODES = new Set(["cache_only", "refresh_if_stale", "force_refresh"]);
const GENERIC_WORKFLOW_IDS = new Set([
  "daily_brief",
  "portfolio_review",
  "thesis_update",
  "operating_driver_valuation",
  "pair_switch_decision",
  "theme_expectation_gap",
  "industry_causal_explainer",
  "company_signal_plan",
  "claim_correction",
]);
export const DEFAULT_GOVERNED_WORKFLOW_TIMEOUT_MS = 10 * 60_000;

function sleep(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

function requestHash(workflowId, input) {
  return crypto.createHash("sha256").update(JSON.stringify({ workflow_id: workflowId, input })).digest("hex");
}

function readArtifact(artifact, roots, expectedMimeType) {
  if (!artifact || artifact.mime_type !== expectedMimeType) {
    throw new Error(`Governed workflow artifact is missing or has the wrong MIME type: ${expectedMimeType}`);
  }
  const artifactPath = resolveArtifactPath(artifact, roots);
  if (!artifactPath || !fs.existsSync(artifactPath)) {
    throw new Error(`Governed workflow artifact file not found: ${artifact?.artifact_id || "unknown"}`);
  }
  return fs.readFileSync(artifactPath, "utf8");
}

export class GovernedWorkflowRunner {
  constructor({
    repository,
    processService,
    artifactRoots,
    pollIntervalMs = 100,
    timeoutMs = DEFAULT_GOVERNED_WORKFLOW_TIMEOUT_MS,
    runIdFactory = () => `run_${crypto.randomUUID().replaceAll("-", "")}`,
    researchSynthesisService = null,
    now = () => Date.now(),
    sleepFn = sleep,
  }) {
    if (!repository) throw new TypeError("GovernedWorkflowRunner requires repository");
    if (!processService) throw new TypeError("GovernedWorkflowRunner requires processService");
    if (!Array.isArray(artifactRoots) || artifactRoots.length === 0) {
      throw new TypeError("GovernedWorkflowRunner requires artifactRoots");
    }
    this.repository = repository;
    this.processService = processService;
    this.artifactRoots = artifactRoots;
    this.pollIntervalMs = Math.max(1, Number(pollIntervalMs) || 100);
    this.timeoutMs = Math.max(
      this.pollIntervalMs,
      Number(timeoutMs) || DEFAULT_GOVERNED_WORKFLOW_TIMEOUT_MS,
    );
    this.runIdFactory = runIdFactory;
    this.researchSynthesisService = researchSynthesisService;
    this.now = typeof now === "function" ? now : () => Date.now();
    this.sleep = typeof sleepFn === "function" ? sleepFn : sleep;
  }

  async waitForTerminalRun(runId, { onPoll = null } = {}) {
    const deadline = this.now() + this.timeoutMs;
    while (true) {
      const run = this.repository.getRun(runId);
      if (!run) throw new Error(`Governed workflow run disappeared: ${runId}`);
      if (typeof onPoll === "function") await onPoll(run);
      if (TERMINAL_STATUSES.has(run.status)) return run;
      const remainingMs = deadline - this.now();
      if (remainingMs <= 0) break;
      await this.sleep(Math.min(this.pollIntervalMs, remainingMs));
    }
    // 截止点再读一次，避免任务恰好在最后一次 sleep 期间完成却被误判为超时。
    const finalRun = this.repository.getRun(runId);
    if (!finalRun) throw new Error(`Governed workflow run disappeared: ${runId}`);
    if (typeof onPoll === "function") await onPoll(finalRun);
    if (TERMINAL_STATUSES.has(finalRun.status)) return finalRun;
    const events = this.repository.listEvents(runId);
    const lastStageEvent = [...events].reverse().find((event) => event.stage_id);
    const stageHint = lastStageEvent?.stage_id ? `; last_stage=${lastStageEvent.stage_id}` : "";
    throw new Error(
      `Governed workflow timed out after ${this.timeoutMs}ms: ${runId}; status=${finalRun.status}${stageHint}`,
    );
  }

  async runWorkflow({ workflowId, input = {} } = {}) {
    const normalizedWorkflowId = String(workflowId || "").trim();
    if (!GENERIC_WORKFLOW_IDS.has(normalizedWorkflowId)) {
      throw new TypeError(`Unsupported governed workflow: ${normalizedWorkflowId || "missing"}`);
    }
    if (!input || typeof input !== "object" || Array.isArray(input)) {
      throw new TypeError("Governed workflow input must be an object");
    }
    const runId = this.runIdFactory();
    const created = this.repository.createQueuedRun({
      runId,
      workflowId: normalizedWorkflowId,
      input,
      idempotencyKey: null,
      requestHash: requestHash(normalizedWorkflowId, input),
    });
    if (!created.reused) this.processService.startExistingRun(created.run.run_id);
    const run = await this.waitForTerminalRun(created.run.run_id);
    if (!["completed", "waiting_review"].includes(run.status)) {
      throw new Error(`Governed ${normalizedWorkflowId} ${run.status}: ${run.error_message || run.run_id}`);
    }
    const artifacts = this.repository.listArtifacts(run.run_id);
    const events = this.repository.listEvents(run.run_id);
    const primaryArtifact = artifacts.find((item) => item.mime_type === "text/markdown")
      || artifacts.find((item) => item.mime_type === "application/json")
      || null;
    let primaryArtifactContent = null;
    if (primaryArtifact) {
      const artifactPath = resolveArtifactPath(primaryArtifact, this.artifactRoots);
      if (artifactPath && fs.existsSync(artifactPath)) {
        primaryArtifactContent = fs.readFileSync(artifactPath, "utf8");
      }
    }
    return {
      ...run,
      artifacts,
      events,
      primaryArtifact,
      primaryArtifactContent,
      researchExecution: buildResearchExecutionSummary(events),
    };
  }

  async runStockDeepDive({ ticker, acquisitionMode = null, allowNetwork, onProgress = null } = {}) {
    const normalizedTicker = String(ticker || "").trim().toUpperCase();
    if (!TICKER_PATTERN.test(normalizedTicker)) throw new TypeError("invalid ticker");
    const mode = acquisitionMode || (allowNetwork === false ? "cache_only" : "refresh_if_stale");
    if (!ACQUISITION_MODES.has(mode)) {
      throw new TypeError("invalid acquisitionMode");
    }
    const workflowId = "stock_deep_dive";
    const input = {
      ticker: normalizedTicker,
      allow_network: mode !== "cache_only",
      acquisition_mode: mode,
    };
    const runId = this.runIdFactory();
    const created = this.repository.createQueuedRun({
      runId,
      workflowId,
      input,
      idempotencyKey: null,
      requestHash: requestHash(workflowId, input),
    });
    let lastProgressFingerprint = null;
    let progressEnabled = typeof onProgress === "function";
    const publishProgress = async (knownRun = null) => {
      if (!progressEnabled) return;
      const currentRun = knownRun || this.repository.getRun(created.run.run_id) || created.run;
      const currentEvents = this.repository.listEvents(created.run.run_id);
      const researchExecution = buildResearchExecutionSummary(currentEvents);
      const lastSequence = currentEvents.at(-1)?.sequence || 0;
      const fingerprint = JSON.stringify({
        runStatus: currentRun?.status || "queued",
        lastSequence,
        researchExecution,
      });
      if (fingerprint === lastProgressFingerprint) return;
      lastProgressFingerprint = fingerprint;
      try {
        await onProgress({
          run_id: created.run.run_id,
          workflow_id: workflowId,
          status: researchExecution.status,
          run_status: currentRun?.status || "queued",
          last_sequence: lastSequence,
          researchExecution,
        });
      } catch (error) {
        progressEnabled = false;
        console.warn("研究进度订阅已断开，后台任务继续运行:", error.message);
      }
    };
    await publishProgress(created.run);
    if (!created.reused) this.processService.startExistingRun(created.run.run_id);
    const run = await this.waitForTerminalRun(created.run.run_id, { onPoll: publishProgress });
    if (run.status !== "completed") {
      await publishProgress(run);
      throw new Error(`Governed stock deep dive ${run.status}: ${run.error_message || run.run_id}`);
    }

    const artifacts = this.repository.listArtifacts(run.run_id);
    const reportArtifact = artifacts.find((item) => item.artifact_type === "stock_deep_dive_report");
    const packetArtifact = artifacts.find((item) => item.artifact_type === "stock_research_packet_v2");
    const auditArtifact = artifacts.find((item) => item.artifact_type === "stock_deep_dive_audit");
    let report = readArtifact(reportArtifact, this.artifactRoots, "text/markdown");
    const packet = JSON.parse(readArtifact(packetArtifact, this.artifactRoots, "application/json"));
    if (packet.schema_version !== "2.0") {
      throw new Error(`Unsupported Research Packet schema: ${packet.schema_version || "missing"}`);
    }
    if (packet.quality?.report_validation?.status !== "passed") {
      throw new Error("Governed stock report did not pass final validation");
    }
    let synthesis = null;
    if (this.researchSynthesisService && packet.workflow_version === "3.0") {
      this.repository.appendEvent(run.run_id, {
        eventType: "stage.started", stageId: "report_synthesis", message: "开始模型综合完整研究报告",
      });
      await publishProgress(run);
      try {
        synthesis = await this.researchSynthesisService.synthesize({ packet, governedDraft: report });
        report = synthesis.report;
        const modelSynthesized = String(synthesis.mode || "").startsWith("model_");
        this.repository.appendEvent(run.run_id, {
          eventType: modelSynthesized ? "stage.completed" : "stage.warning",
          stageId: "report_synthesis",
          level: modelSynthesized ? "info" : "warning",
          message: modelSynthesized ? "模型已完成报告综合" : "模型综合降级，采用已通过校验的受治理初稿",
          payload: { mode: synthesis.mode, attempts: synthesis.attempts, error: synthesis.error || null },
        });
        await publishProgress(run);
        this.repository.appendEvent(run.run_id, {
          eventType: "stage.started", stageId: "final_report_review", message: "开始复核最终报告",
        });
        await publishProgress(run);
        const finalPassed = synthesis.validation?.status === "passed";
        this.repository.appendEvent(run.run_id, {
          eventType: finalPassed ? "stage.completed" : "stage.failed",
          stageId: "final_report_review",
          level: finalPassed ? "info" : "error",
          message: finalPassed ? "最终报告结构、事实与引用复核通过" : "最终报告复核未通过",
          payload: synthesis.validation || {},
        });
        await publishProgress(run);
        if (!finalPassed) throw new Error("Synthesized stock report did not pass final validation");
        packet.research_v3 ||= {};
        packet.research_v3.report_quality ||= {};
        packet.research_v3.report_quality.synthesis = {
          mode: synthesis.mode,
          attempts: synthesis.attempts,
          validation: synthesis.validation,
          model_validation: synthesis.model_validation || null,
          error: synthesis.error || null,
        };
        this.repository.appendEvent(run.run_id, {
          eventType: "stage.started", stageId: "persist_final_report", message: "开始归档最终报告",
        });
        await publishProgress(run);
        const reportPath = resolveArtifactPath(reportArtifact, this.artifactRoots);
        const packetPath = resolveArtifactPath(packetArtifact, this.artifactRoots);
        fs.writeFileSync(reportPath, report, "utf8");
        fs.writeFileSync(packetPath, JSON.stringify(packet, null, 2), "utf8");
        if (auditArtifact) {
          const auditPath = resolveArtifactPath(auditArtifact, this.artifactRoots);
          const audit = JSON.parse(readArtifact(auditArtifact, this.artifactRoots, "application/json"));
          audit.model_synthesis = packet.research_v3.report_quality.synthesis;
          audit.report_validation = synthesis.validation;
          fs.writeFileSync(auditPath, JSON.stringify(audit, null, 2), "utf8");
        }
        this.repository.appendEvent(run.run_id, {
          eventType: "stage.completed", stageId: "persist_final_report", message: "最终报告与质量结果已归档",
        });
        await publishProgress(run);
      } catch (error) {
        const currentEvents = this.repository.listEvents(run.run_id);
        const synthesisTerminal = currentEvents.some((event) => event.stage_id === "report_synthesis" && event.event_type !== "stage.started");
        if (!synthesisTerminal) {
          this.repository.appendEvent(run.run_id, {
            eventType: "stage.failed", stageId: "report_synthesis", level: "error",
            message: error instanceof Error ? error.message : String(error),
          });
          await publishProgress(run);
        }
        throw error;
      }
    }
    const events = this.repository.listEvents(run.run_id);
    await publishProgress(run);
    return {
      ...run,
      report,
      packet,
      artifacts,
      synthesis,
      events,
      researchExecution: buildResearchExecutionSummary(events),
    };
  }
}
