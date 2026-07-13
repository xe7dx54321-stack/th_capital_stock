/**
 * 价值评分榜单组件
 *
 * 展示所有股票的 5 维价值评分，按综合分排序
 * 点击行可进入标的详情页
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import type { ValueScoreItem } from "../lib/api";

interface Props {
  scores?: ValueScoreItem[];
  loading?: boolean;
}

function scoreColor(score: number | null): string {
  if (score == null || isNaN(score)) return "#5a5a5a";
  if (score >= 7) return "#7cb342";
  if (score >= 5) return "#d4a373";
  return "#b74a2c";
}

const DIMENSION_LABELS = ["基本面", "估值", "技术", "主题", "产业"];

function ScoreDots({ scores }: { scores: (number | null)[] }) {
  return (
    <div className="flex items-center gap-2">
      {scores.map((s, i) => {
        const label = DIMENSION_LABELS[i] || "";
        if (s == null || isNaN(s)) {
          return (
            <div
              key={i}
              className="flex items-center gap-1.5"
              title={`${label}: 暂无数据`}
            >
              <div
                className="w-2 h-2 rounded-full flex-shrink-0"
                style={{ backgroundColor: "#5a5a5a", opacity: 0.4 }}
              />
              <span className="text-xs text-text-dim">—</span>
            </div>
          );
        }
        return (
          <div
            key={i}
            className="flex items-center gap-1.5"
            title={`${label}: ${s.toFixed(1)}`}
          >
            <div
              className="w-2 h-2 rounded-full flex-shrink-0"
              style={{ backgroundColor: scoreColor(s) }}
            />
            <span className="text-xs text-text-muted">{s.toFixed(1)}</span>
          </div>
        );
      })}
    </div>
  );
}

function ScoreBar({ score }: { score: number | null }) {
  if (score == null || isNaN(score)) {
    return (
      <div className="flex items-center gap-2">
        <div className="w-20 h-1 bg-surface-3 rounded-full overflow-hidden flex-shrink-0" />
        <span className="text-base font-medium tabular-nums w-8 text-right text-text-dim">
          —
        </span>
      </div>
    );
  }
  const color = scoreColor(score);
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-1 bg-surface-3 rounded-full overflow-hidden flex-shrink-0">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${(score / 10) * 100}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-base font-medium tabular-nums w-8 text-right" style={{ color }}>
        {score.toFixed(1)}
      </span>
    </div>
  );
}

export default function ValueScoreTable({ scores, loading }: Props) {
  const [filter, setFilter] = useState<string>("all");
  const navigate = useNavigate();

  if (loading || !scores) {
    return (
      <div className="card-base p-8">
        <div className="animate-pulse flex flex-col gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-10 bg-surface-3 rounded" />
          ))}
        </div>
      </div>
    );
  }

  const filtered = filter === "all" ? scores : scores.filter((s) => s.market === filter);
  const topList = filtered.slice(0, 20);

  return (
    <div className="card-base overflow-hidden">
      {/* 标题区 */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-surface-4">
        <div className="flex items-baseline gap-3">
          <div className="text-base font-medium text-text">价值评分榜单</div>
          <div className="text-xs text-text-muted">点击任意行进入详情页</div>
        </div>
        <div className="flex items-center gap-1 text-xs">
          {[
            { key: "all", label: "全部" },
            { key: "A", label: "A股" },
            { key: "H", label: "港股" },
            { key: "US", label: "美股" },
          ].map((opt) => (
            <button
              key={opt.key}
              onClick={() => setFilter(opt.key)}
              className={
                "px-2 py-1 rounded-md transition-colors " +
                (filter === opt.key
                  ? "bg-accent text-surface font-medium"
                  : "text-text-muted hover:text-text hover:bg-surface-3")
              }
            >
              {opt.label}
              <span className="ml-1 opacity-60">
                ({scores.filter((s) => opt.key === "all" || s.market === opt.key).length})
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* 表头 - 紧凑样式 */}
      <div className="grid grid-cols-13 gap-3 px-5 py-1.5 text-[11px] text-text-muted uppercase tracking-wider border-b border-surface-4">
        <div className="col-span-1">#</div>
        <div className="col-span-3">名称代码</div>
        <div className="col-span-2">市场 · 主题</div>
        <div className="col-span-2">综合建议</div>
        <div className="col-span-2">5 维评分</div>
        <div className="col-span-2 text-right">综合分</div>
        <div className="col-span-1 text-right">最新价</div>
      </div>

      {/* 数据行 - 每行只占 1 行 */}
      <div className="divide-y divide-surface-4">
        {topList.length === 0 ? (
          <div className="px-6 py-8 text-center text-text-muted text-sm">暂无数据</div>
        ) : (
          topList.map((item, idx) => (
            <div
              key={item.tsCode}
              onClick={() => navigate(`/stock/${encodeURIComponent(item.tsCode)}`)}
              className="grid grid-cols-13 gap-3 px-5 py-1.5 cursor-pointer hover:bg-surface-2 transition-colors animate-fade-in items-center"
              style={{ animationDelay: `${idx * 0.02}s` }}
            >
              <div className="col-span-1 text-text-dim text-xs tabular-nums">
                {idx + 1}
              </div>
              <div className="col-span-3 flex items-baseline gap-2 min-w-0">
                <span className="text-sm text-text font-medium truncate">{item.name}</span>
                <span className="text-xs text-text-dim truncate">{item.tsCode}</span>
              </div>
              <div className="col-span-2 text-xs text-text-muted truncate">
                {item.market}股 · {item.sector || "—"}
              </div>
              <div className="col-span-2">
                {item.verdict ? (
                  <span
                    className={`inline-block text-[11px] px-1.5 py-0.5 rounded border ${
                      /看多|买入|强烈看多|超买/i.test(item.verdict) ? "border-emerald-400/40 text-emerald-400 bg-emerald-500/10" :
                      /看空|卖出|强烈看空|超卖/i.test(item.verdict) ? "border-rose-400/40 text-rose-400 bg-rose-500/10" :
                      /中性|观望|持有/i.test(item.verdict) ? "border-surface-4 text-text-muted bg-surface-3" :
                      "border-amber-400/40 text-amber-400 bg-amber-500/10"
                    }`}
                  >
                    {item.verdict}
                  </span>
                ) : (
                  <span className="text-xs text-text-dim">—</span>
                )}
              </div>
              <div className="col-span-2">
                <ScoreDots
                  scores={[
                    item.fundamentalQuality,
                    item.valuationPosition,
                    item.technicalMomentum,
                    item.themeRelevance,
                    item.industryPosition,
                  ]}
                />
              </div>
              <div className="col-span-2 flex justify-end">
                <ScoreBar score={item.compositeScore} />
              </div>
              <div className="col-span-1 text-right text-text-muted text-xs tabular-nums">
                {item.latestClose != null ? item.latestClose.toFixed(2) : "—"}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
