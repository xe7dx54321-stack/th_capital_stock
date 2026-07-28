import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ResearchWorkbench from "../../../app/ResearchWorkbench";
import * as api from "../../../lib/api";

vi.mock("../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../lib/api")>("../../../lib/api");
  return {
    ...actual,
    fetchWorkflowRuns: vi.fn(),
    fetchSessions: vi.fn(),
    fetchSessionMessages: vi.fn(),
    createSession: vi.fn(),
    deleteSession: vi.fn(),
    updateSession: vi.fn(),
  };
});

const session = {
  id: "session-test",
  title: "新对话",
  status: "active" as const,
  is_pinned: 0,
  pinned_at: null,
  message_count: 0,
  last_message_at: null,
  created_at: "2026-07-19T01:00:00Z",
  updated_at: "2026-07-19T01:00:00Z",
};

describe("ResearchWorkbench", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    Element.prototype.scrollIntoView = vi.fn();

    vi.mocked(api.fetchWorkflowRuns).mockResolvedValue({
      runs: [
        { run_id: "run-1", workflow_id: "daily_brief", status: "completed", input: {}, summary: {}, created_at: "2026-07-19T01:00:00Z", artifacts: [] },
        { run_id: "run-2", workflow_id: "stock_deep_dive", status: "waiting_review", input: {}, summary: {}, created_at: "2026-07-19T02:00:00Z", artifacts: [] },
      ],
    });
    vi.mocked(api.fetchSessions).mockResolvedValue({ success: true, sessions: [] });
    vi.mocked(api.fetchSessionMessages).mockResolvedValue({ success: true, messages: [] });
    vi.mocked(api.createSession).mockResolvedValue({ success: true, session });
    vi.mocked(api.deleteSession).mockResolvedValue({ success: true, deleted: true });
  });

  it("renders the current chat workbench and audited run summary", async () => {
    render(<MemoryRouter><ResearchWorkbench /></MemoryRouter>);

    expect(await screen.findByText("今天想分析点什么？")).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "研究概览" })).toHaveTextContent("研究总数2");
    expect(screen.getByRole("region", { name: "研究概览" })).toHaveTextContent("待审核1");
    expect(screen.getByRole("region", { name: "研究概览" })).toHaveTextContent("已完成1");
  });

  it("creates a session and sends a workflow chat request", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({
      run_id: "run_agent_fixture",
      taskType: "opportunity_scan",
      status: "completed",
      response: "已生成带证据的机会扫描。",
      data: {
        dataHealth: {
          status: "warning",
          can_claim_current: true,
          total_evidence: 3,
          fresh_current_evidence: 2,
        },
        citationValidation: {
          status: "passed",
          coverage: 1,
          unknown_citation_ids: [],
          missing_citation_claims: [],
          current_claim_violations: [],
        },
      },
      executionHistory: [],
      workflowSummary: { totalSteps: 3, completedSteps: 3 },
    }), { status: 200, headers: { "Content-Type": "application/json" } }));

    render(<MemoryRouter><ResearchWorkbench /></MemoryRouter>);
    const input = await screen.findByPlaceholderText("输入你的问题，例如：帮我分析中际旭创...");
    fireEvent.change(input, { target: { value: "扫描今天的投资机会" } });
    fireEvent.keyDown(input, { key: "Enter", code: "Enter" });

    expect(await screen.findByText("已生成带证据的机会扫描。")).toBeInTheDocument();
    expect(screen.getAllByText("机会扫描").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/run_agent_fixture/)).toBeInTheDocument();
    expect(screen.getByText("部分数据受限")).toBeInTheDocument();
    expect(screen.getByText("引用与结构通过")).toBeInTheDocument();
    expect(api.createSession).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith("/api/chat/workflow/stream", expect.objectContaining({ method: "POST" })));
    const request = JSON.parse(String(fetchMock.mock.calls[0][1]?.body));
    expect(request).toMatchObject({ message: "扫描今天的投资机会", sessionId: "session-test" });
  });

  it("keeps workflow request failures visible and actionable", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("unavailable", { status: 503 }));

    render(<MemoryRouter><ResearchWorkbench /></MemoryRouter>);
    const input = await screen.findByPlaceholderText("输入你的问题，例如：帮我分析中际旭创...");
    fireEvent.change(input, { target: { value: "分析 300308.SZ" } });
    fireEvent.keyDown(input, { key: "Enter", code: "Enter" });

    expect(await screen.findByText("抱歉，发生了错误：聊天服务请求失败")).toBeInTheDocument();
  });

  it("shows governed V3 stages separately from the two-step chat orchestration", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({
      run_id: "run_agent_v3",
      governed_run_id: "run_research_v3",
      taskType: "stock_deep_analysis",
      status: "completed",
      response: "# 个股深度研究 V3\n\n正文",
      data: {
        dataHealth: { status: "healthy", can_claim_current: true, total_evidence: 12, fresh_current_evidence: 8 },
        citationValidation: { status: "passed", coverage: 1, unknown_citation_ids: [], missing_citation_claims: [], current_claim_violations: [] },
        researchExecution: {
          status: "completed", completedStages: 3, totalStages: 3, warningStages: 0, failedStages: 0,
          groups: [{
            id: "preparation", label: "研究准备", completedStages: 3, totalStages: 3,
            stages: [
              { id: "validate_input", label: "校验研究标的", status: "completed", message: "完成" },
              { id: "build_research_plan", label: "生成研究计划与章节矩阵", status: "completed", message: "完成" },
              { id: "check_provider_health", label: "检查数据源健康状态", status: "completed", message: "完成" },
            ],
          }],
        },
      },
      executionHistory: [],
      workflowSummary: { totalSteps: 2, completedSteps: 2 },
      artifacts: [],
    }), { status: 200, headers: { "Content-Type": "application/json" } }));

    render(<MemoryRouter><ResearchWorkbench /></MemoryRouter>);
    const input = await screen.findByPlaceholderText("输入你的问题，例如：帮我分析中际旭创...");
    fireEvent.change(input, { target: { value: "请深度分析中际旭创" } });
    fireEvent.keyDown(input, { key: "Enter", code: "Enter" });

    expect((await screen.findAllByText("3/3 阶段完成")).length).toBeGreaterThanOrEqual(1);
    fireEvent.click(screen.getByText("研究运行与产物"));
    expect(screen.getByText("研究主流程")).toBeInTheDocument();
    expect(screen.getByText("研究准备")).toBeInTheDocument();
    expect(screen.getByText("生成研究计划与章节矩阵")).toBeInTheDocument();
    expect(screen.getByText("2/2 步完成")).toBeInTheDocument();
  });
});
