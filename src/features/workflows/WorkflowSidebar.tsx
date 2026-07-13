import { CircleDot, Clock3, FileSearch, LockKeyhole } from "lucide-react";

import type { WorkflowDefinition, WorkflowRun } from "../../lib/api";

interface Props {
  workflows: WorkflowDefinition[];
  runs: WorkflowRun[];
  selectedRunId: string | null;
  onSelectRun: (runId: string) => void;
}

const labels: Record<string, string> = {
  stock_deep_dive: "个股深挖",
  daily_brief: "每日简报",
  portfolio_review: "组合复盘",
  thesis_update: "论点更新",
};

export default function WorkflowSidebar({ workflows, runs, selectedRunId, onSelectRun }: Props) {
  return (
    <aside className="workbench-sidebar" aria-label="工作流和历史记录">
      <section>
        <p className="eyebrow">Research protocols</p>
        <h2>研究流程</h2>
        <div className="protocol-list">
          {workflows.map((workflow) => (
            <div className={`protocol ${workflow.enabled ? "is-ready" : "is-locked"}`} key={workflow.workflow_id}>
              {workflow.enabled ? <FileSearch size={17} /> : <LockKeyhole size={16} />}
              <span><strong>{labels[workflow.workflow_id] || workflow.title}</strong><small>{workflow.enabled ? "可运行" : "即将接入"}</small></span>
            </div>
          ))}
        </div>
      </section>

      <section className="run-history">
        <div className="section-heading"><h2>运行档案</h2><span>{runs.length}</span></div>
        {runs.length === 0 ? <p className="quiet">尚无研究记录。</p> : (
          <div className="run-list">
            {runs.map((run) => (
              <button
                className={`run-record ${selectedRunId === run.run_id ? "is-selected" : ""}`}
                key={run.run_id}
                onClick={() => onSelectRun(run.run_id)}
              >
                <span className={`status-dot status-${run.status}`}><CircleDot size={13} /></span>
                <span>
                  <strong>{String(run.input.ticker || labels[run.workflow_id] || run.workflow_id)}</strong>
                  <small><Clock3 size={11} /> {new Date(run.created_at).toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" })}</small>
                </span>
                <em>{run.status.replace("_", " ")}</em>
              </button>
            ))}
          </div>
        )}
      </section>
    </aside>
  );
}
