import { AlertTriangle, Check, LoaderCircle, Radio } from "lucide-react";

import type { WorkflowEvent, WorkflowRun } from "../../lib/api";

interface Props { run: WorkflowRun | null; events: WorkflowEvent[]; connection: "live" | "polling" | "idle"; }

function eventMessage(event: WorkflowEvent) {
  return event.message || String(event.payload.message || event.payload.stage || event.event_type);
}

export default function RunTimeline({ run, events, connection }: Props) {
  if (!run) return <section className="timeline empty-timeline"><p>提交一个标的，研究流程会在这里逐步展开。</p></section>;
  return (
    <section className="timeline" aria-label="运行时间线">
      <div className="timeline-header">
        <div><p className="eyebrow">Run ledger</p><h2>{String(run.input.ticker || run.workflow_id)}</h2></div>
        <span className={`connection ${connection}`}><Radio size={13} /> {connection === "polling" ? "轮询恢复" : connection === "live" ? "实时连接" : "已归档"}</span>
      </div>
      <div className="event-rail">
        {events.length === 0 ? <div className="event-row"><LoaderCircle className="spin" size={16} /><span><strong>正在读取运行日志</strong><small>等待本地工作进程返回事件</small></span></div> : events.map((event) => {
          const warning = event.level === "warning" || event.event_type.includes("warning");
          const failed = event.level === "error" || event.event_type.includes("failed");
          const complete = event.event_type.includes("completed") || event.event_type === "artifact.created";
          return (
            <div className={`event-row ${warning || failed ? "is-warning" : ""}`} key={`${event.run_id}-${event.sequence}`}>
              {warning || failed ? <AlertTriangle size={16} /> : complete ? <Check size={16} /> : <LoaderCircle size={16} />}
              <span><strong>{eventMessage(event)}</strong><small>{event.event_type} · #{event.sequence}</small></span>
              <time>{new Date(event.created_at).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}</time>
            </div>
          );
        })}
      </div>
      {run.error_message ? <p className="run-error" role="alert">{run.error_message}</p> : null}
    </section>
  );
}
