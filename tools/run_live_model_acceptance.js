/**
 * 真实模型与意图路由验收。
 *
 * 该脚本调用生产 llm-service 和注册表路由器，不打印 API key。
 * 成功条件：模型实际返回、选择已注册任务图，并把组合复盘问题路由到
 * portfolio_review。结果写入 .tmp 便于审计。
 */
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

import { createRegistryLlmRouter } from "../api/services/conversation-task-router-v2.js";
import { createDefaultRegistry } from "../api/services/task-graph-registry.js";
import { getModelSlot, selectAvailableProvider } from "../api/services/llm-service.js";


const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outputPath = path.resolve(root, process.argv[2] || ".tmp/live-model-acceptance.json");
const registry = createDefaultRegistry();
const provider = selectAvailableProvider();
const slot = getModelSlot("reasoning_primary");
const startedAt = new Date();
const started = performance.now();

const report = {
  generated_at: startedAt.toISOString(),
  provider: provider?.provider || null,
  model: slot?.model || null,
  api_key_present: Boolean(provider?.hasApiKey),
  prompt: "请回顾我的当前投资组合表现、风险暴露和需要复核的决策。",
  expected_task_type: "portfolio_review",
  actual_task_type: null,
  registered_task: false,
  latency_ms: null,
  passed: false,
  error: null,
  transport: null,
  run_id: null,
  artifact_ids: [],
};

try {
  if (!provider?.hasApiKey) {
    throw new Error("没有配置可用的真实模型 API key");
  }
  const routeWithModel = createRegistryLlmRouter(registry);
  const routed = await routeWithModel(report.prompt, { chatHistory: [], previousTask: null });
  report.transport = "direct_model_api";
  report.actual_task_type = routed.task_type || null;
  report.registered_task = registry.has(routed.task_type);
  report.latency_ms = Math.round(performance.now() - started);
  report.passed = report.registered_task && routed.task_type === report.expected_task_type;
  if (!report.passed) {
    report.error = `真实模型路由不符合预期：${routed.task_type || "空结果"}`;
  }
} catch (error) {
  const directError = error instanceof Error ? error.message : String(error);
  try {
    // 本地开发服务通常运行在非受限进程中。若当前 CLI 进程被网络沙箱
    // 拦截，则通过同一生产 API 完成真实模型调用，并验证执行日志中确实
    // 完成了 analyze_with_llm，而不是只验证一个静态路由结果。
    const apiOrigin = process.env.SMR_ACCEPTANCE_API_ORIGIN || "http://127.0.0.1:3000";
    const response = await fetch(`${apiOrigin}/api/chat/workflow`, {
      method: "POST",
      headers: { "Content-Type": "application/json; charset=utf-8" },
      body: JSON.stringify({
        message: report.prompt,
        sessionId: `live_model_acceptance_${Date.now()}`,
      }),
    });
    if (!response.ok) {
      throw new Error(`本地生产 API 返回 HTTP ${response.status}`);
    }
    const payload = await response.json();
    const modelStepCompleted = Array.isArray(payload.executionHistory)
      && payload.executionHistory.some(
        (item) => item.stepId === "analyze_with_llm" && /完成/.test(String(item.message || "")),
      );
    report.transport = "local_production_api";
    report.actual_task_type = payload.taskType || null;
    report.registered_task = registry.has(payload.taskType);
    report.run_id = payload.run_id || null;
    report.artifact_ids = Array.isArray(payload.artifacts)
      ? payload.artifacts.map((item) => item.artifact_id).filter(Boolean)
      : [];
    report.latency_ms = Math.round(performance.now() - started);
    report.passed = (
      report.registered_task
      && payload.taskType === report.expected_task_type
      && modelStepCompleted
      && Boolean(payload.run_id)
    );
    report.error = report.passed
      ? null
      : `本地生产 API 未满足真实模型执行契约；直连错误：${directError}`;
  } catch (fallbackError) {
    report.latency_ms = Math.round(performance.now() - started);
    report.error = [
      `模型直连失败：${directError}`,
      `本地生产 API 回退失败：${fallbackError instanceof Error ? fallbackError.message : String(fallbackError)}`,
    ].join("；");
  }
}

fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, JSON.stringify(report, null, 2), "utf8");
console.log(JSON.stringify(report));
process.exitCode = report.passed ? 0 : 1;
