/**
 * 新闻流组件（增强版）
 *
 * - 显示最新抓取的新闻，支持按来源过滤
 * - 点击任意一条新闻 -> 打开弹窗查看正文 + 智能解读
 * - 弹窗内可点击"打开原文链接"跳转
 *
 * 小白讲解：
 *   - 每条新闻展示：时间、来源、标题、摘要、相关股票
 *   - 点击整条新闻 -> 打开详情弹窗，显示完整正文 + 解读
 */

import { useMemo, useState, useEffect } from "react";
import { Newspaper, ExternalLink, X, Lightbulb, ShieldCheck, AlertTriangle, TrendingUp, AlertCircle } from "lucide-react";
import type { NewsItem, NewsDetail } from "../lib/api";
import { fetchNewsDetail } from "../lib/api";

interface Props {
  items?: NewsItem[];
  sources?: string[];
  loading?: boolean;
}

function formatDate(s: string): string {
  if (!s) return "";
  return s.slice(0, 16).replace("T", " ");
}

// 美化来源名称
function prettySource(s: string): string {
  const mapping: Record<string, string> = {
    eastmoney_news_search: "东方财富",
    yahoo_finance_rss: "Yahoo Finance",
    manual_news: "人工收录",
    announcement: "公告",
  };
  return mapping[s] || s;
}

// 不同解读类型的图标
function insightIcon(type: string) {
  const t = (type || "").toLowerCase();
  if (t.includes("bull")) return <TrendingUp className="w-3.5 h-3.5" />;
  if (t.includes("bear")) return <TrendingUp className="w-3.5 h-3.5 rotate-180" />;
  if (t.includes("risk") || t.includes("warn")) return <AlertTriangle className="w-3.5 h-3.5" />;
  if (t.includes("fund") || t.includes("theme") || t.includes("order")) return <ShieldCheck className="w-3.5 h-3.5" />;
  return <Lightbulb className="w-3.5 h-3.5" />;
}

function insightTypeColor(type: string): string {
  const t = (type || "").toLowerCase();
  if (t.includes("bull")) return "border-emerald-500/40 text-emerald-400 bg-emerald-500/10";
  if (t.includes("bear")) return "border-rose-500/40 text-rose-400 bg-rose-500/10";
  if (t.includes("risk") || t.includes("warn")) return "border-amber-500/40 text-amber-400 bg-amber-500/10";
  return "border-sky-500/40 text-sky-400 bg-sky-500/10";
}

export default function NewsFeed({ items, sources, loading }: Props) {
  const [activeSource, setActiveSource] = useState<string>("all");
  const [selected, setSelected] = useState<NewsItem | null>(null);
  const [detail, setDetail] = useState<NewsDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const filtered = useMemo(() => {
    if (!items) return [];
    if (activeSource === "all") return items;
    return items.filter((i) => i.source === activeSource);
  }, [items, activeSource]);

  // 点击新闻 -> 拉取详情
  useEffect(() => {
    if (!selected) {
      setDetail(null);
      return;
    }
    setDetailLoading(true);
    fetchNewsDetail(selected.id)
      .then((d) => setDetail(d))
      .catch(() => setDetail(null))
      .finally(() => setDetailLoading(false));
  }, [selected]);

  if (loading || !items) {
    return (
      <div className="card-base p-6">
        <div className="animate-pulse flex flex-col gap-3">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-6 bg-surface-3 rounded" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="card-base overflow-hidden">
      {/* 标题和来源过滤 */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 px-6 py-5 border-b border-surface-4">
        <div className="flex items-center gap-2">
          <Newspaper className="w-4 h-4 text-text-dim" />
          <div>
            <div className="text-lg font-medium text-text">最新新闻流</div>
            <div className="text-xs text-text-muted mt-0.5">
              {filtered.length > 0 ? `显示 ${filtered.length} 条 · 共 ${items.length} 条 · 点击查看详情与解读` : "暂无新闻"}
            </div>
          </div>
        </div>

        {/* 来源过滤 */}
        {sources && sources.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5 text-xs">
            <button
              onClick={() => setActiveSource("all")}
              className={
                "px-2.5 py-1 rounded-md transition-colors " +
                (activeSource === "all"
                  ? "bg-accent text-surface font-medium"
                  : "text-text-muted hover:text-text hover:bg-surface-3")
              }
            >
              全部
            </button>
            {sources.map((src) => {
              const count = items.filter((i) => i.source === src).length;
              return (
                <button
                  key={src}
                  onClick={() => setActiveSource(src)}
                  className={
                    "px-2.5 py-1 rounded-md transition-colors " +
                    (activeSource === src
                      ? "bg-accent text-surface font-medium"
                      : "text-text-muted hover:text-text hover:bg-surface-3")
                  }
                >
                  {prettySource(src)} ({count})
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* 新闻列表 */}
      <div className="divide-y divide-surface-4 max-h-[620px] overflow-y-auto">
        {filtered.length === 0 ? (
          <div className="px-6 py-12 text-center text-text-muted text-sm">暂无匹配的新闻</div>
        ) : (
          filtered.map((n) => (
            <div
              key={n.id}
              onClick={() => setSelected(n)}
              className="px-6 py-4 hover:bg-surface-2 transition-colors cursor-pointer animate-fade-in group"
            >
              {/* 顶部：来源 + 时间 */}
              <div className="flex items-center gap-3 text-xs text-text-dim mb-2">
                <span className="px-2 py-0.5 bg-surface-3 rounded text-text-muted">{prettySource(n.source)}</span>
                <span className="tabular-nums">{formatDate(n.publishedAt)}</span>
                {n.credibility && (
                  <span className="ml-auto text-text-muted text-[11px]">可信度: {n.credibility}</span>
                )}
              </div>

              {/* 标题 */}
              <div className="text-sm text-text leading-relaxed flex items-start gap-2">
                <span className="flex-1 group-hover:text-accent transition-colors">{n.title}</span>
                {n.url && (
                  <a
                    href={n.url}
                    target="_blank"
                    rel="noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="flex-shrink-0 text-text-dim hover:text-accent transition-colors"
                    title="打开原文"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                )}
              </div>

              {/* 摘要（如果有） */}
              {n.summary && (
                <div className="text-xs text-text-muted mt-2 leading-relaxed">{n.summary}</div>
              )}

              {/* 相关股票代码 */}
              {n.tickers && n.tickers.length > 0 && (
                <div className="flex flex-wrap items-center gap-1.5 mt-2.5">
                  {n.tickers.slice(0, 6).map((t) => (
                    <span key={t} className="text-xs px-1.5 py-0.5 bg-surface-3 rounded text-accent border border-surface-4">
                      {t}
                    </span>
                  ))}
                  {n.tickers.length > 6 && (
                    <span className="text-xs text-text-dim">+{n.tickers.length - 6}</span>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* ========= 新闻详情弹窗 ========= */}
      {selected && (
        <div
          className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-start md:items-center justify-center p-4 overflow-y-auto"
          onClick={() => setSelected(null)}
        >
          <div
            className="w-full max-w-2xl my-8 bg-surface-2 border border-surface-4 rounded-xl shadow-2xl animate-fade-in"
            onClick={(e) => e.stopPropagation()}
          >
            {/* 标题栏 */}
            <div className="px-6 py-5 border-b border-surface-4 flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="text-lg font-medium text-text leading-snug">{selected.title}</div>
                <div className="flex items-center gap-2 mt-2 text-xs text-text-dim">
                  <span className="px-2 py-0.5 bg-surface-3 rounded text-text-muted">
                    {prettySource(selected.sourceName || selected.source)}
                  </span>
                  <span className="tabular-nums">{formatDate(selected.publishedAt)}</span>
                  {detail?.credibilityText && (
                    <span className="text-[11px]">· 可信度: {detail.credibilityText}</span>
                  )}
                </div>
              </div>
              <button
                onClick={() => setSelected(null)}
                className="flex-shrink-0 p-1.5 rounded-full hover:bg-surface-4 text-text-dim hover:text-text transition-colors"
                aria-label="关闭"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* 主体 */}
            <div className="px-6 py-5 space-y-5">
              {/* 智能解读（先显示，放在最前面） */}
              {detail && detail.insights && detail.insights.length > 0 && (
                <div className="bg-surface-3 rounded-lg p-4 border border-surface-4">
                  <div className="flex items-center gap-2 text-sm font-medium text-text mb-3">
                    <Lightbulb className="w-4 h-4 text-amber-400" />
                    智能解读
                  </div>
                  <div className="space-y-2">
                    {detail.insights.map((ins, idx) => (
                      <div
                        key={idx}
                        className={`flex items-start gap-2 text-xs text-text-muted leading-relaxed px-3 py-2 rounded-md border ${insightTypeColor(ins.type)}`}
                      >
                        <span className="mt-0.5 flex-shrink-0">{insightIcon(ins.type)}</span>
                        <span className="flex-1">{ins.text}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 加载中 */}
              {detailLoading && (
                <div className="py-10 text-center text-sm text-text-muted animate-pulse">
                  正在加载新闻正文…
                </div>
              )}

              {/* 正文 */}
              {!detailLoading && detail && (
                <div>
                  <div className="text-sm font-medium text-text mb-3">新闻正文</div>
                  {detail.body && detail.body.trim().length > 0 ? (
                    <div className="text-sm text-text-muted leading-relaxed whitespace-pre-wrap bg-surface-3 rounded-lg p-4 max-h-[400px] overflow-y-auto">
                      {detail.body}
                    </div>
                  ) : (
                    <div className="text-sm text-text-muted italic">（该新闻没有可解析的正文，请点击下方链接查看原文）</div>
                  )}
                </div>
              )}

              {/* 兜底：如果后端没返回 detail，则显示摘要 */}
              {!detailLoading && !detail && (
                <div>
                  <div className="text-sm text-text-muted italic">（正在解析，请稍候…如长时间未加载，可直接查看原文链接）</div>
                </div>
              )}

              {/* 相关股票 */}
              {(selected.tickers && selected.tickers.length > 0) || (detail?.tickers && detail.tickers.length > 0) ? (
                <div>
                  <div className="text-sm font-medium text-text mb-2">涉及标的</div>
                  <div className="flex flex-wrap items-center gap-1.5">
                    {(detail?.tickers || selected.tickers || []).slice(0, 10).map((t) => (
                      <span key={t} className="text-xs px-2 py-1 bg-surface-3 rounded text-accent border border-surface-4">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              ) : null}

              {/* 底部操作栏 */}
              <div className="flex items-center justify-between pt-2 border-t border-surface-4">
                <div className="text-xs text-text-muted">
                  {detail?.updatedAt ? `更新于 ${formatDate(detail.updatedAt)}` : ""}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setSelected(null)}
                    className="px-4 py-2 text-xs text-text-muted hover:text-text rounded-md border border-surface-4 hover:bg-surface-3 transition-colors"
                  >
                    关闭
                  </button>
                  {selected.url && (
                    <a
                      href={selected.url}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center gap-1.5 px-4 py-2 text-xs bg-accent text-surface rounded-md hover:opacity-90 transition-opacity"
                    >
                      <ExternalLink className="w-3 h-3" />
                      打开原文
                    </a>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// 为避免 lint 警告，AlertCircle 被保留为将来的扩展
void AlertCircle;
