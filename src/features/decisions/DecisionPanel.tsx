import { CalendarClock, CheckCircle2, ChevronDown, FilePenLine, History, Scale } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  createDecision,
  fetchDecisions,
  recordDecisionOutcome,
  type DecisionDetail,
  type WorkflowRun,
} from "../../lib/api";


const actionLabels: Record<string, string> = {
  continue_observing: "继续观察",
  deepen_research: "补充研究",
  reduce_attention: "降低关注",
  close_thesis: "关闭论点",
};

const outcomeLabels: Record<string, string> = {
  open: "等待复盘",
  confirmed: "得到验证",
  failed: "未获验证",
  partially_confirmed: "部分验证",
  invalidated: "失效条件触发",
  closed: "已关闭",
};

function array(value: unknown): string[] {
  return Array.isArray(value) ? value.map(String).filter(Boolean) : [];
}

function claimText(value: unknown): string {
  if (!Array.isArray(value) || value.length === 0) return "";
  const first = value[0];
  return first && typeof first === "object" && "text" in first
    ? String((first as { text: unknown }).text)
    : String(first);
}

function splitLines(value: string): string[] {
  return value.split(/[\n,，]/).map((item) => item.trim()).filter(Boolean);
}

function dueDate(days: number) {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return date.toISOString();
}

export default function DecisionPanel({ run }: { run: WorkflowRun | null }) {
  const ticker = String(run?.input.ticker || "");
  const summary = run?.summary || {};
  const suggestedEvidence = useMemo(() => array(summary.evidence_ids), [summary.evidence_ids]);
  const suggestedThesis = useMemo(() => claimText(summary.claims), [summary.claims]);
  const [decisions, setDecisions] = useState<DecisionDetail[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);
  const [reviewing, setReviewing] = useState(false);
  const [action, setAction] = useState("continue_observing");
  const [thesis, setThesis] = useState("");
  const [counterargument, setCounterargument] = useState("");
  const [evidenceIds, setEvidenceIds] = useState("");
  const [killConditions, setKillConditions] = useState("");
  const [referencePrice, setReferencePrice] = useState("");
  const [reviewDays, setReviewDays] = useState("90");
  const [outcomeStatus, setOutcomeStatus] = useState("partially_confirmed");
  const [outcomeSummary, setOutcomeSummary] = useState("");
  const [outcomeEvidence, setOutcomeEvidence] = useState("");
  const [observedPrice, setObservedPrice] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setCreating(false);
    setReviewing(false);
    setThesis(suggestedThesis);
    setEvidenceIds(suggestedEvidence.join(", "));
    setCounterargument("");
    setKillConditions("");
    setError("");
    if (!ticker) { setDecisions([]); return; }
    let active = true;
    setLoading(true);
    void fetchDecisions(ticker)
      .then((result) => { if (active) setDecisions(result.decisions); })
      .catch((cause) => { if (active) setError(cause instanceof Error ? cause.message : "决策记录读取失败"); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [ticker, run?.run_id, suggestedEvidence, suggestedThesis]);

  const activeDecision = decisions[0] || null;
  const latestOutcome = activeDecision?.outcome_history[0] || null;
  const canCreate = thesis.trim() && counterargument.trim() && splitLines(evidenceIds).length > 0 && splitLines(killConditions).length > 0;
  const reviewDateLabel = useMemo(() => activeDecision?.review_due_at
    ? new Date(activeDecision.review_due_at).toLocaleDateString("zh-CN")
    : "未设置", [activeDecision?.review_due_at]);

  async function submitDecision(event: FormEvent) {
    event.preventDefault();
    if (!ticker || !canCreate || busy) return;
    setBusy(true);
    setError("");
    try {
      const result = await createDecision({
        ticker,
        action,
        thesis: thesis.trim(),
        counterargument: counterargument.trim(),
        evidence_ids: splitLines(evidenceIds),
        invalidation_conditions: splitLines(killConditions),
        reference_price: referencePrice ? Number(referencePrice) : null,
        review_due_at: dueDate(Number(reviewDays)),
        source_run_id: run?.run_id || null,
        source_memory_id: summary.memory_candidate_id ? String(summary.memory_candidate_id) : null,
        recorded_by: "本地研究者",
        time_horizon: `${reviewDays}天`,
      });
      setDecisions((current) => [result.decision, ...current]);
      setCreating(false);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "决策记录创建失败");
    } finally { setBusy(false); }
  }

  async function submitOutcome(event: FormEvent) {
    event.preventDefault();
    if (!activeDecision || !outcomeSummary.trim() || busy) return;
    setBusy(true);
    setError("");
    try {
      const result = await recordDecisionOutcome(activeDecision.decision_id, {
        outcome_status: outcomeStatus,
        summary: outcomeSummary.trim(),
        evidence_ids: splitLines(outcomeEvidence),
        observed_price: observedPrice ? Number(observedPrice) : null,
        recorded_by: "本地研究者",
      });
      setDecisions((current) => [result.decision, ...current.filter((item) => item.decision_id !== result.decision.decision_id)]);
      setReviewing(false);
      setOutcomeSummary("");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "复盘结果记录失败");
    } finally { setBusy(false); }
  }

  if (!ticker) return null;

  return (
    <section className="decision-panel" aria-label="决策复盘">
      <div className="decision-panel-header">
        <div><p className="eyebrow">决策闭环</p><h2>把判断留给未来检验</h2></div>
        <div className="decision-header-actions">
          {decisions.length ? <span>{decisions.length} 条记录</span> : null}
          <button type="button" onClick={() => setCreating((value) => !value)}><FilePenLine size={14} /> {creating ? "收起" : "新建决策"}</button>
        </div>
      </div>

      {loading ? <p className="decision-empty">正在读取决策档案…</p> : null}
      {!loading && !activeDecision && !creating ? (
        <div className="decision-empty-state">
          <Scale size={24} />
          <div><strong>还没有留下判断快照</strong><p>记录观点、反方与失效条件，之后再用事实复盘。</p></div>
          <button type="button" onClick={() => setCreating(true)}>建立第一条决策</button>
        </div>
      ) : null}

      {creating ? (
        <form className="decision-form" onSubmit={submitDecision}>
          <div className="decision-form-grid">
            <label>后续动作<select value={action} onChange={(event) => setAction(event.target.value)}>{Object.entries(actionLabels).map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
            <label>复盘周期<select value={reviewDays} onChange={(event) => setReviewDays(event.target.value)}><option value="30">30 天</option><option value="90">90 天</option><option value="180">180 天</option></select></label>
            <label className="is-wide">当前判断<textarea value={thesis} onChange={(event) => setThesis(event.target.value)} rows={2} placeholder="我现在认为……" /></label>
            <label className="is-wide">最强反方<textarea value={counterargument} onChange={(event) => setCounterargument(event.target.value)} rows={2} placeholder="这项判断最可能错在……" /></label>
            <label className="is-wide">失效条件<textarea value={killConditions} onChange={(event) => setKillConditions(event.target.value)} rows={2} placeholder="每行一项，例如：毛利率连续两个季度下降" /></label>
            <label>观察价格<input inputMode="decimal" value={referencePrice} onChange={(event) => setReferencePrice(event.target.value)} placeholder="可选" /></label>
            <label>证据编号<input value={evidenceIds} onChange={(event) => setEvidenceIds(event.target.value)} placeholder="例如 ev-1, ev-2" /></label>
          </div>
          <div className="decision-form-footer"><span>原始判断写入后不会被结果覆盖。</span><button disabled={!canCreate || busy}>{busy ? "正在保存" : "记录决策"}</button></div>
        </form>
      ) : null}

      {activeDecision && !creating ? (
        <div className="decision-comparison">
          <article className="decision-then">
            <div className="decision-card-title"><span><FilePenLine size={15} /> 当时判断</span><time>{new Date(activeDecision.decision_time).toLocaleDateString("zh-CN")}</time></div>
            <div className="decision-summary-line"><strong>{activeDecision.ticker}</strong><span>{actionLabels[activeDecision.action] || "研究决策"}</span></div>
            <blockquote>{activeDecision.thesis_summary}</blockquote>
            <div className="decision-detail"><small>最强反方</small><p>{activeDecision.bear_case_summary}</p></div>
            <div className="decision-detail"><small>失效条件</small>{activeDecision.kill_conditions.map((item) => <p key={item}>· {item}</p>)}</div>
            <div className="decision-evidence">{activeDecision.evidence_ids.map((item) => <code key={item}>{item}</code>)}</div>
          </article>
          <article className="decision-later">
            <div className="decision-card-title"><span><History size={15} /> 后来发生</span><span className={`review-state is-${activeDecision.review_state}`}>{activeDecision.review_state === "overdue" ? "待复盘" : outcomeLabels[activeDecision.outcome_status] || "观察中"}</span></div>
            {latestOutcome ? (
              <div className="outcome-result">
                <CheckCircle2 size={23} />
                <strong>{outcomeLabels[latestOutcome.outcome_status] || "已记录结果"}</strong>
                <p>{latestOutcome.summary}</p>
                <small>{latestOutcome.recorded_by} · {new Date(latestOutcome.recorded_at).toLocaleString("zh-CN")}</small>
              </div>
            ) : (
              <div className="outcome-pending"><CalendarClock size={23} /><strong>等待事实回答</strong><p>计划于 {reviewDateLabel} 复盘。在此之前只追加价格和证据，不改写原始判断。</p></div>
            )}
            <button className="outcome-toggle" type="button" onClick={() => setReviewing((value) => !value)}>{reviewing ? "收起复盘" : "记录复盘结果"}<ChevronDown size={14} /></button>
            {reviewing ? (
              <form className="outcome-form" onSubmit={submitOutcome}>
                <label>结果状态<select value={outcomeStatus} onChange={(event) => setOutcomeStatus(event.target.value)}><option value="confirmed">得到验证</option><option value="partially_confirmed">部分验证</option><option value="failed">未获验证</option><option value="invalidated">失效条件触发</option><option value="closed">结束观察</option></select></label>
                <label>事实结果<textarea value={outcomeSummary} onChange={(event) => setOutcomeSummary(event.target.value)} rows={3} placeholder="描述后来实际发生了什么" /></label>
                <div><label>观察价格<input inputMode="decimal" value={observedPrice} onChange={(event) => setObservedPrice(event.target.value)} placeholder="可选" /></label><label>新增证据<input value={outcomeEvidence} onChange={(event) => setOutcomeEvidence(event.target.value)} placeholder="可选" /></label></div>
                <button disabled={!outcomeSummary.trim() || busy}>{busy ? "正在保存" : "保存复盘"}</button>
              </form>
            ) : null}
          </article>
        </div>
      ) : null}
      {error ? <p className="decision-error" role="alert">{error}</p> : null}
    </section>
  );
}
