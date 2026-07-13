import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ResearchWorkbench from "../../../app/ResearchWorkbench";
import * as api from "../../../lib/api";

vi.mock("../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../lib/api")>("../../../lib/api");
  return {
    ...actual,
    fetchWorkflows: vi.fn(),
    fetchWorkflowRuns: vi.fn(),
    fetchWorkflowRun: vi.fn(),
    fetchWorkflowEvents: vi.fn(),
    createWorkflowRun: vi.fn(),
    subscribeWorkflowEvents: vi.fn(),
    fetchDecisions: vi.fn(),
  };
});

const workflow = {
  workflow_id: "stock_deep_dive",
  title: "Stock deep dive",
  description: "Build an evidence-backed local company research report.",
  enabled: true,
  input_schema: { type: "object" },
};

const completedRun = {
  run_id: "run_previous",
  workflow_id: "stock_deep_dive",
  status: "completed",
  input: { ticker: "300308.SZ", allow_network: false },
  summary: { conclusion_status: "cannot_conclude", evidence_ids: ["ev-1"] },
  created_at: "2026-07-13T01:00:00Z",
  artifacts: [],
};

describe("ResearchWorkbench", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    vi.mocked(api.fetchWorkflows).mockResolvedValue({ workflows: [workflow] });
    vi.mocked(api.fetchWorkflowRuns).mockResolvedValue({ runs: [completedRun] });
    vi.mocked(api.fetchWorkflowRun).mockResolvedValue(completedRun);
    vi.mocked(api.fetchWorkflowEvents).mockResolvedValue({ events: [] });
    vi.mocked(api.subscribeWorkflowEvents).mockReturnValue(() => undefined);
    vi.mocked(api.fetchDecisions).mockResolvedValue({ decisions: [] });
  });

  it("launches a ticker workflow and renders streamed progress", async () => {
    vi.mocked(api.createWorkflowRun).mockResolvedValue({
      ...completedRun,
      run_id: "run_new",
      status: "queued",
      input: { ticker: "600519.SH", allow_network: false },
    });
    vi.mocked(api.subscribeWorkflowEvents).mockImplementation((_id, _after, onEvent) => {
      onEvent({
        event_id: 1,
        run_id: "run_new",
        sequence: 1,
        event_type: "stage.progress",
        payload: { stage: "evidence", message: "正在核验关键证据" },
        created_at: "2026-07-13T02:00:00Z",
      });
      return () => undefined;
    });

    render(<MemoryRouter><ResearchWorkbench /></MemoryRouter>);
    fireEvent.change(await screen.findByLabelText("研究标的"), { target: { value: "600519.SH" } });
    fireEvent.click(screen.getByRole("button", { name: "开始深挖" }));

    await waitFor(() => expect(api.createWorkflowRun).toHaveBeenCalledWith(
      "stock_deep_dive",
      { ticker: "600519.SH", allow_network: false },
      expect.any(String),
    ));
    expect(await screen.findByText("正在核验关键证据")).toBeInTheDocument();
  });

  it("falls back to event polling when the live stream disconnects", async () => {
    vi.mocked(api.subscribeWorkflowEvents).mockImplementation((_id, _after, _onEvent, onError) => {
      onError();
      return () => undefined;
    });
    vi.mocked(api.fetchWorkflowEvents).mockResolvedValue({
      events: [{
        event_id: 2,
        run_id: "run_previous",
        sequence: 2,
        event_type: "stage.warning",
        payload: { message: "行情时间戳已过期" },
        created_at: "2026-07-13T02:10:00Z",
      }],
    });

    render(<MemoryRouter><ResearchWorkbench /></MemoryRouter>);

    expect(await screen.findByText("轮询恢复")).toBeInTheDocument();
    expect(await screen.findByText("行情时间戳已过期")).toBeInTheDocument();
  });

  it("keeps launch failures visible and actionable", async () => {
    vi.mocked(api.createWorkflowRun).mockRejectedValue(new Error("本地工作进程不可用"));
    render(<MemoryRouter><ResearchWorkbench /></MemoryRouter>);

    fireEvent.change(await screen.findByLabelText("研究标的"), { target: { value: "300308.SZ" } });
    fireEvent.click(screen.getByRole("button", { name: "开始深挖" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("本地工作进程不可用");
  });
});
