import { Database, Hourglass, Layers3 } from "lucide-react";

import type { WorkflowRun } from "../../lib/api";
import MemoryReviewPanel from "../memories/MemoryReviewPanel";

function list(value: unknown): string[] { return Array.isArray(value) ? value.map(String) : []; }

function claimTexts(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.map((item) => {
    if (item && typeof item === "object" && "text" in item) return String((item as { text: unknown }).text);
    return String(item);
  });
}

function freshnessLabel(value: unknown): string {
  const labels: Record<string, string> = {
    fresh: "新鲜",
    stale: "已过期",
    missing: "有缺失",
    complete: "完整",
    partial: "部分完整",
    local: "本地数据",
    unknown: "待检测",
  };
  const translate = (item: unknown) => labels[String(item).toLowerCase()] || String(item);
  if (value && typeof value === "object") {
    const item = value as { condition?: unknown; status?: unknown };
    return [item.condition, item.status].filter(Boolean).map(translate).join(" / ") || "待检测";
  }
  return value ? translate(value) : "待检测";
}

export default function ResearchContextPanel({ run, onMemoryReviewed }: { run: WorkflowRun | null; onMemoryReviewed?: () => void }) {
  const summary = run?.summary || {};
  const evidence = list(summary.evidence_ids);
  const claims = claimTexts(summary.claims);
  const freshness = freshnessLabel(summary.freshness || summary.data_freshness);

  return (
    <aside className="context-panel" aria-label="研究上下文">
      <div><p className="eyebrow">研究上下文</p><h2>证据与判断</h2></div>
      <section className="context-block">
        <h3><Database size={15} /> 证据索引 <span>{evidence.length}</span></h3>
        {evidence.length ? evidence.map((item) => <code key={item}>{item}</code>) : <p>报告生成后，证据 ID 会陈列在此。</p>}
      </section>
      <section className="context-block">
        <h3><Hourglass size={15} /> 数据新鲜度</h3>
        <strong className="freshness">{freshness}</strong>
        <p>任何过期、缺失或口径冲突都会保留在报告中，不被静默覆盖。</p>
      </section>
      <section className="context-block">
        <h3><Layers3 size={15} /> 关键判断 <span>{claims.length}</span></h3>
        {claims.length ? claims.map((claim) => <p className="claim" key={claim}>{claim}</p>) : <p>当前没有经过证据约束的新增判断。</p>}
      </section>
      <MemoryReviewPanel memoryId={summary.memory_candidate_id ? String(summary.memory_candidate_id) : null} onReviewed={onMemoryReviewed} />
    </aside>
  );
}
