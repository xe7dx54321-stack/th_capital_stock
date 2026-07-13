/**
 * 新机会发现组件
 *
 * 展示自动扫描发现的新标的（不在关注池中的）
 * 点击卡片进入标的详情页
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Flame, TrendingUp, Sparkles, Newspaper, Target } from "lucide-react";
import type { DiscoveryItem } from "../lib/api";

interface Props {
  discoveries?: DiscoveryItem[];
  loading?: boolean;
}

function priorityStyle(p: string) {
  switch (p) {
    case "high":
      return {
        bg: "bg-[#b74a2c]/15",
        border: "border-[#b74a2c]/40",
        text: "text-[#d4a373]",
        label: "高优先级",
        icon: Flame,
      };
    case "medium":
      return {
        bg: "bg-[#d4a373]/10",
        border: "border-[#d4a373]/30",
        text: "text-[#d4a373]",
        label: "中等",
        icon: TrendingUp,
      };
    default:
      return {
        bg: "bg-surface-3",
        border: "border-surface-4",
        text: "text-text-muted",
        label: "待观察",
        icon: Sparkles,
      };
  }
}

export default function DiscoveryCards({ discoveries, loading }: Props) {
  const [showAll, setShowAll] = useState(false);
  const navigate = useNavigate();

  if (loading || !discoveries) {
    return (
      <div>
        <div className="mb-4">
          <div className="text-lg font-medium text-text">新机会发现</div>
          <div className="text-xs text-text-muted mt-1">自动扫描新闻/研报/财务变化发现新标的</div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="card-base h-40 animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  const list = showAll ? discoveries : discoveries.slice(0, 6);

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="text-lg font-medium text-text">新机会发现</div>
          <div className="text-xs text-text-muted mt-1">
            基于新闻热度、研报提及、财务变化的自动扫描
            {discoveries.length > 0 ? ` · 共 ${discoveries.length} 个候选，点击卡片进入详情` : ""}
          </div>
        </div>
      </div>

      {discoveries.length === 0 ? (
        <div className="card-base p-8 text-center text-text-muted text-sm">
          当前没有新发现。系统持续扫描中…
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {list.map((d, idx) => {
              const style = priorityStyle(d.priority);
              const Icon = style.icon;
              return (
                <div
                  key={d.ticker}
                  onClick={() => navigate(`/stock/${encodeURIComponent(d.ticker)}`)}
                  className="card-base p-5 flex flex-col gap-3 cursor-pointer hover:border-accent transition-colors animate-fade-in"
                  style={{ animationDelay: `${idx * 0.05}s` }}
                >
                  {/* 顶部：名称 + 优先级标签 */}
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="text-lg font-medium text-text">{d.name}</div>
                      <div className="text-xs text-text-dim mt-0.5">{d.ticker}</div>
                    </div>
                    <div
                      className={
                        "flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs border " +
                        style.bg + " " + style.border + " " + style.text
                      }
                    >
                      <Icon className="w-3 h-3" />
                      {style.label}
                    </div>
                  </div>

                  {/* 行业标签 */}
                  <div className="flex items-center gap-2">
                    <span
                      className={
                        "flex items-center gap-1.5 px-2 py-1 rounded text-xs border " +
                        (d.isInFocus
                          ? "border-[#7cb342]/40 bg-[#7cb342]/10 text-[#7cb342]"
                          : "border-surface-4 text-text-muted bg-surface-3")
                      }
                    >
                      {d.isInFocus && <Target className="w-3 h-3" />}
                      {d.isInFocus ? `${d.sector} · 在关注方向` : `非关注方向`}
                    </span>
                    <span className="text-xs text-text-dim">{d.market}股</span>
                  </div>

                  {/* 发现原因 */}
                  <div className="text-sm text-text-muted">{d.triggerReason}</div>

                  {/* 新闻提及数 */}
                  <div className="flex items-center gap-2 text-xs">
                    <Newspaper className="w-3 h-3 text-text-dim" />
                    <span className="text-text-dim">{d.newsMentions} 次提及</span>
                  </div>

                  {/* 最新触发新闻 */}
                  {d.latestNewsTitle && (
                    <div className="mt-1 pt-3 border-t border-surface-4">
                      <div className="text-xs text-text-dim mb-1">
                        {d.latestNewsAt ? d.latestNewsAt.slice(0, 16).replace("T", " ") : ""}
                      </div>
                      <div className="text-xs text-text-muted leading-relaxed line-clamp-2">
                        {d.latestNewsTitle}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {discoveries.length > 6 && (
            <div className="mt-4 text-center">
              <button
                onClick={() => setShowAll(!showAll)}
                className="text-xs text-text-muted hover:text-accent transition-colors underline underline-offset-4"
              >
                {showAll ? "收起" : `查看剩余 ${discoveries.length - 6} 个`}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
