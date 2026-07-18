import { CircleDot, Clock3 } from "lucide-react";

import type { WorkflowRun } from "../../lib/api";

interface Props {
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

const statusLabels: Record<string, string> = {
  queued: "排队中",
  running: "运行中",
  waiting_review: "待审核",
  completed: "已完成",
  failed: "失败",
  cancelled: "已取消",
};

export default function WorkflowSidebar({ runs, selectedRunId, onSelectRun }: Props) {
  return (
    <aside className="workbench-sidebar" aria-label="运行历史记录">
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
                <em>{statusLabels[run.status] || "状态未知"}</em>
              </button>
            ))}
          </div>
        )}
      </section>
    </aside>
  );
}
