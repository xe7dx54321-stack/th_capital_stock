import assert from "node:assert/strict";
import test from "node:test";

import { buildResearchExecutionSummary } from "../../api/services/research-execution-summary.js";


test("research execution summary exposes the complete 30-stage catalog and preserves warnings", () => {
  const events = [
    { event_type: "run.started", message: "run", created_at: "2026-07-22T00:00:00Z" },
    { event_type: "stage.started", stage_id: "validate_input", message: "started", payload: {}, created_at: "2026-07-22T00:00:01Z" },
    { event_type: "stage.completed", stage_id: "validate_input", message: "validated", payload: {}, created_at: "2026-07-22T00:00:02Z" },
    { event_type: "stage.started", stage_id: "report_synthesis", message: "started", payload: {}, created_at: "2026-07-22T00:00:03Z" },
    { event_type: "stage.warning", stage_id: "report_synthesis", message: "fallback", payload: {}, created_at: "2026-07-22T00:00:04Z" },
  ];
  const result = buildResearchExecutionSummary(events);
  assert.equal(result.totalStages, 30);
  assert.equal(result.completedStages, 2);
  assert.equal(result.warningStages, 1);
  assert.equal(result.status, "running");
  assert.deepEqual(
    result.groups.map((group) => group.label),
    ["研究准备", "资料检索", "证据与分析", "报告生成", "复核与归档"],
  );
  const synthesis = result.groups.flatMap((group) => group.stages)
    .find((stage) => stage.id === "report_synthesis");
  assert.equal(synthesis.label, "模型综合完整研究报告");
  assert.equal(synthesis.status, "warning");
  const pending = result.groups.flatMap((group) => group.stages)
    .find((stage) => stage.id === "persist_final_report");
  assert.equal(pending.status, "pending");
  assert.equal(pending.message, "等待中");
});
