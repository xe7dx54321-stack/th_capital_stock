import { AlertTriangle, Check, LoaderCircle, Radio } from "lucide-react";

import type { WorkflowEvent, WorkflowRun } from "../../lib/api";

interface Props { run: WorkflowRun | null; events: WorkflowEvent[]; connection: "live" | "polling" | "idle"; }

const eventLabels: Record<string, string> = {
  "run.queued": "研究任务已进入队列",
  "run.started": "研究任务已启动",
  "stage.started": "开始执行研究步骤",
  "stage.progress": "研究步骤正在推进",
  "stage.completed": "研究步骤已完成",
  "stage.warning": "研究步骤需要关注",
  "artifact.created": "研究报告已生成",
  "review.requested": "研究记忆等待人工审核",
  "run.completed": "本次研究已完成",
  "run.failed": "本次研究未能完成",
  "run.cancelled": "本次研究已取消",
};

const stageLabels: Record<string, string> = {
  input_validation: "输入校验",
  evidence_collection: "证据收集",
  evidence_normalization: "证据整理",
  reasoning: "研究推演",
  report_generation: "报告生成",
  memory_candidate: "记忆候选",
};

function eventMessage(event: WorkflowEvent) {
  const payloadMessage = String(event.payload.message || "");
  if (/[一-鿿]/.test(payloadMessage)) return payloadMessage;
  const stage = stageLabels[String(event.stage_id || event.payload.stage || "")];
  return stage ? `${eventLabels[event.event_type] || "研究进程更新"}：${stage}` : eventLabels[event.event_type] || "研究进程更新";
}

export default function RunTimeline({ run, events, connection }: Props) {
  if (!run) return <section className="timeline empty-timeline"><p>提交一个标的，研究流程会在这里逐步展开。</p></section>;
  return (
    <section className="timeline" aria-label="运行时间线">
      <div className="timeline-header">
        <div><p className="eyebrow">研究进程</p><h2>{String(run.input.ticker || run.workflow_id)}</h2></div>
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
              <span><strong>{eventMessage(event)}</strong><small>第 {event.sequence} 条进程记录</small></span>
              <time>{new Date(event.created_at).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}</time>
            </div>
          );
        })}
      </div>
      {run.error_message ? <p className="run-error" role="alert">{run.error_message}</p> : null}
    </section>
  );
}
