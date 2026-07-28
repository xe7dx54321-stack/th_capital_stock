import { afterEach, describe, expect, it, vi } from "vitest";

import { sendChatRequestStream } from "../ChatPanel";


describe("sendChatRequestStream", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("delivers research progress before resolving the final workflow response", async () => {
    const progress = {
      run_id: "run_research_stream",
      workflow_id: "stock_deep_dive",
      status: "running",
      run_status: "running",
      last_sequence: 4,
      researchExecution: {
        status: "running",
        completedStages: 1,
        totalStages: 30,
        warningStages: 0,
        failedStages: 0,
        groups: [{
          id: "preparation",
          label: "研究准备",
          completedStages: 1,
          totalStages: 4,
          stages: [{
            id: "validate_input",
            label: "校验研究标的",
            status: "completed",
            message: "已完成",
          }],
        }],
      },
    };
    const result = {
      run_id: "run_agent_stream",
      governed_run_id: "run_research_stream",
      taskType: "stock_deep_analysis",
      status: "completed",
      response: "# 个股深度研究 V3",
      data: { researchExecution: progress.researchExecution },
      executionHistory: [],
      workflowSummary: { totalSteps: 2, completedSteps: 2 },
      artifacts: [],
    };
    const streamBody = [
      "event: connected\ndata: {\"status\":\"connected\"}\n\n",
      `event: research_progress\ndata: ${JSON.stringify(progress)}\n\n`,
      `event: result\ndata: ${JSON.stringify(result)}\n\n`,
    ].join("");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(streamBody, {
      status: 200,
      headers: { "Content-Type": "text/event-stream; charset=utf-8" },
    }));

    const received: unknown[] = [];
    const final = await sendChatRequestStream(
      "请深度分析中际旭创",
      "session-stream",
      [],
      (snapshot) => received.push(snapshot),
    );

    expect(received).toHaveLength(1);
    const firstProgress = received[0] as typeof progress;
    expect(firstProgress.researchExecution.totalStages).toBe(30);
    expect(firstProgress.researchExecution.completedStages).toBe(1);
    expect(final.response).toBe("# 个股深度研究 V3");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/chat/workflow/stream",
      expect.objectContaining({ method: "POST" }),
    );
  });
});
