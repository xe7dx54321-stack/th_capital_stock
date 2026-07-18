/**
 * Agent 工具面板组件
 * 
 * 功能：
 *   1. 展示所有可用的 Agent 工具
 *   2. 支持执行单个工具
 *   3. 显示工具执行结果
 *   4. 支持执行完整研究流程
 * 
 * 小白讲解：
 *   这个面板就像一个"工具箱"——展示所有可用的 AI 工具，
 *   用户可以点击执行任意工具，查看执行结果。
 */

import { useState, useEffect } from "react";
import {
  Wrench,
  Play,
  Loader2,
  CheckCircle2,
  XCircle,
  ChevronDown,
  Sparkles,
  BarChart3,
  Eye,
  Newspaper,
  FileText,
  Layers,
  Compass,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";


/**
 * Agent 工具类型
 */
interface AgentTool {
  toolId: string;
  name: string;
  description: string;
  inputSchema: any;
  requiresInput: boolean;
  workflowId?: string;
}


/**
 * 工具执行结果类型
 */
interface ToolResult {
  success: boolean;
  toolId: string;
  toolName: string;
  type: "workflow" | "api";
  data?: any;
  message?: string;
  error?: string;
}


/**
 * 工具图标映射
 */
const TOOL_ICONS: Record<string, any> = {
  stock_deep_dive: FileText,
  daily_brief: Newspaper,
  portfolio_review: BarChart3,
  thesis_update: Layers,
  value_score: BarChart3,
  opportunity_radar: Compass,
  discovery_candidates: Sparkles,
  market_news: Eye,
};


/**
 * 获取所有工具列表
 */
async function fetchTools(): Promise<AgentTool[]> {
  const response = await fetch("/api/agent/tools");
  if (!response.ok) throw new Error("获取工具列表失败");
  const data = await response.json();
  return data.tools;
}


/**
 * 执行工具
 */
async function executeTool(toolId: string, input: any): Promise<ToolResult> {
  const response = await fetch("/api/agent/execute", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ toolId, input }),
  });
  if (!response.ok) throw new Error("工具执行失败");
  return response.json();
}


/**
 * 执行研究流程
 */
async function executeResearchFlow(ticker: string): Promise<any> {
  const response = await fetch("/api/agent/research-flow", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ticker }),
  });
  if (!response.ok) throw new Error("研究流程执行失败");
  return response.json();
}


/**
 * 工具卡片组件
 */
function ToolCard({ tool, onExecute, executing, result }: {
  tool: AgentTool;
  onExecute: (input: any) => void;
  executing: boolean;
  result: ToolResult | null;
}) {
  const [inputValue, setInputValue] = useState("");
  const [showResult, setShowResult] = useState(false);
  const Icon = TOOL_ICONS[tool.toolId] || Wrench;

  return (
    <article className="agent-tool-card">
      <header className="agent-tool-header">
        <div className="agent-tool-icon"><Icon size={16} /></div>
        <div className="agent-tool-info">
          <h4>{tool.name}</h4>
          <p>{tool.description}</p>
        </div>
      </header>

      {tool.requiresInput && (
        <div className="agent-tool-input">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="输入股票代码，如 300308.SZ"
            disabled={executing}
          />
        </div>
      )}

      <footer className="agent-tool-footer">
        <button
          className="agent-tool-btn"
          onClick={() => onExecute(tool.requiresInput ? { ticker: inputValue } : {})}
          disabled={executing || (tool.requiresInput && !inputValue.trim())}
        >
          {executing ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
          {executing ? "执行中" : "执行"}
        </button>

        {result && (
          <button
            className="agent-tool-toggle"
            onClick={() => setShowResult(!showResult)}
          >
            <span className={result.success ? "is-success" : "is-error"}>
              {result.success ? <CheckCircle2 size={12} /> : <XCircle size={12} />}
              {result.success ? "成功" : "失败"}
            </span>
            <ChevronDown size={12} className={showResult ? "rotate-180" : ""} />
          </button>
        )}
      </footer>

      {showResult && result && (
        <div className="agent-tool-result">
          {result.message && <p className="agent-tool-msg">{result.message}</p>}
          {result.error && <p className="agent-tool-err">{result.error}</p>}
          {result.data && (
            <pre className="agent-tool-data">
              {JSON.stringify(result.data, null, 2).slice(0, 500)}
              {JSON.stringify(result.data, null, 2).length > 500 ? "..." : ""}
            </pre>
          )}
        </div>
      )}
    </article>
  );
}


/**
 * 主组件
 */
export default function AgentPanel() {
  const [tools, setTools] = useState<AgentTool[]>([]);
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, ToolResult>>({});
  const [flowTicker, setFlowTicker] = useState("");
  const [flowRunning, setFlowRunning] = useState(false);
  const [flowResult, setFlowResult] = useState<any>(null);

  useEffect(() => {
    fetchTools()
      .then(setTools)
      .catch((e) => console.error(e))
      .finally(() => setLoading(false));
  }, []);

  /**
   * 执行工具
   */
  async function handleExecute(toolId: string, input: any) {
    setExecuting(toolId);
    try {
      const result = await executeTool(toolId, input);
      setResults((prev) => ({ ...prev, [toolId]: result }));
    } catch (e) {
      setResults((prev) => ({
        ...prev,
        [toolId]: {
          success: false,
          toolId,
          toolName: toolId,
          type: "api",
          error: e instanceof Error ? e.message : "执行失败",
        },
      }));
    } finally {
      setExecuting(null);
    }
  }

  /**
   * 执行完整研究流程
   */
  async function handleFlow() {
    if (!flowTicker.trim()) return;
    setFlowRunning(true);
    try {
      const result = await executeResearchFlow(flowTicker.trim());
      setFlowResult(result);
    } catch (e) {
      setFlowResult({
        success: false,
        error: e instanceof Error ? e.message : "执行失败",
      });
    } finally {
      setFlowRunning(false);
    }
  }

  if (loading) {
    return (
      <div className="agent-panel-loading">
        <Loader2 size={20} className="animate-spin" />
        <span>加载工具列表...</span>
      </div>
    );
  }

  return (
    <div className="agent-panel">
      <div className="agent-panel-header">
        <Wrench size={18} />
        <h2>Agent 工具箱</h2>
        <span className="agent-panel-count">{tools.length} 个工具</span>
      </div>

      {/* 完整研究流程 */}
      <div className="agent-flow">
        <div className="agent-flow-label">
          <Sparkles size={14} />
          <span>一键完整研究流程</span>
        </div>
        <div className="agent-flow-form">
          <input
            type="text"
            value={flowTicker}
            onChange={(e) => setFlowTicker(e.target.value)}
            placeholder="输入股票代码，如 300308.SZ"
            disabled={flowRunning}
          />
          <button
            onClick={handleFlow}
            disabled={flowRunning || !flowTicker.trim()}
          >
            {flowRunning ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
            {flowRunning ? "执行中" : "启动流程"}
          </button>
        </div>
        {flowResult && (
          <div className="agent-flow-result">
            {flowResult.success ? (
              <p className="is-success">✅ {flowResult.summary}</p>
            ) : (
              <p className="is-error">❌ {flowResult.error || "流程失败"}</p>
            )}
            {flowResult.steps && (
              <ol className="agent-flow-steps">
                {flowResult.steps.map((step: any, i: number) => (
                  <li key={i} className={`is-${step.status}`}>
                    <span className="agent-flow-step-name">{step.step}</span>
                    <span className="agent-flow-step-msg">{step.message}</span>
                  </li>
                ))}
              </ol>
            )}
          </div>
        )}
      </div>

      {/* 工具网格 */}
      <div className="agent-tool-grid">
        {tools.map((tool) => (
          <ToolCard
            key={tool.toolId}
            tool={tool}
            onExecute={(input) => handleExecute(tool.toolId, input)}
            executing={executing === tool.toolId}
            result={results[tool.toolId] || null}
          />
        ))}
      </div>
    </div>
  );
}
