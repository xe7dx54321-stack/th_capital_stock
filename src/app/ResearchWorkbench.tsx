import { Landmark, LayoutDashboard, RefreshCcw } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import ArtifactViewer from "../features/workflows/ArtifactViewer";
import RunTimeline from "../features/workflows/RunTimeline";
import WorkflowLauncher from "../features/workflows/WorkflowLauncher";
import WorkflowSidebar from "../features/workflows/WorkflowSidebar";
import ResearchContextPanel from "../features/research/ResearchContextPanel";
import {
  createWorkflowRun,
  fetchWorkflowEvents,
  fetchWorkflowRun,
  fetchWorkflowRuns,
  fetchWorkflows,
  subscribeWorkflowEvents,
  type WorkflowDefinition,
  type WorkflowEvent,
  type WorkflowRun,
} from "../lib/api";
import "./workbench.css";

const ACTIVE = new Set(["queued", "running", "waiting_review"]);
const LAST_RUN_KEY = "smr.workbench.lastRun";

function mergeEvents(current: WorkflowEvent[], incoming: WorkflowEvent[]) {
  const merged = new Map(current.map((event) => [event.sequence, event]));
  incoming.forEach((event) => merged.set(event.sequence, event));
  return [...merged.values()].sort((a, b) => a.sequence - b.sequence);
}

export default function ResearchWorkbench() {
  const [workflows, setWorkflows] = useState<WorkflowDefinition[]>([]);
  const [runs, setRuns] = useState<WorkflowRun[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [selectedRun, setSelectedRun] = useState<WorkflowRun | null>(null);
  const [events, setEvents] = useState<WorkflowEvent[]>([]);
  const [connection, setConnection] = useState<"live" | "polling" | "idle">("idle");
  const [launching, setLaunching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const latestSequence = useRef(0);

  const loadIndex = useCallback(async () => {
    setLoading(true);
    try {
      const [{ workflows: definitions }, { runs: history }] = await Promise.all([
        fetchWorkflows(), fetchWorkflowRuns(),
      ]);
      setWorkflows(definitions);
      setRuns(history);
      const remembered = localStorage.getItem(LAST_RUN_KEY);
      const next = history.find((run) => run.run_id === remembered)?.run_id || history[0]?.run_id || null;
      setSelectedRunId((current) => current || next);
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "无法读取本地工作流服务");
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { void loadIndex(); }, [loadIndex]);

  useEffect(() => {
    if (!selectedRunId) { setSelectedRun(null); setEvents([]); return; }
    localStorage.setItem(LAST_RUN_KEY, selectedRunId);
    setEvents([]);
    latestSequence.current = 0;
    let stopped = false;
    let pollTimer: ReturnType<typeof setInterval> | undefined;

    const accept = (incoming: WorkflowEvent[]) => {
      if (stopped || incoming.length === 0) return;
      latestSequence.current = Math.max(latestSequence.current, ...incoming.map((event) => event.sequence));
      setEvents((current) => mergeEvents(current, incoming));
      if (incoming.some((event) => ["artifact.created", "run.completed", "run.failed", "run.cancelled", "review.requested"].includes(event.event_type))) {
        void fetchWorkflowRun(selectedRunId).then((run) => {
          if (!stopped) { setSelectedRun(run); setRuns((current) => [run, ...current.filter((item) => item.run_id !== run.run_id)]); }
        });
      }
    };

    const poll = async () => {
      try { accept((await fetchWorkflowEvents(selectedRunId, latestSequence.current)).events); } catch { /* retry on the next interval */ }
    };

    void Promise.all([fetchWorkflowRun(selectedRunId), fetchWorkflowEvents(selectedRunId, 0)])
      .then(([run, result]) => {
        if (stopped) return;
        setSelectedRun(run);
        accept(result.events);
      })
      .catch((reason) => { if (!stopped) setError(reason instanceof Error ? reason.message : "运行记录读取失败"); });

    setConnection("live");
    const closeStream = subscribeWorkflowEvents(selectedRunId, 0, (event) => accept([event]), () => {
      if (stopped || pollTimer) return;
      setConnection("polling");
      void poll();
      pollTimer = setInterval(poll, 1500);
    });

    return () => {
      stopped = true;
      closeStream();
      if (pollTimer) clearInterval(pollTimer);
    };
  }, [selectedRunId]);

  useEffect(() => {
    if (selectedRun && !ACTIVE.has(selectedRun.status) && connection === "live") setConnection("idle");
  }, [selectedRun, connection]);

  async function launch(ticker: string) {
    setLaunching(true);
    setError(null);
    try {
      const run = await createWorkflowRun(
        "stock_deep_dive",
        { ticker, allow_network: false },
        `deep-dive:${ticker}:${new Date().toISOString().slice(0, 16)}`,
      );
      setRuns((current) => [run, ...current.filter((item) => item.run_id !== run.run_id)]);
      setSelectedRunId(run.run_id);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "研究任务创建失败");
    } finally { setLaunching(false); }
  }

  async function refreshSelectedRun() {
    if (!selectedRunId) return;
    try {
      const run = await fetchWorkflowRun(selectedRunId);
      setSelectedRun(run);
      setRuns((current) => [run, ...current.filter((item) => item.run_id !== run.run_id)]);
    } catch { /* the next history refresh can recover this view */ }
  }

  return (
    <main className="workbench-shell">
      <header className="workbench-masthead">
        <Link className="workbench-brand" to="/workbench"><Landmark size={20} /><span>TH CAPITAL</span><em>local research desk</em></Link>
        <nav><Link to="/"><LayoutDashboard size={15} /> 旧版看板</Link><button onClick={() => void loadIndex()} disabled={loading}><RefreshCcw size={14} /> {loading ? "同步中" : "同步档案"}</button></nav>
      </header>
      <div className="workbench-grid">
        <WorkflowSidebar workflows={workflows} runs={runs} selectedRunId={selectedRunId} onSelectRun={setSelectedRunId} />
        <div className="workbench-center">
          <WorkflowLauncher busy={launching} error={error} onLaunch={launch} />
          <RunTimeline run={selectedRun} events={events} connection={connection} />
          <ArtifactViewer artifacts={selectedRun?.artifacts || []} />
        </div>
        <ResearchContextPanel run={selectedRun} onMemoryReviewed={() => void refreshSelectedRun()} />
      </div>
    </main>
  );
}
