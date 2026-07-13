import { Archive, Check, ChevronDown, ChevronUp, ExternalLink, X } from "lucide-react";
import { useEffect, useState } from "react";

import { fetchMemory, reviewMemory, type MemoryDetail } from "../../lib/api";

function value(value: unknown) {
  if (value === undefined || value === null || value === "") return "—";
  return typeof value === "string" ? value : JSON.stringify(value, null, 2);
}

interface Props { memoryId: string | null; onReviewed?: () => void; }

const statusLabels: Record<string, string> = {
  candidate: "候选",
  approved: "已批准",
  rejected: "已拒绝",
  archived: "已归档",
};

const relationLabels: Record<string, string> = {
  supports: "支持",
  contradicts: "反驳",
  supersedes: "替代",
  context: "背景",
};

const fieldLabels: Record<string, string> = {
  thesis: "核心论点",
  bull_case: "乐观情景",
  bear_case: "谨慎情景",
  risks: "关键风险",
  catalysts: "催化因素",
  valuation: "估值判断",
  confidence: "置信度",
};

export default function MemoryReviewPanel({ memoryId, onReviewed }: Props) {
  const [memory, setMemory] = useState<MemoryDetail | null>(null);
  const [reviewer, setReviewer] = useState("本地研究者");
  const [reason, setReason] = useState("");
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!memoryId) { setMemory(null); return; }
    let active = true;
    setError("");
    void fetchMemory(memoryId)
      .then((result) => { if (active) setMemory(result); })
      .catch((cause) => { if (active) setError(cause instanceof Error ? cause.message : "记忆读取失败"); });
    return () => { active = false; };
  }, [memoryId]);

  async function submit(action: "approve" | "reject" | "archive") {
    if (!memory || !reviewer.trim() || !reason.trim()) { setError("请填写审核人和审核原因。"); return; }
    setBusy(true);
    setError("");
    try {
      const result = await reviewMemory(memory.memory_id, action, reviewer.trim(), reason.trim());
      setMemory(result.memory);
      setReason("");
      onReviewed?.();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "审核操作失败");
    } finally { setBusy(false); }
  }

  if (!memoryId) return (
    <section className="context-block memory-placeholder">
      <h3>研究记忆</h3><p>深挖报告产生候选论点后，可在这里进行人工审核。</p><span>候选不会自动写入</span>
    </section>
  );
  if (!memory) return <section className="context-block memory-review"><h3>研究记忆</h3><p>{error || "正在读取候选版本…"}</p></section>;

  const candidate = memory.status === "candidate";
  return (
    <section className="context-block memory-review">
      <div className="memory-title"><h3>研究记忆</h3><span className={`memory-status is-${memory.status}`}>{statusLabels[memory.status] || "状态未知"}</span></div>
      <div className="memory-version"><strong>V{memory.version}</strong><span>{memory.entity_id}</span></div>
      <div className="diff-list">
        {memory.field_diff.length === 0 ? <p>没有检测到字段变化。</p> : memory.field_diff.map((item) => (
          <article key={item.field}>
            <strong>{fieldLabels[item.field] || "研究字段"}</strong>
            <del>{value(item.before)}</del>
            <ins>{value(item.after)}</ins>
          </article>
        ))}
      </div>
      <button className="sources-toggle" onClick={() => setSourcesOpen((open) => !open)}>
        <ExternalLink size={13} /> 查看来源 ({memory.evidence_links.length}) {sourcesOpen ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
      </button>
      {sourcesOpen ? <div className="memory-sources">{memory.evidence_links.map((link) => <code key={`${link.evidence_id}-${link.relation}`}>[{relationLabels[link.relation] || "关联"}] {link.evidence_id}</code>)}</div> : null}
      {candidate ? (
        <div className="review-form">
          <label>审核人<input value={reviewer} onChange={(event) => setReviewer(event.target.value)} /></label>
          <label>审核原因<textarea value={reason} onChange={(event) => setReason(event.target.value)} placeholder="说明采纳或拒绝的依据" rows={2} /></label>
          {error ? <p role="alert">{error}</p> : null}
          <div className="review-actions">
            <button disabled={busy} onClick={() => void submit("approve")}><Check size={13} /> 批准写入</button>
            <button disabled={busy} onClick={() => void submit("reject")}><X size={13} /> 拒绝</button>
            <button disabled={busy} onClick={() => void submit("archive")}><Archive size={13} /> 归档</button>
          </div>
        </div>
      ) : <p className="reviewed-note">{memory.reviewed_by ? `${memory.reviewed_by}：${memory.review_reason}` : "该版本已完成审核。"}</p>}
    </section>
  );
}
