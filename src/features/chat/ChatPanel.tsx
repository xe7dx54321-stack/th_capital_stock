/**
 * ChatBot 聊天界面组件
 *
 * 功能：
 *   1:1 复现 Codex / Trae 的聊天界面设计
 *   - 左侧：会话列表侧边栏（新建对话 + 历史会话列表）
 *   - 中间：根据状态显示不同页面
 *     · 空状态（没有对话）：欢迎页，引导语 + 大输入框 + 推荐任务卡片
 *     · 工作状态（有对话）：聊天消息流 + 执行过程 + 结果展示 + 底部输入框
 *   - 支持新建会话、切换会话、恢复历史消息
 *   - 支持 Markdown 格式渲染回复内容
 *
 * 小白讲解：
 *   就像 Codex 或 Trae 打开时的体验：
 *   - 第一次进入，中间区域显示"今天想分析点什么？"，下面有输入框和几个推荐任务
 *   - 输入问题点发送后，中间区域切换成聊天界面，展示分析过程和结果
 *   - 左边始终是会话列表，可以随时切换或新建
 */

import { useState, useRef, useEffect } from "react";
import {
  Send, Bot, User, Loader2, Trash2,
  TrendingUp, Newspaper, BarChart3, Target,
  ArrowUp, Sparkles, Activity, FileText, ShieldCheck, ChevronDown,
  CheckCircle2, AlertTriangle, Circle, XCircle,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { parseApiDate } from "../../lib/datetime";
import {
  fetchSessions, createSession, fetchSessionMessages, deleteSession,
  type ChatSession, type SessionMessage,
} from "../../lib/api";
import SessionSidebar from "./SessionSidebar";


/**
 * 聊天消息类型
 */
interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  intent?: string;
  execution?: ResearchExecutionDetails;
}

interface ResearchExecutionDetails {
  taskType: string;
  runId?: string;
  governedRunId?: string | null;
  completedSteps: number;
  totalSteps: number;
  health?: WorkflowResponse["data"]["dataHealth"];
  citation?: WorkflowResponse["data"]["citationValidation"];
  artifacts: NonNullable<WorkflowResponse["artifacts"]>;
  researchExecution?: ResearchExecutionSummary | null;
}

interface ResearchStage {
  id: string;
  label: string;
  status: "pending" | "running" | "completed" | "warning" | "failed";
  message: string;
  startedAt?: string | null;
  completedAt?: string | null;
}

interface ResearchStageGroup {
  id: string;
  label: string;
  completedStages: number;
  totalStages: number;
  stages: ResearchStage[];
}

interface ResearchExecutionSummary {
  status: "running" | "completed" | "warning" | "failed";
  completedStages: number;
  totalStages: number;
  warningStages: number;
  failedStages: number;
  groups: ResearchStageGroup[];
}


/**
 * Workflow 回复类型
 */
interface WorkflowResponse {
  run_id?: string;
  governed_run_id?: string | null;
  taskType: string;
  status: string;
  response: string;
  data: Record<string, unknown> & {
    dataHealth?: {
      status: "healthy" | "warning" | "blocked";
      can_claim_current: boolean;
      total_evidence: number;
      fresh_current_evidence: number;
    };
    citationValidation?: {
      status: "passed" | "warning" | "not_applicable";
      coverage: number;
      unknown_citation_ids: string[];
      missing_citation_claims: unknown[];
      current_claim_violations: unknown[];
    };
    researchExecution?: ResearchExecutionSummary | null;
  };
  executionHistory: Array<{ stepId: string; message: string; data?: unknown }>;
  workflowSummary: { totalSteps: number; completedSteps: number };
  extractedMemories?: Array<{ title: string; content: string; category: string; confidence: number }>;
  artifacts?: Array<{ artifact_id: string; artifact_type?: string; title: string; mime_type: string }>;
}

interface ResearchProgressEvent {
  run_id: string;
  workflow_id: string;
  status: ResearchExecutionSummary["status"];
  run_status: string;
  last_sequence: number;
  researchExecution: ResearchExecutionSummary;
}


/**
 * 推荐任务列表
 *
 * 空状态欢迎页显示的推荐任务卡片
 * 参考 Codex/Trae 的设计：给用户几个常见选项降低使用门槛
 */
const suggestedTasks = [
  {
    icon: BarChart3,
    title: "今日A股复盘",
    description: "扫描涨跌幅榜、资金流向，生成今日市场总结",
    message: "帮我做一份今天的A股复盘",
    color: "from-blue-500 to-cyan-500",
  },
  {
    icon: TrendingUp,
    title: "涨跌幅归因分析",
    description: "用涨跌幅榜与巨潮公告交叉核对，不猜测因果",
    message: "做一份今天涨跌幅前10的归因分析",
    color: "from-purple-500 to-pink-500",
  },
  {
    icon: Target,
    title: "机会雷达扫描",
    description: "全市场扫描放量异动、价格突破、估值极端等信号",
    message: "今天有哪些机会",
    color: "from-orange-500 to-red-500",
  },
  {
    icon: Newspaper,
    title: "最新市场新闻",
    description: "获取最新的财经新闻和市场动态",
    message: "最近有什么重要的市场新闻",
    color: "from-green-500 to-emerald-500",
  },
];


/**
 * 发送聊天请求（使用 Workflow 引擎）
 *
 * 参数：
 *   message: 用户消息
 *   sessionId: 当前会话 ID（可选，传入后消息会保存到对应会话）
 *
 * 返回：
 *   Promise<WorkflowResponse>: Workflow 响应
 */
async function sendChatRequest(message: string, sessionId?: string, chatHistory?: Array<{role: string; content: string}>): Promise<WorkflowResponse> {
  const body: Record<string, unknown> = { message };
  if (sessionId) body.sessionId = sessionId;
  // 传递对话历史，让后端知道之前的上下文
  if (chatHistory && chatHistory.length > 0) {
    body.conversationContext = { chatHistory };
  }

  const response = await fetch("/api/chat/workflow", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    let details: { error?: string; run_id?: string } = {};
    try {
      details = await response.json();
    } catch {
      // 非 JSON 错误响应保留通用提示。
    }
    const runHint = details.run_id ? `（任务 ${details.run_id}）` : "";
    throw new Error(`${details.error || "聊天服务请求失败"}${runHint}`);
  }

  return response.json();
}

export async function sendChatRequestStream(
  message: string,
  sessionId: string | undefined,
  chatHistory: Array<{role: string; content: string}> | undefined,
  onProgress: (progress: ResearchProgressEvent) => void,
): Promise<WorkflowResponse> {
  const body: Record<string, unknown> = { message };
  if (sessionId) body.sessionId = sessionId;
  if (chatHistory && chatHistory.length > 0) body.conversationContext = { chatHistory };

  const response = await fetch("/api/chat/workflow/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify(body),
  });

  if (response.status === 404 || response.status === 405 || !response.body) {
    return sendChatRequest(message, sessionId, chatHistory);
  }
  if (!response.ok) {
    let details: { error?: string } = {};
    try {
      details = await response.json();
    } catch {
      // 保留通用错误。
    }
    throw new Error(details.error || "聊天服务请求失败");
  }
  if (!response.headers.get("content-type")?.includes("text/event-stream")) {
    return response.json();
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let result: WorkflowResponse | null = null;
  let streamError: Error | null = null;

  const consumeFrame = (frame: string) => {
    const lines = frame.split(/\r?\n/);
    let eventName = "message";
    const dataLines: string[] = [];
    for (const line of lines) {
      if (line.startsWith(":")) continue;
      if (line.startsWith("event:")) eventName = line.slice(6).trim();
      if (line.startsWith("data:")) dataLines.push(line.slice(5).trimStart());
    }
    if (dataLines.length === 0) return;
    const payload = JSON.parse(dataLines.join("\n")) as Record<string, unknown>;
    if (eventName === "research_progress") {
      onProgress(payload as unknown as ResearchProgressEvent);
    } else if (eventName === "result") {
      result = payload as unknown as WorkflowResponse;
    } else if (eventName === "error") {
      const runHint = payload.run_id ? `（任务 ${String(payload.run_id)}）` : "";
      streamError = new Error(`${String(payload.error || "研究任务执行失败")}${runHint}`);
    }
  };

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value, { stream: !done });
    const frames = buffer.split(/\r?\n\r?\n/);
    buffer = frames.pop() || "";
    for (const frame of frames) {
      if (frame.trim()) consumeFrame(frame);
    }
    if (done) break;
  }
  if (buffer.trim()) consumeFrame(buffer);
  if (streamError) throw streamError;
  if (!result) throw new Error("研究流已结束，但没有收到最终结果");
  return result;
}


/**
 * 格式化时间显示（HH:MM）
 */
function formatTime(date: Date): string {
  const hours = date.getHours().toString().padStart(2, "0");
  const minutes = date.getMinutes().toString().padStart(2, "0");
  return `${hours}:${minutes}`;
}


/**
 * 意图标签映射
 *
 * 把后端的英文意图标识转换为中文显示
 */
function getIntentLabel(intent: string): string {
  const labels: Record<string, string> = {
    stock_analysis: "股票分析",
    value_score: "价值评分",
    opportunity_radar: "机会雷达",
    discovery_candidates: "新发现",
    market_news: "市场新闻",
    market_attribution: "涨跌幅归因",
    help: "帮助",
    unknown: "未知",
    stock_deep_analysis: "深度分析",
    opportunity_scan: "机会扫描",
    discovery: "新发现",
    portfolio_review: "组合回顾",
    daily_brief: "每日简报",
    thesis_update: "投资论更新",
    risk_analysis: "风险分析",
    competitor_analysis: "竞争对手分析",
    trend_analysis: "趋势分析",
    chat: "自由对话",
  };
  return labels[intent] || intent;
}


/**
 * 用户消息气泡组件
 */
function UserMessageBubble({ content, timestamp }: { content: string; timestamp: Date }) {
  return (
    <div className="flex justify-end mb-4">
      <div className="flex items-start gap-2 max-w-[70%] flex-row-reverse">
        <div className="flex flex-col items-center flex-shrink-0">
          <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
            <User size={16} className="text-white" />
          </div>
          <span className="text-xs text-gray-400 mt-1">{formatTime(timestamp)}</span>
        </div>
        <div className="bg-blue-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 shadow-md">
          <p className="text-sm whitespace-pre-wrap">{content}</p>
        </div>
      </div>
    </div>
  );
}


/**
 * AI 消息气泡组件（含 Markdown 渲染）
 */
function ResearchExecutionPanel({ details }: { details: ResearchExecutionDetails }) {
  const reportArtifacts = details.artifacts.filter((item) =>
    ["stock_deep_dive_report", "stock_research_packet_v2", "stock_deep_dive_audit"].includes(item.artifact_type || "")
  );
  const passed = details.citation?.status === "passed";
  const research = details.researchExecution;
  const isRunning = research?.status === "running";
  const [isExpanded, setIsExpanded] = useState(Boolean(isRunning));
  const progressText = research
    ? `${research.completedStages}/${research.totalStages} 阶段完成`
    : `${details.completedSteps}/${details.totalSteps} 步完成`;
  const stageIcon = (status: ResearchStage["status"]) => {
    if (status === "completed") return <CheckCircle2 size={15} className="text-emerald-600" />;
    if (status === "warning") return <AlertTriangle size={15} className="text-amber-600" />;
    if (status === "failed") return <XCircle size={15} className="text-rose-600" />;
    if (status === "running") return <Loader2 size={15} className="animate-spin text-blue-600" />;
    return <Circle size={15} className="text-slate-300" />;
  };
  return (
    <details
      open={isExpanded}
      onToggle={(event) => setIsExpanded(event.currentTarget.open)}
      className="group mt-8 overflow-hidden rounded-2xl border border-slate-200 bg-slate-50/80"
    >
      <summary className="flex cursor-pointer list-none items-center justify-between gap-4 px-5 py-4 text-sm text-slate-700 marker:hidden">
        <span className="flex items-center gap-3 font-medium">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-white text-slate-700 shadow-sm ring-1 ring-slate-200">
            <Activity size={16} />
          </span>
          研究运行与产物
        </span>
        <span className="flex items-center gap-3 text-xs text-slate-500">
          {progressText}
          <ChevronDown size={15} className="transition-transform duration-200 group-open:rotate-180" />
        </span>
      </summary>
      <div className="border-t border-slate-200 px-5 py-5">
        <div className="grid gap-3 sm:grid-cols-4">
          <div className="rounded-xl bg-white p-3 ring-1 ring-slate-200">
            <div className="text-[11px] tracking-wide text-slate-400">任务类型</div>
            <div className="mt-1 text-sm font-semibold text-slate-800">{getIntentLabel(details.taskType)}</div>
          </div>
          <div className="rounded-xl bg-white p-3 ring-1 ring-slate-200">
            <div className="text-[11px] tracking-wide text-slate-400">报告校验</div>
            <div className="mt-1 flex items-center gap-1.5 text-sm font-semibold text-slate-800">
              {isRunning
                ? <Loader2 size={14} className="animate-spin text-blue-600" />
                : <ShieldCheck size={14} className={passed ? "text-emerald-600" : "text-amber-600"} />}
              {isRunning ? "等待最终复核" : passed ? "引用与结构通过" : "已降级，建议复核"}
            </div>
          </div>
          <div className="rounded-xl bg-white p-3 ring-1 ring-slate-200">
            <div className="text-[11px] tracking-wide text-slate-400">研究覆盖</div>
            <div className="mt-1 text-sm font-semibold text-slate-800">
              {isRunning ? "资料收集中" : details.health?.status === "healthy" ? "完整" : "部分数据受限"}
            </div>
          </div>
          <div className="rounded-xl bg-white p-3 ring-1 ring-slate-200">
            <div className="text-[11px] tracking-wide text-slate-400">意图编排</div>
            <div className="mt-1 text-sm font-semibold text-slate-800">
              {isRunning ? "已进入深研流程" : `${details.completedSteps}/${details.totalSteps} 步完成`}
            </div>
          </div>
        </div>
        {research && research.groups.length > 0 && (
          <div className="mt-5 space-y-3" data-testid="research-stage-timeline">
            <div className="flex items-center justify-between">
              <div className="text-sm font-semibold text-slate-800">研究主流程</div>
              <div className="text-xs text-slate-500">
                {research.completedStages}/{research.totalStages} 阶段完成
                {research.warningStages > 0 ? ` · ${research.warningStages} 项降级` : ""}
              </div>
            </div>
            <div className="h-1.5 overflow-hidden rounded-full bg-slate-200">
              <div
                className="h-full rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 transition-[width] duration-500"
                style={{ width: `${Math.round((research.completedStages / Math.max(1, research.totalStages)) * 100)}%` }}
              />
            </div>
            {research.groups.map((group) => (
              <div key={group.id} className="overflow-hidden rounded-xl bg-white ring-1 ring-slate-200">
                <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50/70 px-4 py-2.5">
                  <span className="text-xs font-semibold text-slate-700">{group.label}</span>
                  <span className="text-[11px] text-slate-400">{group.completedStages}/{group.totalStages}</span>
                </div>
                <div className="divide-y divide-slate-100">
                  {group.stages.map((stage) => (
                    <div key={stage.id} className="flex items-start gap-3 px-4 py-3">
                      <span className="mt-0.5 flex-none">{stageIcon(stage.status)}</span>
                      <div className="min-w-0 flex-1">
                        <div className="text-xs font-medium text-slate-700">{stage.label}</div>
                        {stage.message && <div className="mt-0.5 truncate text-[11px] text-slate-400">{stage.message}</div>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
        {reportArtifacts.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            {reportArtifacts.map((item) => (
              <a
                key={item.artifact_id}
                href={`/api/artifacts/${encodeURIComponent(item.artifact_id)}`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 rounded-full bg-white px-3 py-2 text-xs font-medium text-slate-700 ring-1 ring-slate-200 transition hover:-translate-y-0.5 hover:text-blue-700 hover:shadow-sm"
              >
                <FileText size={13} /> {item.title || "研究产物"}
              </a>
            ))}
          </div>
        )}
        {(details.runId || details.governedRunId) && (
          <div className="mt-4 font-mono text-[10px] leading-5 text-slate-400">
            {details.governedRunId && <div>研究任务 {details.governedRunId}</div>}
            {details.runId && <div>会话任务 {details.runId}</div>}
          </div>
        )}
      </div>
    </details>
  );
}

function AssistantMessageBubble({ content, timestamp, intent, execution }: { content: string; timestamp: Date; intent?: string; execution?: ResearchExecutionDetails }) {
  return (
    <div className="mb-8 flex justify-start">
      <div className="flex w-full max-w-[1120px] items-start gap-3">
        <div className="flex flex-col items-center flex-shrink-0">
          <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-full flex items-center justify-center">
            <Bot size={16} className="text-white" />
          </div>
          <span className="text-xs text-gray-400 mt-1">{formatTime(timestamp)}</span>
        </div>
        <article className="min-w-0 flex-1 rounded-[26px] rounded-tl-md border border-slate-200 bg-white px-6 py-6 text-slate-900 shadow-[0_16px_50px_-32px_rgba(15,23,42,0.35)] md:px-10 md:py-9">
          {intent && intent !== "help" && (
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">
              <span className="bg-gray-200 dark:bg-gray-700 px-2 py-0.5 rounded-full">
                {getIntentLabel(intent)}
              </span>
            </div>
          )}
          <div className="text-[15px] leading-7 text-slate-700">
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={{
              h1: ({ children }) => <h1 className="mb-6 mt-1 border-b border-slate-200 pb-5 text-2xl font-bold tracking-tight text-slate-950 md:text-3xl">{children}</h1>,
              h2: ({ children }) => <h2 className="mb-3 mt-10 text-xl font-bold tracking-tight text-slate-950">{children}</h2>,
              h3: ({ children }) => <h3 className="mb-2 mt-6 text-base font-bold text-slate-900">{children}</h3>,
              ul: ({ children }) => <ul className="my-3 list-disc space-y-1 pl-6 marker:text-blue-600">{children}</ul>,
              ol: ({ children }) => <ol className="my-3 list-decimal space-y-1 pl-6 marker:font-semibold marker:text-blue-700">{children}</ol>,
              li: ({ children }) => <li>{children}</li>,
              strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
              table: ({ children }) => <div className="my-5 overflow-x-auto rounded-xl border border-slate-200"><table className="w-full text-xs">{children}</table></div>,
              th: ({ children }) => <th className="border-b border-slate-200 bg-slate-50 px-3 py-2.5 text-left font-semibold text-slate-700">{children}</th>,
              td: ({ children }) => <td className="border-b border-slate-100 px-3 py-2.5 text-left text-slate-600">{children}</td>,
              p: ({ children }) => <p className="mb-3">{children}</p>,
              blockquote: ({ children }) => <blockquote className="my-5 border-l-2 border-blue-500 bg-blue-50/70 px-4 py-3 text-slate-600">{children}</blockquote>,
            }}>
              {content}
            </ReactMarkdown>
          </div>
          {execution && <ResearchExecutionPanel details={execution} />}
        </article>
      </div>
    </div>
  );
}


/**
 * 加载中状态组件（AI 正在思考）
 */
function LoadingIndicator() {
  return (
    <div className="flex justify-start mb-4">
      <div className="flex items-start gap-2 max-w-[85%]">
        <div className="flex flex-col items-center flex-shrink-0">
          <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-full flex items-center justify-center">
            <Bot size={16} className="text-white" />
          </div>
        </div>
        <div className="bg-gray-100 dark:bg-gray-800 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
          <div className="flex items-center gap-2">
            <Loader2 size={16} className="text-gray-500 animate-spin" />
            <span className="text-sm text-gray-500">正在思考中...</span>
          </div>
        </div>
      </div>
    </div>
  );
}


/**
 * 将 session 消息记录转换为前端 ChatMessage 数组
 *
 * 参数：
 *   messages: 后端返回的 session 消息列表（按时间正序）
 * 返回：
 *   ChatMessage 数组
 */
function sessionMessagesToChatMessages(messages: SessionMessage[]): ChatMessage[] {
  return messages.map((msg) => ({
    id: `session-${msg.id}`,
    role: msg.role,
    content: msg.content,
    timestamp: parseApiDate(msg.created_at),
    intent: msg.intent || undefined,
  }));
}


/**
 * 判断当前是否处于"空状态"
 *
 * 空状态 = 没有任何用户消息（只有欢迎语或完全为空）
 * 此时显示欢迎页而非聊天界面
 *
 * 参数：
 *   messages: 当前消息列表
 * 返回：
 *   true = 显示欢迎页, false = 显示聊天工作区
 */
function isEmptyState(messages: ChatMessage[]): boolean {
  // 如果有用户消息，就不是空状态
  return !messages.some(msg => msg.role === "user");
}


/**
 * 主聊天组件
 *
 * 1:1 复现 Codex / Trae 的聊天界面设计
 */
export default function ChatPanel() {
  // === 聊天状态 ===
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isStreamingProgress, setIsStreamingProgress] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const welcomeInputRef = useRef<HTMLTextAreaElement>(null);

  // === Session 管理状态 ===
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [sidebarRefreshKey, setSidebarRefreshKey] = useState(0);


  /**
   * 组件初始化时加载会话列表
   *
   * 如果有会话，自动选中最近的一个
   * 如果没有会话，保持空状态显示欢迎页
   */
  useEffect(() => {
    async function initSessions() {
      try {
        const result = await fetchSessions("active");
        if (result.success && result.sessions.length > 0) {
          // 自动选中第一个会话（最新的）
          await selectSession(result.sessions[0]);
        }
      } catch (err) {
        console.warn("加载会话列表失败:", err);
      }
    }
    initSessions();
  }, []);


  /**
   * 空状态时自动聚焦欢迎页输入框
   */
  useEffect(() => {
    if (isEmptyState(messages) && !isLoading) {
      welcomeInputRef.current?.focus();
    }
  }, [messages, isLoading]);


  /**
   * 滚动到最新消息
   */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);


  /**
   * 切换会话
   *
   * 从后端加载该会话的所有消息，替换当前显示的消息列表
   */
  async function selectSession(session: ChatSession) {
    setCurrentSessionId(session.id);
    try {
      const result = await fetchSessionMessages(session.id);
      if (result.success && result.messages.length > 0) {
        setMessages(sessionMessagesToChatMessages(result.messages));
      } else {
        // 空会话，显示欢迎页
        setMessages([]);
      }
    } catch (err) {
      console.error("加载会话消息失败:", err);
    }
  }


  /**
   * 新建会话
   *
   * 创建新会话后自动切换到空状态欢迎页
   */
  function handleCreateSession(session: ChatSession) {
    setCurrentSessionId(session.id);
    setMessages([]);
    setSidebarRefreshKey(k => k + 1);
  }


  /**
   * 触发侧边栏刷新
   */
  function refreshSidebar() {
    setSidebarRefreshKey(k => k + 1);
  }


  /**
   * 发送消息（核心方法）
   *
   * 1. 如果没有当前会话，自动创建一个
   * 2. 添加用户消息到界面
   * 3. 调用后端 Workflow 引擎获取 AI 回复
   * 4. 添加 AI 回复到界面
   * 5. 刷新侧边栏（更新标题、消息数等）
   *
   * 参数：
   *   text: 要发送的消息内容（如果不传，使用 inputValue）
   */
  async function handleSend(text?: string) {
    const message = (text || inputValue).trim();
    if (!message || isLoading) return;

    // 如果没有当前会话，自动创建一个
    let sessionId = currentSessionId;
    if (!sessionId) {
      try {
        const result = await createSession();
        if (result.success && result.session) {
          sessionId = result.session.id;
          setCurrentSessionId(sessionId);
        }
      } catch (err) {
        console.warn("自动创建会话失败:", err);
      }
    }

    // 添加用户消息
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: message,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);
    setIsStreamingProgress(false);
    const streamingMessageId = `stream-${Date.now()}`;
    let progressMessageCreated = false;

    try {
      // 构建对话历史：把当前 session 中已有的消息传给后端
      // 只传最近 10 条，避免 prompt 太长超出 token 限制
      // 修复：助手消息保留 2000 字（之前 500 字太短，报告被裁剪后后端无法理解上下文）
      const chatHistory = messages.slice(-10).map(msg => ({
        role: msg.role,
        content: msg.role === "user" ? msg.content.substring(0, 300) : msg.content.substring(0, 2000),
      }));

      const response = await sendChatRequestStream(
        message,
        sessionId || undefined,
        chatHistory,
        (progress) => {
          progressMessageCreated = true;
          setIsStreamingProgress(true);
          const progressMessage: ChatMessage = {
            id: streamingMessageId,
            role: "assistant",
            content: "正在执行个股深度研究。研究报告完成后将在这里展开。",
            timestamp: new Date(),
            intent: "stock_deep_analysis",
            execution: {
              taskType: "stock_deep_analysis",
              governedRunId: progress.run_id,
              completedSteps: 1,
              totalSteps: 2,
              artifacts: [],
              researchExecution: progress.researchExecution,
            },
          };
          setMessages((previous) => {
            const exists = previous.some((item) => item.id === streamingMessageId);
            return exists
              ? previous.map((item) => item.id === streamingMessageId ? progressMessage : item)
              : [...previous, progressMessage];
          });
        },
      );

      // 添加 AI 回复
      const assistantMessage: ChatMessage = {
        id: progressMessageCreated ? streamingMessageId : (Date.now() + 1).toString(),
        role: "assistant",
        content: response.response,
        timestamp: new Date(),
        intent: response.taskType,
        execution: response.workflowSummary ? {
          taskType: response.taskType,
          runId: response.run_id,
          governedRunId: response.governed_run_id,
          completedSteps: response.workflowSummary.completedSteps,
          totalSteps: response.workflowSummary.totalSteps,
          health: response.data?.dataHealth,
          citation: response.data?.citationValidation,
          artifacts: response.artifacts || [],
          researchExecution: response.data?.researchExecution,
        } : undefined,
      };
      setMessages((previous) => progressMessageCreated
        ? previous.map((item) => item.id === streamingMessageId ? assistantMessage : item)
        : [...previous, assistantMessage]);

      // 刷新侧边栏
      refreshSidebar();
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: progressMessageCreated ? streamingMessageId : (Date.now() + 1).toString(),
        role: "assistant",
        content: `抱歉，发生了错误：${error instanceof Error ? error.message : "未知错误"}`,
        timestamp: new Date(),
        intent: "unknown",
      };
      setMessages((previous) => progressMessageCreated
        ? previous.map((item) => item.id === streamingMessageId ? {
            ...errorMessage,
            execution: item.execution,
          } : item)
        : [...previous, errorMessage]);
    } finally {
      setIsLoading(false);
      setIsStreamingProgress(false);
    }
  }


  /**
   * 键盘事件处理
   *
   * Enter 发送，Shift+Enter 换行
   */
  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }


  /**
   * 清空当前会话
   *
   * 删除当前会话并回到空状态欢迎页
   */
  async function handleClearHistory() {
    if (!window.confirm("确定要清空当前对话吗？此操作不可恢复。")) return;

    if (currentSessionId) {
      try {
        await deleteSession(currentSessionId);
        setCurrentSessionId(null);
        refreshSidebar();
      } catch (err) {
        console.error("删除会话失败:", err);
        alert("删除会话失败，请稍后重试");
        return;
      }
    }

    setMessages([]);
  }


  /**
   * 判断当前是否显示空状态欢迎页
   */
  const showWelcome = isEmptyState(messages);


  return (
    <div className="flex flex-1 min-h-0 bg-white dark:bg-gray-900 overflow-hidden border-t border-gray-200">
      {/* === 左侧：会话列表侧边栏 === */}
      <SessionSidebar
        key={sidebarRefreshKey}
        currentSessionId={currentSessionId}
        onSelectSession={selectSession}
        onCreateSession={handleCreateSession}
      />

      {/* === 中间区域：根据状态显示不同页面 === */}
      {showWelcome ? (
        /* ---------- 空状态：欢迎页 ---------- */
        <div className="flex-1 flex flex-col items-center justify-center overflow-y-auto px-6 py-8">
          <div className="w-full max-w-2xl">

            {/* 欢迎语 */}
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-2xl mb-4 shadow-lg">
                <Sparkles size={28} className="text-white" />
              </div>
              <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-2">
                今天想分析点什么？
              </h1>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                直接在下方输入你的需求，或从下方推荐任务中选择一项开始
              </p>
            </div>

            {/* 大输入框 */}
            <div className="relative mb-6">
              <textarea
                ref={welcomeInputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="输入你的问题，例如：帮我分析中际旭创..."
                rows={3}
                className="w-full px-5 py-4 text-sm border border-gray-300 dark:border-gray-600 rounded-2xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 shadow-sm"
              />
              <button
                onClick={() => handleSend()}
                disabled={!inputValue.trim() || isLoading}
                className="absolute bottom-4 right-4 flex items-center justify-center w-9 h-9 bg-gradient-to-br from-purple-600 to-indigo-600 hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-xl transition-opacity shadow-md"
              >
                {isLoading ? <Loader2 size={18} className="animate-spin" /> : <ArrowUp size={18} />}
              </button>
            </div>

            {/* 推荐任务卡片 */}
            <div className="grid grid-cols-2 gap-3">
              {suggestedTasks.map((task) => (
                <button
                  key={task.title}
                  onClick={() => handleSend(task.message)}
                  disabled={isLoading}
                  className="group flex flex-col items-start p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl hover:border-purple-300 dark:hover:border-purple-600 hover:shadow-md transition-all text-left disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <div className={`inline-flex items-center justify-center w-8 h-8 bg-gradient-to-br ${task.color} rounded-lg mb-2`}>
                    <task.icon size={16} className="text-white" />
                  </div>
                  <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-100 mb-1">
                    {task.title}
                  </h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
                    {task.description}
                  </p>
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : (
        /* ---------- 工作状态：聊天界面 ---------- */
        <div className="flex flex-col flex-1 overflow-hidden">

          {/* 顶部工具栏 */}
          <div className="flex items-center justify-between px-4 py-2.5 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-full flex items-center justify-center">
                <Bot size={14} className="text-white" />
              </div>
              <span className="text-sm font-medium text-gray-700 dark:text-gray-200">SMR 研究助手</span>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={handleClearHistory}
                disabled={isLoading}
                title="清空当前对话"
                className="flex items-center gap-1 text-xs text-gray-400 hover:text-red-500 transition-colors disabled:opacity-40"
              >
                <Trash2 size={13} />
                <span>清空</span>
              </button>
              <div className="flex items-center gap-1">
                <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                <span className="text-xs text-gray-400">在线</span>
              </div>
            </div>
          </div>

          {/* 消息流区域 */}
          <div className="flex-1 overflow-y-auto px-4 py-4">
            {messages.map((msg) =>
              msg.role === "user" ? (
                <UserMessageBubble key={msg.id} content={msg.content} timestamp={msg.timestamp} />
              ) : (
                <AssistantMessageBubble key={msg.id} content={msg.content} timestamp={msg.timestamp} intent={msg.intent} execution={msg.execution} />
              )
            )}
            {isLoading && !isStreamingProgress && <LoadingIndicator />}
            <div ref={messagesEndRef} />
          </div>

          {/* 底部输入区域 */}
          <div className="px-4 py-3 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-end gap-2">
              <div className="flex-1 relative">
                <textarea
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="输入你的问题..."
                  rows={1}
                  className="w-full px-4 py-2.5 text-sm border border-gray-300 dark:border-gray-600 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none max-h-32 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400"
                  style={{ minHeight: "44px" }}
                />
              </div>
              <button
                onClick={() => handleSend()}
                disabled={!inputValue.trim() || isLoading}
                className="flex items-center justify-center w-10 h-10 bg-gradient-to-br from-purple-600 to-indigo-600 hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-xl transition-opacity shadow-md"
              >
                {isLoading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
              </button>
            </div>
            <p className="text-xs text-gray-400 mt-2 text-center">
              按 Enter 发送，Shift+Enter 换行
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
