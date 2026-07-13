import { BookOpenCheck, Database, Hourglass, Layers3 } from "lucide-react";

import type { WorkflowRun } from "../../lib/api";

function list(value: unknown): string[] { return Array.isArray(value) ? value.map(String) : []; }

export default function ResearchContextPanel({ run }: { run: WorkflowRun | null }) {
  const summary = run?.summary || {};
  const evidence = list(summary.evidence_ids);
  const claims = list(summary.claims);
  const freshness = String(summary.freshness || summary.data_freshness || "待检测");

  return (
    <aside className="context-panel" aria-label="研究上下文">
      <div><p className="eyebrow">Research context</p><h2>证据侧栏</h2></div>
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
      <section className="context-block memory-placeholder">
        <h3><BookOpenCheck size={15} /> 研究记忆</h3>
        <p>候选论点必须人工审核，才会写入长期研究记忆。</p>
        <span>审核工作流 · 下一阶段</span>
      </section>
    </aside>
  );
}
