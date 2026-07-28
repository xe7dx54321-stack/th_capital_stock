import assert from "node:assert/strict";
import test from "node:test";

import express from "express";

import { createEnhancedChatRouter } from "../../api/services/chat-enhanced-service.js";
import { buildResearchExecutionSummary } from "../../api/services/research-execution-summary.js";


function listen(app) {
  return new Promise((resolve, reject) => {
    const server = app.listen(0, "127.0.0.1", () => resolve(server));
    server.once("error", reject);
  });
}

function close(server) {
  return new Promise((resolve, reject) => {
    server.close((error) => error ? reject(error) : resolve());
  });
}

test("streaming chat emits real 30-stage progress before the final result", async () => {
  const app = express();
  app.use(express.json());
  app.locals.workflowAuditService = null;
  app.locals.governedWorkflowRunner = {};

  const calls = [];
  app.use(createEnhancedChatRouter({
    repository: null,
    persistChat() {},
    async workflowChatExecutor(options) {
      calls.push(options);
      await options.onResearchProgress({
        run_id: "run_stream_fixture",
        workflow_id: "stock_deep_dive",
        status: "running",
        run_status: "running",
        last_sequence: 2,
        researchExecution: buildResearchExecutionSummary([
          {
            sequence: 1,
            event_type: "stage.started",
            stage_id: "validate_input",
            message: "开始校验",
            created_at: "2026-07-28T00:00:00Z",
          },
          {
            sequence: 2,
            event_type: "stage.completed",
            stage_id: "validate_input",
            message: "校验完成",
            created_at: "2026-07-28T00:00:01Z",
          },
        ]),
      });
      return {
        run_id: "run_agent_fixture",
        governed_run_id: "run_stream_fixture",
        taskType: "stock_deep_analysis",
        status: "completed",
        response: "# 正式研究报告",
        data: { researchExecution: buildResearchExecutionSummary([]) },
        executionHistory: [],
        workflowSummary: { totalSteps: 2, completedSteps: 2 },
        artifacts: [],
      };
    },
  }));

  const server = await listen(app);
  try {
    const address = server.address();
    const response = await fetch(`http://127.0.0.1:${address.port}/api/chat/workflow/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify({ message: "请深度分析中际旭创" }),
    });
    assert.equal(response.status, 200);
    assert.match(response.headers.get("content-type"), /text\/event-stream/);
    const body = await response.text();
    const connectedIndex = body.indexOf("event: connected");
    const progressIndex = body.indexOf("event: research_progress");
    const resultIndex = body.indexOf("event: result");
    assert.equal(connectedIndex >= 0, true);
    assert.equal(progressIndex > connectedIndex, true);
    assert.equal(resultIndex > progressIndex, true);
    assert.match(body, /"totalStages":30/);
    assert.match(body, /"completedStages":1/);
    assert.match(body, /# 正式研究报告/);
    assert.equal(typeof calls[0].onResearchProgress, "function");
  } finally {
    await close(server);
  }
});
