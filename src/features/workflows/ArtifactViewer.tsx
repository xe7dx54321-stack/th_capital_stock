import { FileText, Maximize2 } from "lucide-react";
import { useEffect, useState } from "react";

import { artifactUrl, type WorkflowArtifact } from "../../lib/api";

const artifactLabels: Record<string, string> = {
  stock_deep_dive_report: "个股深挖报告",
  daily_brief: "每日研究简报",
  portfolio_review: "组合复盘报告",
  thesis_update: "论点更新报告",
};

function artifactLabel(artifact: WorkflowArtifact) {
  if (/[一-鿿]/.test(artifact.title)) return artifact.title;
  const ticker = String(artifact.metadata?.ticker || "");
  return [ticker, artifactLabels[artifact.artifact_type] || "研究报告"].filter(Boolean).join(" · ");
}

export default function ArtifactViewer({ artifacts }: { artifacts: WorkflowArtifact[] }) {
  const [selected, setSelected] = useState<WorkflowArtifact | null>(artifacts[0] || null);
  const [content, setContent] = useState("");
  const [error, setError] = useState("");

  useEffect(() => { setSelected(artifacts[0] || null); }, [artifacts]);
  useEffect(() => {
    if (!selected) { setContent(""); return; }
    const controller = new AbortController();
    fetch(artifactUrl(selected.artifact_id), { signal: controller.signal })
      .then((response) => { if (!response.ok) throw new Error("报告读取失败"); return response.text(); })
      .then((text) => { setContent(text); setError(""); })
      .catch((reason) => { if (reason.name !== "AbortError") setError(reason.message); });
    return () => controller.abort();
  }, [selected]);

  if (artifacts.length === 0) return null;
  return (
    <section className="artifact-viewer">
      <div className="artifact-bar">
        <span><FileText size={15} /> 研究产物</span>
        <select value={selected?.artifact_id || ""} onChange={(event) => setSelected(artifacts.find((item) => item.artifact_id === event.target.value) || null)} aria-label="选择研究产物">
          {artifacts.map((artifact) => <option value={artifact.artifact_id} key={artifact.artifact_id}>{artifactLabel(artifact)}</option>)}
        </select>
        <a href={selected ? artifactUrl(selected.artifact_id) : "#"} target="_blank" rel="noreferrer" aria-label="打开完整研究产物"><Maximize2 size={14} /></a>
      </div>
      {error ? <p role="alert">{error}</p> : <pre>{content || "正在装订研究报告…"}</pre>}
    </section>
  );
}
