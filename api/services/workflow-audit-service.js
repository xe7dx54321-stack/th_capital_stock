import crypto from "crypto";
import fs from "fs";
import path from "path";


function summarizeData(value) {
  if (value === null || value === undefined) return {};
  if (Array.isArray(value)) return { kind: "array", count: value.length };
  if (typeof value !== "object") return { value: String(value).slice(0, 500) };

  const scalarFields = {};
  for (const [key, item] of Object.entries(value)) {
    if (["string", "number", "boolean"].includes(typeof item)) {
      scalarFields[key] = typeof item === "string" ? item.slice(0, 300) : item;
    }
    if (Object.keys(scalarFields).length >= 8) break;
  }
  return {
    kind: "object",
    keys: Object.keys(value).slice(0, 30),
    fields: scalarFields,
  };
}

function eventShape(entry) {
  const message = String(entry.message || "");
  if (message.startsWith("✓")) return { eventType: "stage.completed", level: "info" };
  if (message.startsWith("✗")) return { eventType: "stage.failed", level: "error" };
  if (message.startsWith("⚠") || message.includes("已跳过")) return { eventType: "stage.warning", level: "warning" };
  if (message.startsWith("正在执行")) return { eventType: "stage.started", level: "info" };
  return { eventType: "stage.progress", level: "info" };
}

function renderEvidenceSection(result) {
  const health = result.data?.dataHealth;
  const catalog = result.data?.evidenceCatalog || [];
  const citation = result.data?.citationValidation;
  if (!health && catalog.length === 0 && !citation) return "";
  const statusLabel = health?.status === "healthy" ? "健康" : health?.status === "warning" ? "需注意" : "不足";
  const lines = catalog.map((item) => {
    const linkText = item.source_urls?.length ? `；来源链接：${item.source_urls.join("、")}` : "";
    return `- [${item.evidence_id}] ${item.source_name}；截至：${item.as_of || "未知"}；新鲜度：${item.freshness}；条目：${item.item_count}${linkText}`;
  });
  const citationLabel = citation?.status === "passed" ? "通过" : citation?.status === "warning" ? "需复核" : "不适用";
  const citationSection = citation ? `

## 引用校验

- 校验状态：${citationLabel}
- 时效性陈述引用覆盖率：${Math.round((citation.coverage || 0) * 100)}%
- 未知证据编号：${citation.unknown_citation_ids?.join("、") || "无"}
- 缺少引用的陈述：${citation.missing_citation_claims?.length || 0}
- 违反当期数据门禁的陈述：${citation.current_claim_violations?.length || 0}` : "";
  return `

## 数据健康

- 综合状态：${statusLabel}
- 可否支撑“当前/今日”判断：${health?.can_claim_current ? "可以" : "不可以"}
- 新鲜当期证据：${health?.fresh_current_evidence || 0}
- 证据总数：${health?.total_evidence || catalog.length}

## 证据目录

${lines.length > 0 ? lines.join("\n") : "- 无可用证据"}${citationSection}`;
}

function renderMarkdown({ runId, message, result }) {
  const summary = result.workflowSummary || {};
  const evidenceSection = renderEvidenceSection(result);
  return `# Agent 投研任务产物

- 任务编号：${runId}
- 任务类型：${result.taskType || "chat"}
- 执行状态：${result.status || "unknown"}
- 生成时间：${new Date().toISOString()}
- 执行步骤：${summary.completedSteps || 0}/${summary.totalSteps || 0}
- 失败步骤：${summary.failedSteps || 0}
- 跳过步骤：${summary.skippedSteps || 0}

## 用户问题

${message}
${evidenceSection}

## 研究结果

${result.response || "未生成研究结果。"}
`;
}

function writeAtomicFile(targetPath, content) {
  const temporaryPath = `${targetPath}.tmp`;
  fs.writeFileSync(temporaryPath, content, "utf8");
  fs.renameSync(temporaryPath, targetPath);
}

export class WorkflowAuditService {
  constructor({ repository, artifactRoot, artifactRootIndex = 0 }) {
    if (!repository) throw new TypeError("WorkflowAuditService requires repository");
    if (!artifactRoot) throw new TypeError("WorkflowAuditService requires artifactRoot");
    this.repository = repository;
    this.artifactRoot = path.resolve(artifactRoot);
    this.artifactRootIndex = artifactRootIndex;
  }

  startChatRun({ message, sessionId = null, chatHistoryCount = 0 }) {
    const runId = `run_agent_${crypto.randomUUID().replaceAll("-", "")}`;
    this.repository.createInlineRun({
      runId,
      workflowId: "agent_chat",
      input: {
        message: String(message).slice(0, 10_000),
        session_id: sessionId,
        chat_history_count: chatHistoryCount,
      },
    });
    return runId;
  }

  recordEngineEvent(runId, entry) {
    const { eventType, level } = eventShape(entry);
    return this.repository.appendEvent(runId, {
      eventType,
      stageId: entry.stepId || null,
      level,
      message: entry.message || "Workflow progress",
      payload: {
        engine_timestamp: entry.timestamp || null,
        data_summary: summarizeData(entry.data),
      },
    });
  }

  completeChatRun(runId, { message, sessionId = null, result }) {
    const runDirectory = path.join(this.artifactRoot, runId);
    const artifactPath = path.join(runDirectory, "report.md");
    fs.mkdirSync(runDirectory, { recursive: true });
    writeAtomicFile(artifactPath, renderMarkdown({ runId, message, result }));

    const artifactId = `artifact_${crypto.randomUUID().replaceAll("-", "")}`;
    const reportArtifact = this.repository.registerArtifact({
      artifactId,
      runId,
      artifactType: "agent_report",
      title: `${result.taskType || "chat"} 执行审计记录`,
      relativePath: path.relative(this.artifactRoot, artifactPath).split(path.sep).join("/"),
      mimeType: "text/markdown",
      metadata: {
        artifact_root_index: this.artifactRootIndex,
        content_role: "execution_audit",
        execution_status: result.status,
        task_type: result.taskType || "chat",
        data_health_status: result.data?.dataHealth?.status || null,
        evidence_count: result.data?.evidenceCatalog?.length || 0,
        citation_status: result.data?.citationValidation?.status || null,
      },
    });
    const artifacts = [reportArtifact];

    const evidenceSnapshots = result.data?.evidenceSnapshots || [];
    if (evidenceSnapshots.length > 0) {
      const evidencePath = path.join(runDirectory, "evidence.json");
      const evidencePayload = {
        schema_version: 1,
        run_id: runId,
        generated_at: new Date().toISOString(),
        data_health: result.data?.dataHealth || null,
        citation_validation: result.data?.citationValidation || null,
        evidence_catalog: result.data?.evidenceCatalog || [],
        snapshots: evidenceSnapshots,
      };
      writeAtomicFile(evidencePath, `${JSON.stringify(evidencePayload, null, 2)}\n`);
      artifacts.push(this.repository.registerArtifact({
        artifactId: `artifact_${crypto.randomUUID().replaceAll("-", "")}`,
        runId,
        artifactType: "evidence_snapshot",
        title: `${result.taskType || "chat"} 原始证据快照`,
        relativePath: path.relative(this.artifactRoot, evidencePath).split(path.sep).join("/"),
        mimeType: "application/json",
        metadata: {
          artifact_root_index: this.artifactRootIndex,
          evidence_count: evidenceSnapshots.length,
          schema_version: 1,
        },
      }));
    }

    const executionStatus = result.status || "failed";
    const storedStatus = executionStatus === "completed"
      ? "completed"
      : executionStatus === "waiting_review"
        ? "waiting_review"
        : executionStatus === "cancelled"
          ? "cancelled"
          : "failed";
    const usage = result.data?.llmAnalysis?.usage || null;
    if (usage) {
      this.repository.appendEvent(runId, {
        eventType: "model.usage",
        stageId: "analyze_with_llm",
        message: "Recorded model token usage",
        payload: summarizeData(usage),
      });
    }
    const dataHealth = result.data?.dataHealth || null;
    const evidenceCatalog = result.data?.evidenceCatalog || [];
    if (dataHealth) {
      this.repository.appendEvent(runId, {
        eventType: "data.health.checked",
        stageId: "evidence_gate",
        message: `Data health is ${dataHealth.status}`,
        payload: {
          data_health: dataHealth,
          evidence_ids: evidenceCatalog.map((item) => item.evidence_id),
        },
      });
    }
    const citationValidation = result.data?.citationValidation || null;
    if (citationValidation && citationValidation.status !== "not_applicable") {
      this.repository.appendEvent(runId, {
        eventType: "report.citations.checked",
        stageId: "citation_validator",
        level: citationValidation.status === "passed" ? "info" : "warning",
        message: `Citation validation is ${citationValidation.status}`,
        payload: citationValidation,
      });
    }

    const summary = {
      execution_status: executionStatus,
      task_type: result.taskType || "chat",
      workflow_summary: result.workflowSummary || {},
      session_id: sessionId,
      response_characters: String(result.response || "").length,
      model_usage: usage,
      data_health: dataHealth,
      evidence_catalog: evidenceCatalog,
      citation_validation: citationValidation,
      artifact_ids: artifacts.map((item) => item.artifact_id),
      governed_run_id: result.data?.governedWorkflow?.run_id || null,
      governed_artifact_ids: (result.data?.governedWorkflow?.artifacts || []).map((item) => item.artifact_id),
    };
    const terminalEventType = executionStatus === "partial" ? "run.partial" : `run.${storedStatus}`;
    const run = this.repository.finalizeInlineRun(runId, {
      status: storedStatus,
      summary,
      errorCode: executionStatus === "partial" ? "partial_failure" : storedStatus === "failed" ? "workflow_failed" : null,
      errorMessage: executionStatus === "partial" ? "One or more workflow steps failed" : null,
      eventType: terminalEventType,
      eventMessage: `Agent workflow ${executionStatus}`,
      eventLevel: storedStatus === "failed" ? "error" : "info",
      eventPayload: { execution_status: executionStatus, artifact_ids: artifacts.map((item) => item.artifact_id) },
    });
    return { run, artifact: reportArtifact, artifacts };
  }

  failChatRun(runId, error) {
    return this.repository.finalizeInlineRun(runId, {
      status: "failed",
      summary: { execution_status: "failed" },
      errorCode: error?.name || "Error",
      errorMessage: error?.message || String(error),
      eventType: "run.failed",
      eventMessage: error?.message || "Agent workflow failed",
      eventLevel: "error",
      eventPayload: { error_name: error?.name || "Error" },
    });
  }
}

export { eventShape, renderEvidenceSection, renderMarkdown, summarizeData };
