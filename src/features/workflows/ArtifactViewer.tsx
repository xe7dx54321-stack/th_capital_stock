import { FileText, Maximize2 } from "lucide-react";
import { useEffect, useState } from "react";

import ValuationModelView from "../../features/artifacts/ValuationModelView";
import ComparisonMatrixView from "../../features/artifacts/ComparisonMatrixView";
import CausalChainView from "../../features/artifacts/CausalChainView";
import SignalPlanView from "../../features/artifacts/SignalPlanView";
import CorrectionDiffView from "../../features/artifacts/CorrectionDiffView";
import MemoryCandidatePanel from "../../features/memory/MemoryCandidatePanel";

import { artifactUrl, reviewMemory, type MemoryDetail, type WorkflowArtifact } from "../../lib/api";

/**
 * 判定一个 study artifact 需要走「多态视图」路由的类型集合。
 * 这些类型会被当作 JSON 拉取，由对应组件接管渲染；
 * 其余类型（markdown / txt 等报告）保留原有 <pre> 文本渲染逻辑。
 */
const POLYMORPHIC_TYPES = new Set<string>([
  "valuation_model",
  "comparison_matrix",
  "causal_chain",
  "signal_plan",
  "correction_diff",
  "memory_candidates",
]);

/**
 * 用中文给 artifact 取一个用户可读的显示名称。
 * 规则优先顺序：
 *   1. 若 title 已含中文，直接用（最精确）；
 *   2. 否则按 type 映射，再拼上 ticker（如果有）。
 */
const artifactLabels: Record<string, string> = {
  stock_deep_dive_report: "个股深挖报告",
  agent_report: "执行审计记录",
  daily_brief: "每日研究简报",
  portfolio_review: "组合复盘报告",
  thesis_update: "论点更新报告",
  valuation_model: "估值模型",
  comparison_matrix: "对标矩阵",
  causal_chain: "因果链分析",
  signal_plan: "监测信号计划",
  correction_diff: "纠错差异对比",
  memory_candidates: "候选记忆待批",
};
function artifactLabel(artifact: WorkflowArtifact) {
  if (/[一-鿿]/.test(artifact.title)) return artifact.title;
  const ticker = String(artifact.metadata?.ticker || "");
  return [ticker, artifactLabels[artifact.artifact_type] || "研究报告"].filter(Boolean).join(" · ");
}

function preferredArtifact(artifacts: WorkflowArtifact[]) {
  return artifacts.find((artifact) => artifact.artifact_type === "stock_deep_dive_report")
    || artifacts.find((artifact) => artifact.artifact_type !== "agent_report")
    || artifacts[0]
    || null;
}

/**
 * 兜底的「异常渲染」：组件抛错不把整个 workbench 搞崩。
 * 生产环境也能看到简单提示，避免白屏给用户造成困惑。
 */
function FallbackView({ error }: { error: unknown }) {
  const message = error instanceof Error ? error.message : String(error);
  return (
    <section className="error-viewer-fallback" role="alert">
      <h4>产物渲染降级提示</h4>
      <p>{message || "多态视图无法解析，请检查后端 JSON 格式。"}</p>
    </section>
  );
}

function MemoryCandidatesArtifactView({ data }: { data: any }) {
  const initial = data?.candidates || (Array.isArray(data) ? data : []);
  const [candidates, setCandidates] = useState(initial);
  const [actionError, setActionError] = useState("");

  useEffect(() => {
    setCandidates(data?.candidates || (Array.isArray(data) ? data : []));
  }, [data]);

  const performReview = async (memoryId: string, action: "approve" | "reject" | "archive") => {
    const actionLabel = action === "approve" ? "批准" : action === "reject" ? "拒绝" : "归档";
    const reason = window.prompt(`请输入${actionLabel}原因（将写入审计日志）`);
    if (!reason?.trim()) return;
    try {
      setActionError("");
      const result = await reviewMemory(memoryId, action, "本地研究者", reason.trim());
      const updated: MemoryDetail = result.memory;
      setCandidates((items: any[]) => items.map((item) => (
        item.memory_id === memoryId ? { ...item, ...updated } : item
      )));
    } catch (error) {
      setActionError(error instanceof Error ? error.message : String(error));
    }
  };

  return (
    <>
      {actionError ? <p role="alert">{actionError}</p> : null}
      <MemoryCandidatePanel
        candidates={candidates}
        onApprove={(id) => { void performReview(id, "approve"); }}
        onReject={(id) => { void performReview(id, "reject"); }}
        onArchive={(id) => { void performReview(id, "archive"); }}
      />
    </>
  );
}

/**
 * 把一个 polymorphic artifact 按 type 路由到具体的 React 组件。
 * 组件抛错时走 FallbackView（ErrorBoundary 的简化版，因为没装）。
 */
function PolymorphicArtifactView({
  artifactType,
  data,
}: {
  artifactType: string;
  data: unknown;
}) {
  try {
    switch (artifactType) {
      case "valuation_model":
        return <ValuationModelView data={data as any} />;
      case "comparison_matrix":
        return <ComparisonMatrixView data={data as any} />;
      case "causal_chain":
        return <CausalChainView data={data as any} />;
      case "signal_plan":
        return <SignalPlanView data={data as any} />;
      case "correction_diff":
        return <CorrectionDiffView data={data as any} />;
      case "memory_candidates":
        return <MemoryCandidatesArtifactView data={data as any} />;
      default:
        return <pre>{JSON.stringify(data, null, 2)}</pre>;
    }
  } catch (e) {
    return <FallbackView error={e} />;
  }
}

export default function ArtifactViewer({ artifacts }: { artifacts: WorkflowArtifact[] }) {
  const [selected, setSelected] = useState<WorkflowArtifact | null>(preferredArtifact(artifacts));
  const [text, setText] = useState<string>("");
  const [parsed, setParsed] = useState<unknown | null>(null);
  const [error, setError] = useState("");

  useEffect(() => { setSelected(preferredArtifact(artifacts)); }, [artifacts]);

  useEffect(() => {
    if (!selected) { setText(""); setParsed(null); return; }
    const isPoly = POLYMORPHIC_TYPES.has(selected.artifact_type);
    const controller = new AbortController();
    fetch(artifactUrl(selected.artifact_id), { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error("报告读取失败");
        return isPoly ? response.json() : response.text();
      })
      .then((payload) => {
        setError("");
        if (isPoly) { setParsed(payload); setText(""); }
        else       { setText(String(payload)); setParsed(null); }
      })
      .catch((reason) => {
        if (reason.name === "AbortError") return;
        // polymorphic 读失败但也许 text 还能看？
        setError(reason.message);
      });
    return () => controller.abort();
  }, [selected]);

  if (artifacts.length === 0) return null;
  const isPoly = selected ? POLYMORPHIC_TYPES.has(selected.artifact_type) : false;

  return (
    <section className="artifact-viewer">
      <div className="artifact-bar">
        <span><FileText size={15} /> 研究产物</span>
        <select
          value={selected?.artifact_id || ""}
          onChange={(event) => setSelected(artifacts.find((item) => item.artifact_id === event.target.value) || null)}
          aria-label="选择研究产物"
        >
          {artifacts.map((artifact) => (
            <option value={artifact.artifact_id} key={artifact.artifact_id}>
              {artifactLabel(artifact)}
            </option>
          ))}
        </select>
        <a
          href={selected ? artifactUrl(selected.artifact_id) : "#"}
          target="_blank"
          rel="noreferrer"
          aria-label="打开完整研究产物"
        ><Maximize2 size={14} /></a>
      </div>
      {error ? (
        <p role="alert">{error}</p>
      ) : isPoly ? (
        parsed ? (
          <PolymorphicArtifactView artifactType={selected!.artifact_type} data={parsed} />
        ) : (
          <p className="loading-hint">正在解析研究产物…</p>
        )
      ) : (
        <pre>{text || "正在装订研究报告…"}</pre>
      )}
    </section>
  );
}
