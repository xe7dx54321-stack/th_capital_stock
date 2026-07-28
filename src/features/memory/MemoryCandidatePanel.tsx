/**
 * 组件：MemoryCandidatePanel（阶段 12-候选记忆审核面板）
 * --------------------------------------------------------------------
 * 功能（小白版）：把 AI 从研究报告里提取出来的"候选记忆"一条一条列出来，
 * 用户可以点【批准 / 拒绝 / 归档】三个按钮。
 * 批准了的就变成正式记忆，下次同标的研究时可以引用。
 *
 * Master Plan 路径：src/features/memory/MemoryCandidatePanel.tsx（严格对齐）
 *
 * 测试清单覆盖：
 *   - 清单 1（6 种制品）：渲染 + 三个按钮
 *   - 清单 4（XSS 安全）：标签/内容用纯文本渲染，不用 innerHTML
 *   - 清单 5（artifact 路径安全）：任何链接 href 都不能包含 "../"（在 React 里用 {String(memory_id)} 内插时转义）
 *   - 清单 8（记忆候选操作）：点击 approve/reject/archive 触发回调
 *   - 冲突标记：conflict_flag=true 的条目显示「冲突待审核」高亮
 */

import React from "react";

export interface MemoryCandidate {
  memory_id: string;
  entity_type?: string;
  entity_id?: string;
  memory_type?: string;
  content?: any;
  status?: "candidate" | "approved" | "rejected" | "archived" | string;
  confidence?: number;
  created_at?: string;
  evidence_links?: { evidence_id: string; relation?: string; created_at?: string }[];
  tags?: string[];
  project_id?: string | null;
  hit_count?: number;
  conflict_flag?: boolean;
}

export interface MemoryCandidatePanelProps {
  candidates?: MemoryCandidate[];
  onApprove?: (memory_id: string) => void;
  onReject?:  (memory_id: string) => void;
  onArchive?: (memory_id: string) => void;
}

/**
 * 安全内插 memory_id：
 *   如果用户恶意把 memory_id 写成 "../../../etc/passwd"，这里不能直接丢到 <a href>
 *   所以我们只在 JSX 里用 React 默认的 textContent 输出（自动 XSS 转义），
 *   并且不渲染任何带 href 的穿越链接。（清单 5）
 */

function contentToText(content: any): string {
  if (content == null) return "";
  if (typeof content === "string") return content;
  try { return JSON.stringify(content, null, 0); } catch { return String(content); }
}

export default function MemoryCandidatePanel(props: MemoryCandidatePanelProps) {
  const { candidates = [], onApprove, onReject, onArchive } = props;

  if (candidates.length === 0) {
    return (
      <section className="memory-candidate-panel artifact-card">
        <header className="card-header">
          <h3>候选记忆审核</h3>
        </header>
        <div className="degraded">暂无待审核候选记忆</div>
      </section>
    );
  }

  return (
    <section className="memory-candidate-panel artifact-card" aria-label="候选记忆审核面板">
      <header className="card-header">
        <div>
          <h3>候选记忆审核</h3>
          <div className="meta">
            共 {candidates.length} 条待审核
            {candidates.some((c) => c.conflict_flag) ? (
              <span className="warn-chip">含冲突记忆（请人工选择或拒绝）</span>
            ) : null}
          </div>
        </div>
      </header>

      <ul className="candidate-list">
        {candidates.map((c) => (
          <li
            className={`candidate-item ${c.conflict_flag ? "has-conflict" : ""}`}
            key={c.memory_id}
          >
            {/* ① 头部：类型 + 实体 + 冲突标记 */}
            <div className="cand-head">
              <span className="mem-type">{c.memory_type || "—"}</span>
              <span className="mem-entity">
                {c.entity_type ? `${c.entity_type}:` : ""}{c.entity_id || "—"}
              </span>
              {c.conflict_flag ? (
                <span className="conflict-flag" role="alert" aria-label="冲突标记">
                  ⚠ 冲突
                </span>
              ) : null}
              {c.confidence != null ? (
                <span className="conf-chip">{(c.confidence * 100).toFixed(0)}%</span>
              ) : null}
              {c.project_id ? <span className="proj-chip">{c.project_id}</span> : null}
            </div>

            {/* ② 正文：记忆内容（用 React 默认文本渲染，不 innerHTML —— 清单 4 安全） */}
            <div className="cand-content">
              {contentToText(c.content) || <span className="degraded">（无内容）</span>}
            </div>

            {/* ③ 标签 + 命中次数 */}
            {c.tags && c.tags.length > 0 ? (
              <div className="cand-tags">
                {c.tags.map((t, i) => (
                  <span className="tag-chip" key={i}>#{t}</span>
                ))}
                {c.hit_count ? <span className="hit-chip">命中 {c.hit_count} 次</span> : null}
              </div>
            ) : c.hit_count ? (
              <div className="cand-tags"><span className="hit-chip">命中 {c.hit_count} 次</span></div>
            ) : null}

            {/* ④ 证据列表 */}
            {c.evidence_links && c.evidence_links.length > 0 ? (
              <details className="cand-evidence">
                <summary>证据链接（{c.evidence_links.length}）</summary>
                <ul>
                  {c.evidence_links.map((e, ei) => (
                    <li key={ei}>
                      {e.relation || "supports"} · {e.evidence_id}
                    </li>
                  ))}
                </ul>
              </details>
            ) : null}

            {/* ⑤ 底部：审核时间 + 三个操作按钮（onApprove/onReject/onArchive） */}
            <div className="cand-footer">
              <span className="cand-time">{c.created_at || ""}</span>
              <div className="cand-actions">
                <button
                  type="button"
                  className="btn approve"
                  onClick={() => onApprove?.(c.memory_id)}
                  aria-label={`批准 ${c.memory_id}`}
                >批准</button>
                <button
                  type="button"
                  className="btn reject"
                  onClick={() => onReject?.(c.memory_id)}
                  aria-label={`拒绝 ${c.memory_id}`}
                >拒绝</button>
                <button
                  type="button"
                  className="btn archive"
                  onClick={() => onArchive?.(c.memory_id)}
                  aria-label={`归档 ${c.memory_id}`}
                >归档</button>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
