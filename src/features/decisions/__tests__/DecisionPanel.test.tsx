import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import DecisionPanel from "../DecisionPanel";
import * as api from "../../../lib/api";


vi.mock("../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../lib/api")>("../../../lib/api");
  return {
    ...actual,
    fetchDecisions: vi.fn(),
    createDecision: vi.fn(),
    recordDecisionOutcome: vi.fn(),
  };
});

const run = {
  run_id: "run-1",
  workflow_id: "stock_deep_dive",
  status: "completed",
  input: { ticker: "300308.SZ" },
  summary: { evidence_ids: ["ev-1"], claims: [{ text: "订单质量正在改善。" }] },
  created_at: "2026-07-13T00:00:00Z",
};

const decision = {
  decision_id: "decision-1",
  recommendation_id: "decision-1",
  ticker: "300308.SZ",
  action: "continue_observing",
  status: "observation_only",
  decision_time: "2026-07-01T00:00:00Z",
  thesis_summary: "现金流改善是核心观察点。",
  bear_case_summary: "应收账款可能掩盖现金流质量。",
  evidence_ids: ["ev-1"],
  kill_conditions: ["经营现金流再次转负"],
  outcome_status: "open",
  outcome_evidence_ids: [],
  review_due_at: "2026-07-10T00:00:00Z",
  review_state: "overdue" as const,
  outcome_history: [],
};

describe("DecisionPanel", () => {
  beforeEach(() => vi.clearAllMocks());

  it("shows the original judgment beside the later outcome and records facts", async () => {
    vi.mocked(api.fetchDecisions).mockResolvedValue({ decisions: [decision] });
    vi.mocked(api.recordDecisionOutcome).mockResolvedValue({
      decision: {
        ...decision,
        outcome_status: "partially_confirmed",
        review_state: "reviewed",
        outcome_history: [{
          outcome_id: "outcome-1",
          outcome_status: "partially_confirmed",
          summary: "价格上涨，但现金流仍待验证。",
          evidence_ids: [],
          recorded_by: "本地研究者",
          recorded_at: "2026-07-13T12:00:00Z",
        }],
      },
    });

    render(<DecisionPanel run={run} />);
    expect(await screen.findByText("现金流改善是核心观察点。")).toBeInTheDocument();
    expect(screen.getByText("后来发生")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /记录复盘结果/ }));
    fireEvent.change(screen.getByLabelText("事实结果"), { target: { value: "价格上涨，但现金流仍待验证。" } });
    fireEvent.click(screen.getByRole("button", { name: "保存复盘" }));

    await waitFor(() => expect(api.recordDecisionOutcome).toHaveBeenCalledWith(
      "decision-1",
      expect.objectContaining({ summary: "价格上涨，但现金流仍待验证。", recorded_by: "本地研究者" }),
    ));
    expect(await screen.findByText("价格上涨，但现金流仍待验证。")).toBeInTheDocument();
  });

  it("creates a decision snapshot with evidence and invalidation conditions", async () => {
    vi.mocked(api.fetchDecisions).mockResolvedValue({ decisions: [] });
    vi.mocked(api.createDecision).mockResolvedValue({ decision });

    render(<DecisionPanel run={run} />);
    fireEvent.click(await screen.findByRole("button", { name: "建立第一条决策" }));
    fireEvent.change(screen.getByLabelText("最强反方"), { target: { value: "订单无法转化为利润。" } });
    fireEvent.change(screen.getByLabelText("失效条件"), { target: { value: "毛利率连续两个季度下降" } });
    fireEvent.click(screen.getByRole("button", { name: "记录决策" }));

    await waitFor(() => expect(api.createDecision).toHaveBeenCalledWith(expect.objectContaining({
      ticker: "300308.SZ",
      thesis: "订单质量正在改善。",
      evidence_ids: ["ev-1"],
      invalidation_conditions: ["毛利率连续两个季度下降"],
      source_run_id: "run-1",
    })));
  });
});
