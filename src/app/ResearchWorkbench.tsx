/**
 * 研究工作台主页面
 *
 * 布局：
 *   - 顶部：导航栏
 *   - 主体：ChatPanel（内含左侧会话侧边栏 + 中部工作区）
 *
 * 小白讲解：
 *   之前的页面有左侧"运行档案"、右侧"研究产物"两个侧边栏，
 *   现在都删掉了，只保留中间的聊天工作区。
 *   会话管理（新建、历史列表）在 ChatPanel 内部的左侧侧边栏里。
 */

import {
  BadgeCheck,
  Bot,
  CircleDot,
  Database,
  FileStack,
  Globe,
  LayoutDashboard,
  RefreshCcw,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import ChatPanel from "../features/chat/ChatPanel";
import { fetchWorkflowRuns, type WorkflowRun } from "../lib/api";
import "./workbench.css";

const LAST_RUN_KEY = "smr.workbench.lastRun";

export default function ResearchWorkbench() {
  const [runs, setRuns] = useState<WorkflowRun[]>([]);
  const [loading, setLoading] = useState(true);

  /**
   * 加载工作流运行历史（仅用于顶部统计数字）
   */
  const loadIndex = useCallback(async () => {
    setLoading(true);
    try {
      const { runs: history } = await fetchWorkflowRuns();
      setRuns(history);
    } catch {
      /* 统计数据加载失败不影响聊天功能 */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadIndex();
    // 清理旧的 localStorage 缓存
    localStorage.removeItem(LAST_RUN_KEY);
  }, [loadIndex]);

  const completedRuns = runs.filter((run) => run.status === "completed").length;
  const pendingReviews = runs.filter((run) => run.status === "waiting_review").length;

  return (
    <main className="workbench-shell">
      <header className="workbench-masthead">
        <Link className="workbench-brand" to="/">
          <span className="brand-mark" aria-hidden="true"><span /></span>
          <strong>同行资本</strong>
          <em>个人研究工作台</em>
        </Link>
        <nav>
          <span className="today-status"><CircleDot size={14} /> 今日研究</span>
          <Link to="/agent"><Bot size={15} /> Agent & 成长</Link>
          <Link to="/mapping"><Globe size={15} /> 海外映射</Link>
          <Link to="/legacy/dashboard"><LayoutDashboard size={15} /> 经典看板</Link>
          <button onClick={() => void loadIndex()} disabled={loading}>
            <RefreshCcw className={loading ? "spin" : ""} size={14} /> {loading ? "同步中" : "同步档案"}
          </button>
        </nav>
      </header>
      <div className="workbench-grid">
        <main className="workbench-main">
          <section className="overview-strip" aria-label="研究概览">
            <article><span className="overview-icon is-blue"><FileStack size={18} /></span><div><small>研究总数</small><strong>{runs.length}</strong></div></article>
            <article><span className="overview-icon is-amber"><CircleDot size={18} /></span><div><small>待审核</small><strong>{pendingReviews}</strong></div></article>
            <article><span className="overview-icon is-green"><BadgeCheck size={18} /></span><div><small>已完成</small><strong>{completedRuns}</strong></div></article>
            <article><span className="overview-icon is-slate"><Database size={18} /></span><div><small>数据边界</small><strong className="boundary-value">本地优先</strong></div></article>
          </section>
          <ChatPanel />
        </main>
      </div>
    </main>
  );
}
