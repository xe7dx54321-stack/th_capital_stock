import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import MemoryReviewPanel from "../MemoryReviewPanel";
import * as api from "../../../lib/api";

vi.mock("../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../lib/api")>("../../../lib/api");
  return { ...actual, fetchMemory: vi.fn(), reviewMemory: vi.fn() };
});

const candidate = {
  memory_id: "memory-2", entity_type: "ticker", entity_id: "300308.SZ", memory_type: "investment_thesis",
  content: { thesis: "new" }, status: "candidate" as const, source_run_id: "run-1", parent_memory_id: "memory-1",
  version: 2, field_diff: [{ field: "thesis", before: "old", after: "new" }],
  evidence_links: [{ evidence_id: "ev-1", relation: "supports" as const, created_at: "2026-07-13" }],
  review_log: [], created_at: "2026-07-13", updated_at: "2026-07-13",
};

describe("MemoryReviewPanel", () => {
  it("shows sources and submits an audited approval", async () => {
    vi.mocked(api.fetchMemory).mockResolvedValue(candidate);
    vi.mocked(api.reviewMemory).mockResolvedValue({ memory: { ...candidate, status: "approved", reviewed_by: "本地研究者", review_reason: "证据已核验" } });
    const reviewed = vi.fn();
    render(<MemoryReviewPanel memoryId="memory-2" onReviewed={reviewed} />);

    expect(await screen.findByText("old")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /查看来源/ }));
    expect(screen.getByText("[支持] ev-1")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("审核原因"), { target: { value: "证据已核验" } });
    fireEvent.click(screen.getByRole("button", { name: "批准写入" }));

    await waitFor(() => expect(api.reviewMemory).toHaveBeenCalledWith("memory-2", "approve", "本地研究者", "证据已核验"));
    expect(reviewed).toHaveBeenCalled();
  });
});
