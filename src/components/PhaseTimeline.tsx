/**
 * 研究阶段时间线组件
 *
 * 展示 Phase 100-170 各研究阶段的执行状态
 *
 * 小白讲解：这个组件是一个横向的阶段进度条，
 * 显示系统中各个自动化研究阶段的完成情况。
 * 每个阶段显示一个百分比进度条。
 */

import { CheckCircle2, Circle, Loader2 } from "lucide-react";
import type { PhaseInfo } from "../lib/api";

interface Props {
  phases?: PhaseInfo[];
  loading?: boolean;
}

function statusIcon(status: string) {
  if (status === "completed") return CheckCircle2;
  if (status === "active") return Loader2;
  return Circle;
}

function statusColor(status: string): string {
  if (status === "completed") return "#7cb342";
  if (status === "active") return "#d4a373";
  return "#5a5a5a";
}

export default function PhaseTimeline({ phases, loading }: Props) {
  if (loading || !phases) {
    return (
      <div className="card-base p-6">
        <div className="animate-pulse flex flex-col gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-12 bg-surface-3 rounded" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="card-base p-6">
      <div className="mb-4">
        <div className="text-lg font-medium text-text">研究流程概览</div>
        <div className="text-xs text-text-muted mt-1">
          Phase 100-170 各阶段的任务执行情况
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {phases.map((p, idx) => {
          const Icon = statusIcon(p.status);
          const color = statusColor(p.status);
          const pct = p.taskCount > 0 ? Math.round((p.completedCount / p.taskCount) * 100) : 0;
          return (
            <div
              key={p.phaseId}
              className="relative p-4 bg-surface rounded-md border border-surface-4 animate-fade-in"
              style={{ animationDelay: `${idx * 0.05}s` }}
            >
              {/* 标题和图标 */}
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                  <div className="text-xs text-text-dim uppercase tracking-wider">
                    {p.phaseId}
                  </div>
                  <div className="mt-1 text-sm text-text font-medium">{p.phaseName}</div>
                </div>
                <Icon
                  className={"w-4 h-4 flex-shrink-0 mt-1 " + (p.status === "active" ? "animate-spin" : "")}
                  style={{ color }}
                />
              </div>

              {/* 描述 */}
              <div className="mt-2 text-xs text-text-muted">{p.description}</div>

              {/* 进度条 */}
              <div className="mt-3">
                <div className="flex items-center justify-between text-xs mb-1.5">
                  <span className="text-text-dim">
                    {p.completedCount} / {p.taskCount}
                  </span>
                  <span className="tabular-nums" style={{ color }}>{pct}%</span>
                </div>
                <div className="h-1 bg-surface-3 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{ width: `${pct}%`, backgroundColor: color }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
